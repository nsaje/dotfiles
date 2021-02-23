# -*- coding: utf-8 -*-
# isort:skip_file
import dash.features.bluekai.service
import magic
import mimetypes
import re
import json
import io

import unicodecsv
import dateutil.parser
from collections import OrderedDict
from collections import Counter

import xlrd
import openpyxl

from django import forms
from django.contrib.postgres import forms as postgres_forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core import validators
from django.core import exceptions
from django.conf import settings

import core.features.multicurrency
import core.features.deals.direct_deal_connection.exceptions
import core.features.bcm
import core.features.publisher_groups
import dash.features.contentupload
import utils.exc
from dash import constants
from dash import models
from dash.views import helpers
from dash.features.custom_flags.forms import CustomFlagsFormMixin
from utils import validation_helper
from zemauth.models import User as ZemUser
from zemauth.features.entity_permission import Permission

import stats.constants

import dash.compatibility.forms

MAX_ADS_PER_UPLOAD = 100


class BaseApiForm(forms.Form):
    def get_errors(self):
        pass


class AdvancedDateTimeField(forms.fields.DateTimeField):
    def strptime(self, value, format):
        return dateutil.parser.parse(value)


class TypedMultipleAnyChoiceField(forms.TypedMultipleChoiceField):
    """
    Same as TypedMultipleChoiceField but unrestricted choices list.
    """

    def valid_value(self, value):
        return True


class PlainCharField(forms.CharField):
    def clean(self, value):
        validation_helper.validate_plain_text(value)
        return super(PlainCharField, self).clean(value)


REDIRECT_JS_HELP_TEXT = """!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');

fbq('init', '531027177051024');
fbq('track', "PageView");"""


class PublisherGroupsFormMixin(forms.Form):

    whitelist_publisher_groups = forms.ModelMultipleChoiceField(
        required=False,
        queryset=None,
        widget=FilteredSelectMultiple(verbose_name="whitelist publisher groups", is_stacked=False),
        error_messages={"invalid_choice": "Invalid whitelist publisher group selection."},
    )

    blacklist_publisher_groups = forms.ModelMultipleChoiceField(
        required=False,
        queryset=None,
        widget=FilteredSelectMultiple(verbose_name="blacklist publisher groups", is_stacked=False),
        error_messages={"invalid_choice": "Invalid blacklist publisher group selection."},
    )

    def __init__(self, *args, **kwargs):
        super(PublisherGroupsFormMixin, self).__init__(*args, **kwargs)
        qs = models.PublisherGroup.objects.all()
        if hasattr(self, "account"):
            self.fields["whitelist_publisher_groups"].queryset = qs.filter_by_account(self.account)
            self.fields["blacklist_publisher_groups"].queryset = qs.filter_by_account(self.account)
        elif hasattr(self, "agency"):
            self.fields["whitelist_publisher_groups"].queryset = qs.filter_by_agency(self.agency)
            self.fields["blacklist_publisher_groups"].queryset = qs.filter_by_agency(self.agency)
        else:
            self.fields["whitelist_publisher_groups"].widget = forms.HiddenInput()
            self.fields["whitelist_publisher_groups"].queryset = qs.none()
            self.fields["blacklist_publisher_groups"].widget = forms.HiddenInput()
            self.fields["blacklist_publisher_groups"].queryset = qs.none()

    def clean_whitelist_publisher_groups(self):
        publisher_groups = self.cleaned_data.get("whitelist_publisher_groups") or []
        return [x.id for x in publisher_groups]

    def clean_blacklist_publisher_groups(self):
        publisher_groups = self.cleaned_data.get("blacklist_publisher_groups") or []
        return [x.id for x in publisher_groups]


class AdGroupAdminForm(forms.ModelForm, CustomFlagsFormMixin):
    SETTINGS_FIELDS = ["notes", "bluekai_targeting"]
    ADDITIONAL_TARGETING_FIELDS = ["notes", "bluekai_campaign_id", "bluekai_targeting"]
    notes = PlainCharField(
        required=False,
        widget=forms.Textarea,
        help_text="Describe what kind of additional targeting was setup on the backend.",
    )
    bluekai_campaign_id = forms.IntegerField(
        required=False,
        widget=forms.TextInput,
        help_text="<font color='red'>If a BlueKai campaign ID is entered here, the Bluekai Targeting field will be overwritten with the targeting expression representing that BlueKai campaign's audience.</font>",
    )
    bluekai_targeting = postgres_forms.JSONField(
        required=False,
        help_text='Example: ["and", "bluekai:446103", ["not", ["or", "bluekai:510120", "bluekai:510122"]]]',
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        # default to empty list instead of null
        initial["bluekai_targeting"] = []
        if "instance" in kwargs:
            settings = kwargs["instance"].get_current_settings()
            for field in self.SETTINGS_FIELDS:
                initial[field] = getattr(settings, field)
        kwargs["initial"] = initial
        super(AdGroupAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.AdGroup
        fields = "__all__"

    def clean_bluekai_targeting(self):
        bluekai_campaign_id = self.cleaned_data.get("bluekai_campaign_id")
        if bluekai_campaign_id:
            return dash.features.bluekai.service.get_expression_from_campaign(bluekai_campaign_id)
        return self.cleaned_data.get("bluekai_targeting")


class AdGroupSourceSettingsForm(forms.Form):
    cpc_cc = forms.DecimalField(decimal_places=4, required=False)
    cpm = forms.DecimalField(decimal_places=4, required=False)
    daily_budget_cc = forms.DecimalField(decimal_places=4, required=False)
    state = forms.TypedChoiceField(
        choices=constants.AdGroupSettingsState.get_choices(), coerce=int, required=False, empty_value=None
    )


class ConversionPixelForm(forms.Form):
    archived = forms.BooleanField(required=False)
    redirect_url = forms.URLField(max_length=2048, required=False)
    notes = PlainCharField(required=False)

    def __init__(self, *args, **kwargs):
        super(ConversionPixelForm, self).__init__(*args, **kwargs)


class ConversionPixelCreateForm(ConversionPixelForm):
    name = PlainCharField(
        max_length=50,
        required=True,
        error_messages={
            "required": "Please specify a name.",
            "max_length": "Name is too long (%(show_value)d/%(limit_value)d).",
        },
    )

    def __init__(self, *args, **kwargs):
        super(ConversionPixelCreateForm, self).__init__(*args, **kwargs)


class CampaignAdminForm(forms.ModelForm, CustomFlagsFormMixin):
    class Meta:
        model = models.Campaign
        exclude = ("users", "groups", "created_dt", "modified_dt", "modified_by")


class AccountAdminForm(forms.ModelForm, CustomFlagsFormMixin):
    class Meta:
        model = models.Account
        fields = "__all__"
        exclude = ("custom_flags",)


class AgencyAdminForm(PublisherGroupsFormMixin, forms.ModelForm, CustomFlagsFormMixin):
    SETTINGS_FIELDS = ["whitelist_publisher_groups", "blacklist_publisher_groups"]

    class Meta:
        model = models.Agency
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        instance = kwargs.get("instance")
        if instance is not None:
            self.agency = instance
            settings = self.agency.get_current_settings()
            for field in self.SETTINGS_FIELDS:
                initial[field] = getattr(settings, field)
        kwargs["initial"] = initial

        super(AgencyAdminForm, self).__init__(*args, **kwargs)

        self.fields["sales_representative"].queryset = (
            ZemUser.objects.all().exclude(first_name="").exclude(last_name="").order_by("first_name", "last_name")
        )
        self.fields["sales_representative"].label_from_instance = lambda obj: "{full_name} <{email}>".format(
            full_name=obj.get_full_name(), email=obj.email or ""
        )
        self.fields["cs_representative"].queryset = (
            ZemUser.objects.all().exclude(first_name="").exclude(last_name="").order_by("first_name", "last_name")
        )
        self.fields["cs_representative"].label_from_instance = lambda obj: "{full_name} <{email}>".format(
            full_name=obj.get_full_name(), email=obj.email or ""
        )
        self.fields["ob_sales_representative"].queryset = ZemUser.objects.all().order_by(
            "first_name", "last_name", "email"
        )
        self.fields["ob_sales_representative"].label_from_instance = lambda obj: "{full_name} <{email}>".format(
            full_name=obj.get_full_name(), email=obj.email or ""
        )
        self.fields["ob_account_manager"].queryset = ZemUser.objects.all().order_by("first_name", "last_name", "email")
        self.fields["ob_account_manager"].label_from_instance = lambda obj: "{full_name} <{email}>".format(
            full_name=obj.get_full_name(), email=obj.email or ""
        )


class UserForm(forms.Form):
    email = forms.EmailField(max_length=127, error_messages={"required": "Please specify user's email."})
    first_name = PlainCharField(max_length=127, error_messages={"required": "Please specify first name."})
    last_name = PlainCharField(max_length=127, error_messages={"required": "Please specify last name."})


DISPLAY_URL_MAX_LENGTH = 35
MANDATORY_CSV_FIELDS = ["url", "title", "image_url"]
GENERAL_OPTIONAL_CSV_FIELDS = [
    "icon_url",
    "display_url",
    "brand_name",
    "description",
    "call_to_action",
    "label",
    "image_crop",
    "primary_tracker_url",
    "secondary_tracker_url",
    "creative_size",
    "ad_tag",
]
TRACKER_OPTIONAL_CSV_FIELDS = [
    "tracker_1_event_type",
    "tracker_1_method",
    "tracker_1_url",
    "tracker_1_fallback_url",
    "tracker_1_optional",
    "tracker_2_event_type",
    "tracker_2_method",
    "tracker_2_url",
    "tracker_2_fallback_url",
    "tracker_2_optional",
    "tracker_3_event_type",
    "tracker_3_method",
    "tracker_3_url",
    "tracker_3_fallback_url",
    "tracker_3_optional",
]
OPTIONAL_CSV_FIELDS = GENERAL_OPTIONAL_CSV_FIELDS + TRACKER_OPTIONAL_CSV_FIELDS
ALL_CSV_FIELDS = MANDATORY_CSV_FIELDS + OPTIONAL_CSV_FIELDS
IGNORED_CSV_FIELDS = ["errors"]
JOINT_CSV_FIELDS = {"creative_size": ("x", "image_width", "image_height")}
NATIVE_SPECIFIC_FIELDS = ["icon_url"]
DISPLAY_SPECIFIC_FIELDS = ["creative_size", "ad_tag"]

EXPRESSIVE_FIELD_NAME_MAPPING = {
    "brand_logo_url": "icon_url",
    "primary_impression_tracker_url": "primary_tracker_url",
    "secondary_impression_tracker_url": "secondary_tracker_url",
}
INVERSE_EXPRESSIVE_FIELD_NAME_MAPPING = {v: k for k, v in EXPRESSIVE_FIELD_NAME_MAPPING.items()}
FIELD_PERMISSION_MAPPING = {
    tracker_field: ["zemauth.can_use_3rdparty_js_trackers"] for tracker_field in TRACKER_OPTIONAL_CSV_FIELDS
}

# Example CSV content - must be ignored if mistakenly uploaded
# Example File is served by client (Zemanta_Content_Ads_Template.csv)
EXAMPLE_CSV_CONTENT = {
    "url": "http://www.zemanta.com/insights/2016/6/13/8-tips-for-creating-clickable-content",
    "title": "8 Tips for Creating Clickable Content",
    "image_url": "http://static1.squarespace.com/static/56bbb88007eaa031a14e3472/"
    "56ce2a0206dcb7970cb2a080/575f341659827ef48ecb2253/1466510434775/"
    "coffee-apple-iphone-laptop.jpg?format=1500w",
}

CSV_EXPORT_COLUMN_NAMES_DICT = OrderedDict(
    [
        ["url", "URL"],
        ["title", "Title"],
        ["image_url", "Image URL"],
        ["image_crop", "Image crop"],
        ["icon_url", "Brand Logo URL"],
        ["display_url", "Display URL"],
        ["brand_name", "Brand name"],
        ["call_to_action", "Call to action"],
        ["description", "Description"],
        ["primary_tracker_url", "Primary impression tracker URL"],
        ["secondary_tracker_url", "Secondary impression tracker URL"],
        ["label", "Label"],
        ["creative_size", "Creative size"],
        ["ad_tag", "Ad tag"],
        ["tracker_1_event_type", "Tracker 1 Event type"],
        ["tracker_1_method", "Tracker 1 Method"],
        ["tracker_1_url", "Tracker 1 URL"],
        ["tracker_1_fallback_url", "Tracker 1 Fallback URL"],
        ["tracker_1_optional", "Tracker 1 Optional"],
        ["tracker_2_event_type", "Tracker 2 Event type"],
        ["tracker_2_method", "Tracker 2 Method"],
        ["tracker_2_url", "Tracker 2 URL"],
        ["tracker_2_fallback_url", "Tracker 2 Fallback URL"],
        ["tracker_2_optional", "Tracker 2 Optional"],
        ["tracker_3_event_type", "Tracker 3 Event type"],
        ["tracker_3_method", "Tracker 3 Method"],
        ["tracker_3_url", "Tracker 3 URL"],
        ["tracker_3_fallback_url", "Tracker 3 Fallback URL"],
        ["tracker_3_optional", "Tracker 3 Optional"],
    ]
)


class DisplayURLField(forms.URLField):
    def clean(self, value):
        display_url = super(forms.URLField, self).clean(value)
        display_url = display_url.strip()
        display_url = re.sub(r"^https?://", "", display_url)
        display_url = re.sub(r"/$", "", display_url)

        validate_length = validators.MaxLengthValidator(
            DISPLAY_URL_MAX_LENGTH, message=self.error_messages["max_length"]
        )
        validate_length(display_url)

        return display_url


class AdGroupAdsUploadBaseForm(forms.Form):
    account_id = forms.IntegerField(required=False)
    ad_group_id = forms.IntegerField(required=False)
    batch_name = PlainCharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "Please enter a name for this upload.",
            "max_length": "Batch name is too long (%(show_value)d/%(limit_value)d).",
        },
    )


XLS_MIMETYPE = "application/vnd.ms-excel"
XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ParseCSVExcelFile(object):
    def _parse_file(self, candidates_file):
        content = candidates_file.read()
        filename_mimetype, _ = mimetypes.guess_type(candidates_file.name)
        content_mimetype = magic.from_buffer(content, mime=True).split("/")

        if filename_mimetype == XLS_MIMETYPE and content_mimetype[0] == "application":
            return self._parse_xls_file(content)
        elif filename_mimetype == XLSX_MIMETYPE and content_mimetype[0] == "application":
            return self._parse_xlsx_file(content)
        elif filename_mimetype == "text/csv" and content_mimetype[0] == "text":
            return self._parse_csv_file(content)
        else:
            raise forms.ValidationError("Input file was not recognized.")

    def _parse_csv_file(self, content):
        # If the file contains ctrl-M chars instead of
        # new line breaks, DictReader will fail to parse it.
        # Therefore we split the file by lines first and
        # pass that to DictReader. If this proves to be too
        # slow, we can instead save the file to a temporary
        # location on upload and then open it with 'rU'
        # (universal-newline mode).
        # Additionally remove empty lines and Example CSV content if present.
        lines = [line for line in content.splitlines() if line]

        encodings = ["utf-8", "windows-1252"]
        rows = None

        # try all supported encodings one by one
        for encoding in encodings:
            try:
                reader = unicodecsv.reader(lines, encoding=encoding)
                rows = [row for row in reader]

                break
            except unicodecsv.Error:
                raise forms.ValidationError("Uploaded file is not a valid CSV file.")
            except UnicodeDecodeError:
                pass

        if rows is None:
            raise forms.ValidationError("Unknown file encoding.")

        return rows

    def _parse_xls_file(self, content):
        wb = xlrd.open_workbook(file_contents=content)

        if wb.nsheets < 1:
            raise forms.ValidationError("No sheets in excel file.")
        sheet = wb.sheet_by_index(0)

        return [self._get_sheet_row(sheet, i) for i in range(sheet.nrows)]

    def _get_sheet_row(self, sheet, i):
        return [cell.value for cell in sheet.row(i)]

    def _parse_xlsx_file(self, content):
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)

        if len(wb.worksheets) < 1:
            raise forms.ValidationError("No sheets in excel file.")
        sheet = wb.worksheets[0]

        return [[cell.value for cell in row] for row in sheet.rows]

    def _is_example_row(self, row):
        return False

    def _is_empty_row(self, row):
        return not any(x.strip() if x else x for x in list(row.values()))

    def _remove_unnecessary_fields(self, row):
        # unicodecsv stores values of all unneeded columns
        # under key None. This can be removed.
        if None in row:
            del row[None]

        # Remove ignored fields from row dict
        for ignored_field in IGNORED_CSV_FIELDS:
            row.pop(ignored_field, None)

        return row

    def _remap_joint_to_separate_fields(self, row):
        for joint_field, joint_params in JOINT_CSV_FIELDS.items():
            row_field = row.pop(joint_field, None)
            if row_field:
                field1, field2 = re.sub(r"\s+", "", row_field.lower()).split(joint_params[0])
                row[joint_params[1]] = field1
                row[joint_params[2]] = field2

        return row


class AdGroupAdsUploadForm(AdGroupAdsUploadBaseForm, ParseCSVExcelFile):
    candidates = forms.FileField(error_messages={"required": "Please choose a file to upload."})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def _get_column_names(self, header):
        # this function maps original CSV column names to internal, normalized
        # ones that are then used across the application
        column_names = [col.strip(" _").lower().replace(" ", "_") for col in header if col is not None]

        if len(column_names) > 1 and column_names[1] == "name":
            column_names[1] = "title"

        if len(column_names) < 1 or column_names[0] != "url":
            raise forms.ValidationError("First column in header should be URL.")

        if len(column_names) < 2 or (column_names[1] != "title"):
            raise forms.ValidationError("Second column in header should be Title.")

        if len(column_names) < 3 or column_names[2] != "image_url":
            raise forms.ValidationError("Third column in header should be Image URL.")

        for n, field in enumerate(column_names):
            # We accept "(optional)" in the names of optional columns.
            # That's how those columns are presented in our csv template (that user can download)
            # If the user downloads the template, fills it in and uploades, it
            # immediately works.
            field = re.sub(r"_*\(optional\)", "", field)
            field = EXPRESSIVE_FIELD_NAME_MAPPING.get(field, field)
            if n >= 3 and field not in OPTIONAL_CSV_FIELDS and field not in IGNORED_CSV_FIELDS:
                raise forms.ValidationError('Unrecognized column name "{0}".'.format(header[n]))
            column_names[n] = field

        # Make sure each column_name appears only once
        for column_name, count in Counter(column_names).items():
            expr_column_name = INVERSE_EXPRESSIVE_FIELD_NAME_MAPPING.get(column_name, column_name)
            formatted_name = expr_column_name.replace("_", " ").capitalize()
            if count > 1:
                raise forms.ValidationError(
                    'Column "{0}" appears multiple times ({1}) in the CSV file.'.format(formatted_name, count)
                )

        return column_names

    def _is_example_row(self, row):
        return all(row[example_key] == example_value for example_key, example_value in EXAMPLE_CSV_CONTENT.items())

    def _map_trackers(self, row):
        trackers = []
        for i in range(1, dash.features.contentupload.MAX_TRACKERS + 1):
            if (
                row.get("tracker_{}_event_type".format(i))
                or row.get("tracker_{}_method".format(i))
                or row.get("tracker_{}_url".format(i))
            ):
                tracker = dash.features.contentupload.get_tracker(
                    url=row.get("tracker_{}_url".format(i)),
                    event_type=row.get("tracker_{}_event_type".format(i)),
                    method=row.get("tracker_{}_method".format(i)),
                    fallback_url=row.get("tracker_{}_fallback_url".format(i))
                    if row.get("tracker_{}_method".format(i)) == dash.constants.TrackerMethod.JS
                    else None,
                    tracker_optional=row.get("tracker_{}_optional".format(i).lower()) == "true",
                )
                trackers.append(tracker)

        if not trackers:
            trackers = dash.features.contentupload.convert_legacy_trackers(
                tracker_urls=[row.get("primary_tracker_url"), row.get("secondary_tracker_url")], tracker_optional=True
            )

        row["trackers"] = trackers
        return row

    def clean_candidates(self):
        candidates_file = self.cleaned_data["candidates"]

        rows = self._parse_file(candidates_file)

        if len(rows) < 1:
            raise forms.ValidationError("Uploaded file is empty.")

        column_names = self._get_column_names(rows[0])

        data = (dict(list(zip(column_names, row))) for row in rows[1:])
        data = [
            self._remove_unnecessary_fields(row)
            for row in data
            if not self._is_example_row(row) and not self._is_empty_row(row)
        ]
        data = [self._remap_joint_to_separate_fields(row) for row in data]

        if self.user.has_perm("zemauth.can_use_3rdparty_js_trackers"):
            data = [self._map_trackers(row) for row in data]

        if len(data) < 1:
            raise forms.ValidationError("Uploaded file is empty.")

        if len(data) > MAX_ADS_PER_UPLOAD:
            raise forms.ValidationError("Too many content ads (max. {})".format(MAX_ADS_PER_UPLOAD))

        return data


class MultiEmailField(forms.Field):
    def to_python(self, value):
        if not value:
            return []
        value = "".join(value.split())
        return value.split(",")

    def validate(self, value):
        super(MultiEmailField, self).validate(value)
        invalid_addresses = []
        for email in value:
            try:
                validators.validate_email(email)
            except forms.ValidationError:
                invalid_addresses.append(email)

        if invalid_addresses:
            raise forms.ValidationError(
                ", ".join(invalid_addresses)
                + (" is" if len(invalid_addresses) == 1 else " are")
                + " not valid email address"
                + ("es" if len(invalid_addresses) > 1 else "")
                + "."
            )


class CreditLineItemAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreditLineItemAdminForm, self).__init__(*args, **kwargs)
        # archived state is stored in settings, we need to have a more stupid
        # query
        not_archived = [a.pk for a in models.Account.objects.all().select_related("settings") if not a.is_archived()]
        # workaround to not change model __unicode__ methods
        self.fields["account"].label_from_instance = lambda obj: "{} - {}".format(obj.id, obj.name)
        self.fields["account"].queryset = models.Account.objects.filter(pk__in=not_archived).order_by("id")

        self.fields["agency"].label_from_instance = lambda obj: "{} - {}".format(obj.id, obj.name)
        self.fields["agency"].queryset = models.Agency.objects.all().order_by("id")

    class Meta:
        model = models.CreditLineItem
        fields = [
            "account",
            "agency",
            "start_date",
            "end_date",
            "currency",
            "amount",
            "license_fee",
            "status",
            "comment",
        ]


class RefundLineItemAdminForm(forms.ModelForm):
    class Meta:
        model = models.RefundLineItem
        fields = ["account", "credit", "start_date", "end_date", "amount", "comment"]

    def full_clean(self):
        try:
            super().full_clean()

        except core.features.bcm.refund_line_item.exceptions.StartDateInvalid as err:
            self.add_error(None, exceptions.ValidationError({"start_date": [str(err)]}))

        except core.features.bcm.refund_line_item.exceptions.RefundAmountExceededTotalSpend as err:
            self.add_error(None, exceptions.ValidationError({"amount": [str(err)]}))

        except core.features.bcm.refund_line_item.exceptions.CreditAvailableAmountNegative as err:
            self.add_error(None, exceptions.ValidationError({"amount": [str(err)]}))


class BudgetLineItemAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BudgetLineItemAdminForm, self).__init__(*args, **kwargs)
        # archived state is stored in settings, we need to have a more stupid
        # query
        not_archived = set([c.id for c in models.Campaign.objects.all() if not c.is_archived()])
        if self.instance and self.instance.campaign_id:
            not_archived.add(self.instance.campaign_id)

        # workaround to not change model __unicode__ methods

        self.fields["campaign"].label_from_instance = lambda obj: "{} - {}".format(obj.id, obj.name)
        self.fields["campaign"].queryset = models.Campaign.objects.filter(pk__in=not_archived).order_by("id")

        self.fields["credit"].queryset = models.CreditLineItem.objects.filter(
            status=constants.CreditLineItemStatus.SIGNED
        ).order_by("account_id")

    class Meta:
        model = models.BudgetLineItem
        fields = ["campaign", "credit", "start_date", "end_date", "amount", "comment"]


class ViewFilterForm(forms.Form):

    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    show_archived = forms.BooleanField(required=False)

    filtered_sources = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_agencies = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_account_types = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_businesses = forms.MultipleChoiceField(choices=constants.Business.get_choices(), required=False)

    def clean_filtered_sources(self):
        return helpers.get_filtered_sources(self.cleaned_data.get("filtered_sources"))

    def clean_filtered_agencies(self):
        return helpers.get_filtered_agencies(self.cleaned_data.get("filtered_agencies"))

    def clean_filtered_account_types(self):
        return helpers.get_filtered_account_types(self.cleaned_data.get("filtered_account_types"))


class BreakdownForm(ViewFilterForm):
    def __init__(self, breakdown, request_body, *args, **kwargs):
        request_body["breakdown"] = breakdown
        super().__init__(request_body, *args, **kwargs)

    start_date = forms.DateField(error_messages={"required": "Please provide start date."})
    end_date = forms.DateField(error_messages={"required": "Please provide end date."})

    show_blacklisted_publishers = forms.TypedChoiceField(
        required=False, choices=constants.PublisherBlacklistFilter.get_choices(), coerce=str, empty_value=None
    )

    offset = forms.IntegerField(min_value=0, required=True)
    limit = forms.IntegerField(min_value=0, max_value=100, required=True)

    parents = TypedMultipleAnyChoiceField(required=False, coerce=str)

    order = PlainCharField(required=False)

    breakdown = PlainCharField(required=True)

    def clean_breakdown(self):
        return [stats.constants.get_dimension_identifier(x) for x in self.cleaned_data["breakdown"].split("/") if x]

    def clean_parents(self):
        parents = []
        if self.data.get("parents"):
            parents = [str(x) for x in self.data["parents"] if x]
        return parents


class ContentAdCandidateForm(forms.ModelForm):
    image = forms.ImageField(required=False, error_messages={"invalid_image": "Invalid image file"})
    icon = forms.ImageField(required=False, error_messages={"invalid_image": "Invalid image file"})
    # TODO: Set queryset in __init__ to filter video assets by account
    video_asset_id = forms.ModelChoiceField(queryset=models.VideoAsset.objects.all(), required=False)
    type = forms.TypedChoiceField(
        choices=constants.AdType.get_choices(),
        required=False,
        error_messages={"invalid_choice": "Choose a valid ad type"},
        coerce=int,
    )
    image_width = forms.IntegerField(required=False)
    image_height = forms.IntegerField(required=False)
    icon_width = forms.IntegerField(required=False)
    icon_height = forms.IntegerField(required=False)

    def __init__(self, campaign, data, files=None, original_content_ad=None):
        for image_field in ["image", "icon"]:
            if files and image_field in files:
                files[image_field].seek(0)

        super(ContentAdCandidateForm, self).__init__(data, files)
        self.campaign = campaign
        self.original_content_ad = original_content_ad

    def _set_trackers(self):
        trackers = self.cleaned_data.get("trackers")
        if trackers is None:
            self.cleaned_data["trackers"] = dash.features.contentupload.convert_legacy_trackers(
                [self.cleaned_data.get("primary_tracker_url"), self.cleaned_data.get("secondary_tracker_url")],
                tracker_optional=True,
            )
        else:
            self.cleaned_data["trackers"] = [dash.features.contentupload.get_tracker(**tracker) for tracker in trackers]

    def clean_image_crop(self):
        image_crop = self.cleaned_data.get("image_crop")
        if not image_crop:
            return constants.ImageCrop.CENTER

        return image_crop.lower()

    def clean_icon_url(self):
        return self.cleaned_data.get("icon_url") or None

    def clean_video_asset_id(self):
        video_asset = self.cleaned_data.get("video_asset_id")
        return str(video_asset.id) if video_asset else None

    def clean_call_to_action(self):
        call_to_action = self.cleaned_data.get("call_to_action")
        if not call_to_action:
            return constants.DEFAULT_CALL_TO_ACTION

        return call_to_action

    def clean_ad_tag(self):
        return self.cleaned_data.get("ad_tag") or None

    def clean(self):
        cleaned_data = super().clean()
        self._set_trackers()

        if cleaned_data.get("type"):
            return cleaned_data

        if self.campaign and self.campaign.type == constants.CampaignType.DISPLAY:
            cleaned_data["type"] = constants.AdType.AD_TAG if cleaned_data.get("ad_tag") else constants.AdType.IMAGE

        elif self.campaign and self.campaign.type == constants.CampaignType.VIDEO or cleaned_data.get("video_asset_id"):
            cleaned_data["type"] = constants.AdType.VIDEO

        else:
            cleaned_data["type"] = constants.AdType.CONTENT

        return cleaned_data

    class Meta:
        model = models.ContentAdCandidate
        fields = [
            "label",
            "url",
            "title",
            "type",
            "state",
            "image_url",
            "image_crop",
            "icon_url",
            "video_asset_id",
            "display_url",
            "brand_name",
            "description",
            "call_to_action",
            "primary_tracker_url",
            "secondary_tracker_url",
            "additional_data",
            "ad_tag",
            "trackers",
            "trackers_status",
        ]


class ContentAdForm(ContentAdCandidateForm):
    label = PlainCharField(
        max_length=256, required=False, error_messages={"max_length": "Label too long (max %(limit_value)d characters)"}
    )
    url = PlainCharField(
        max_length=936,
        error_messages={"required": "Missing URL", "max_length": "URL too long (max %(limit_value)d characters)"},
    )
    title = PlainCharField(
        max_length=90,
        error_messages={"required": "Missing title", "max_length": "Title too long (max %(limit_value)d characters)"},
    )
    image_url = PlainCharField(error_messages={"required": "Missing image"})
    image_crop = forms.ChoiceField(
        choices=constants.ImageCrop.get_choices(),
        error_messages={"invalid_choice": "Choose a valid image crop", "required": "Choose a valid image crop"},
    )
    icon_url = PlainCharField(required=False)
    # TODO: Set queryset in __init__ to filter video assets by account
    video_asset_id = forms.ModelChoiceField(queryset=models.VideoAsset.objects.all(), required=False)
    display_url = DisplayURLField(
        error_messages={
            "required": "Missing display URL",
            "max_length": "Display URL too long (max %(limit_value)d characters)",
        }
    )
    brand_name = PlainCharField(
        max_length=25,
        error_messages={
            "required": "Missing brand name",
            "max_length": "Brand name too long (max %(limit_value)d characters)",
        },
    )
    description = PlainCharField(
        max_length=150,
        error_messages={
            "required": "Missing description",
            "max_length": "Description too long (max %(limit_value)d characters)",
        },
    )
    call_to_action = PlainCharField(
        max_length=25,
        error_messages={
            "required": "Missing call to action",
            "max_length": "Call to action too long (max %(limit_value)d characters)",
        },
    )
    primary_tracker_url = PlainCharField(
        max_length=936, required=False, error_messages={"max_length": "URL too long (max %(limit_value)d characters)"}
    )
    secondary_tracker_url = PlainCharField(
        max_length=936, required=False, error_messages={"max_length": "URL too long (max %(limit_value)d characters)"}
    )

    image_id = PlainCharField(required=False)
    image_hash = PlainCharField(required=False)
    image_file_size = forms.IntegerField(required=False)

    icon_id = PlainCharField(required=False)
    icon_hash = PlainCharField(required=False)
    icon_file_size = forms.IntegerField(required=False)

    image_status = forms.IntegerField(required=False)
    icon_status = forms.IntegerField(required=False)
    url_status = forms.IntegerField(required=False)
    primary_tracker_url_status = forms.IntegerField(required=False)
    secondary_tracker_url_status = forms.IntegerField(required=False)
    state = forms.TypedChoiceField(
        choices=dash.constants.ContentAdSourceState.get_choices(), coerce=int, required=False, empty_value=None
    )
    original_content_ad_id = forms.IntegerField(required=False)

    MIN_IMAGE_SIZE = 300
    MAX_IMAGE_SIZE = 10000
    MIN_ICON_SIZE = 128

    def __init__(self, campaign, *args, **kwargs):
        super(ContentAdForm, self).__init__(campaign, *args, **kwargs)
        self.campaign = campaign

    def _validate_trackers(self, trackers):
        tracker_errors = []
        has_errors = False
        for tracker in trackers:
            tracker_error = {}
            if (
                tracker.get("event_type") is None
                or tracker.get("event_type") not in dash.constants.TrackerEventType.get_all()
            ):
                has_errors = True
                tracker_error["event_type"] = "Valid Event type is required."

            if tracker.get("method") is None or tracker.get("method") not in dash.constants.TrackerMethod.get_all():
                has_errors = True
                tracker_error["method"] = "Valid Method is required."

            if (
                tracker.get("event_type") != dash.constants.TrackerEventType.IMPRESSION
                and tracker.get("method") == dash.constants.TrackerMethod.JS
            ):
                has_errors = True
                tracker_error["method"] = "Javascript Tag method cannot be used together with Viewability type."

            try:
                if tracker.get("url") is None:
                    raise forms.ValidationError("URL is required.")
                self._validate_tracker_url(tracker.get("url"))
            except forms.ValidationError as e:
                has_errors = True
                tracker_error["url"] = e.message
            try:
                if tracker.get("fallback_url"):
                    self._validate_tracker_url(tracker.get("fallback_url"))
            except forms.ValidationError as e:
                has_errors = True
                tracker_error["fallback_url"] = e.message

            tracker_errors.append(tracker_error)

        if has_errors:
            return json.dumps(tracker_errors)

        return None

    def _validate_url(self, url):
        validate_url = validators.URLValidator(schemes=["http", "https"])
        try:
            validate_url(url)
            return url
        except forms.ValidationError:
            pass

        url = "http://{}".format(url)
        validate_url(url)

        return url

    def _validate_tracker_url(self, url):
        if url.lower().startswith("http://"):
            raise forms.ValidationError("Impression tracker URLs have to be HTTPS")

        try:
            url.encode("ascii")
        except UnicodeEncodeError:
            raise forms.ValidationError("Invalid impression tracker URL")

        validate_url = validators.URLValidator(schemes=["https"])
        try:
            # URL is considered invalid if it contains any unicode chars
            validate_url(url)
        except (forms.ValidationError, UnicodeEncodeError):
            raise forms.ValidationError("Invalid impression tracker URL")
        return url

    def clean_url(self):
        url = self.cleaned_data.get("url").strip()
        try:
            return self._validate_url(url)
        except forms.ValidationError:
            raise forms.ValidationError("Invalid URL")

    def clean_image_url(self):
        image_url = self.cleaned_data.get("image_url").strip()
        try:
            return self._validate_url(image_url)
        except forms.ValidationError:
            raise forms.ValidationError("Invalid image URL")

    def clean_icon_url(self):
        icon_url = self.cleaned_data.get("icon_url").strip()
        if not icon_url:
            return
        try:
            return self._validate_url(icon_url)
        except forms.ValidationError:
            raise forms.ValidationError("Invalid image URL")

    def clean_icon_id(self):
        return self.cleaned_data.get("icon_id") or None

    def clean_icon_hash(self):
        return self.cleaned_data.get("icon_hash") or None

    def clean_primary_tracker_url(self):
        url = self.cleaned_data.get("primary_tracker_url").strip()
        if not url:
            return

        return self._validate_tracker_url(url)

    def clean_secondary_tracker_url(self):
        url = self.cleaned_data.get("secondary_tracker_url").strip()
        if not url:
            return

        return self._validate_tracker_url(url)

    def clean_image_crop(self):
        image_crop = self.cleaned_data.get("image_crop")
        if not image_crop:
            return constants.ImageCrop.CENTER

        if image_crop.lower() in constants.ImageCrop.get_all():
            return image_crop.lower()

        raise forms.ValidationError("Image crop {} is not supported".format(image_crop))

    def _get_status_error_msg(self, cleaned_data):
        finished_statuses = [constants.AsyncUploadJobStatus.FAILED, constants.AsyncUploadJobStatus.OK]

        url_processed = cleaned_data["url_status"] in finished_statuses
        image_processed = cleaned_data["image_status"] in finished_statuses

        icon_fields = [
            cleaned_data["icon_id"],
            cleaned_data["icon_hash"],
            cleaned_data["icon_width"],
            cleaned_data["icon_height"],
            cleaned_data["icon_file_size"],
        ]
        icon_processed = (
            cleaned_data["icon_status"] in finished_statuses
            or not any(icon_fields)
            and cleaned_data["icon_status"] == constants.AsyncUploadJobStatus.PENDING_START
        )

        if not (url_processed and image_processed and icon_processed):
            return "Content ad still processing"

    def _get_image_error_msg(self, cleaned_data):
        image_status = cleaned_data["image_status"]
        if image_status not in [constants.AsyncUploadJobStatus.FAILED, constants.AsyncUploadJobStatus.OK]:
            return

        if image_status == constants.AsyncUploadJobStatus.FAILED:
            return "Image could not be processed"

        return self._validate_image_parameters(cleaned_data) or self._validate_image_size(cleaned_data)

    def _validate_image_parameters(self, cleaned_data):
        if not (
            cleaned_data["image_id"]
            and cleaned_data["image_hash"]
            and cleaned_data["image_width"]
            and cleaned_data["image_height"]
            and cleaned_data["image_file_size"]
        ):
            return "Image could not be processed"

    def _validate_image_size(self, cleaned_data):
        if self.campaign and self.campaign.account.id == settings.HARDCODED_ACCOUNT_ID_OEN:
            return

        image_width = cleaned_data["image_width"]
        image_height = cleaned_data["image_height"]

        if image_width < self.MIN_IMAGE_SIZE or image_height < self.MIN_IMAGE_SIZE:
            return "Image too small (minimum size is {min}x{min} px)".format(min=self.MIN_IMAGE_SIZE)

        if image_width > self.MAX_IMAGE_SIZE or image_height > self.MAX_IMAGE_SIZE:
            return "Image too big (maximum size is {max}x{max} px)".format(max=self.MAX_IMAGE_SIZE)

    def _get_icon_error_msg(self, cleaned_data):
        icon_status = cleaned_data["icon_status"]
        if icon_status not in [constants.AsyncUploadJobStatus.FAILED, constants.AsyncUploadJobStatus.OK]:
            return

        if icon_status == constants.AsyncUploadJobStatus.FAILED:
            return "Image could not be processed"

        return self._validate_icon_parameters(cleaned_data) or self._validate_icon_size(cleaned_data)

    def _validate_icon_parameters(self, cleaned_data):
        icon_fields = [
            cleaned_data["icon_id"],
            cleaned_data["icon_hash"],
            cleaned_data["icon_width"],
            cleaned_data["icon_height"],
            cleaned_data["icon_file_size"],
        ]
        if not (all(icon_fields) or not any(icon_fields)):
            return "Image could not be processed"

    def _validate_icon_size(self, cleaned_data):
        if self.campaign and self.campaign.account.id == settings.HARDCODED_ACCOUNT_ID_OEN:
            return

        icon_width = cleaned_data["icon_width"]
        icon_height = cleaned_data["icon_height"]

        if icon_width is None or icon_height is None:
            return

        if icon_width != icon_height:
            return "Image height and width must be equal"

        if icon_width < self.MIN_ICON_SIZE:
            return "Image too small (minimum size is {min}x{min} px)".format(min=self.MIN_ICON_SIZE)

        if icon_width > self.MAX_IMAGE_SIZE:
            return "Image too big (maximum size is {max}x{max} px)".format(max=self.MAX_IMAGE_SIZE)

    def _get_url_error_msg(self, cleaned_data):
        url_status = cleaned_data["url_status"]
        if url_status == constants.AsyncUploadJobStatus.FAILED:
            return "Content unreachable or invalid"

    def _get_video_asset_id_error_msg(self, cleaned_data):
        if not self.campaign:
            return None
        video_asset_id = cleaned_data["video_asset_id"]
        if self.campaign.type == constants.CampaignType.VIDEO and not video_asset_id:
            return "Video asset required on video campaigns"

        if self.campaign.type != constants.CampaignType.VIDEO and video_asset_id:
            return "Video asset only allowed on video campaigns"

    def _get_tracker_error_msg(self, cleaned_data, tracker):
        tracker_status = cleaned_data[tracker + "_status"]
        if tracker_status == constants.AsyncUploadJobStatus.FAILED:
            return "Invalid or unreachable tracker URL"

    def _get_trackers_error_msg(self, cleaned_data):
        trackers = cleaned_data.get("trackers", [])

        trackers_status_errors = []
        has_status_error = False
        for tracker in trackers:
            trackers_status = cleaned_data.get("trackers_status")
            tracker_status_error = {}
            tracker_status_key = dash.features.contentupload.get_tracker_status_key(
                tracker.get("url"), tracker.get("method")
            )
            if trackers_status and trackers_status.get(tracker_status_key) == constants.AsyncUploadJobStatus.FAILED:
                has_status_error = True
                tracker_status_error["url"] = "Invalid or unreachable tracker URL"

            fallback_url = tracker.get("fallback_url")
            fallback_tracker_status_key = dash.features.contentupload.get_tracker_status_key(
                fallback_url, dash.constants.TrackerMethod.IMG
            )
            if (
                fallback_url
                and trackers_status
                and trackers_status.get(fallback_tracker_status_key) == constants.AsyncUploadJobStatus.FAILED
            ):
                has_status_error = True
                tracker_status_error["fallback_url"] = "Invalid or unreachable tracker URL"

            trackers_status_errors.append(tracker_status_error)

        if has_status_error:
            return json.dumps(trackers_status_errors)

        return self._validate_trackers(trackers)

    def _set_tracker_urls(self, cleaned_data):
        cleaned_data["tracker_urls"] = []
        primary_tracker_url = cleaned_data.get("primary_tracker_url")
        if primary_tracker_url:
            cleaned_data["tracker_urls"].append(primary_tracker_url)

        secondary_tracker_url = self.cleaned_data.get("secondary_tracker_url")
        if secondary_tracker_url:
            cleaned_data["tracker_urls"].append(secondary_tracker_url)

    def clean(self):
        cleaned_data = super(ContentAdForm, self).clean()
        self._set_tracker_urls(cleaned_data)

        status_error_msg = self._get_status_error_msg(cleaned_data)
        if status_error_msg:
            self.add_error(None, status_error_msg)

        image_error_msg = self._get_image_error_msg(cleaned_data)
        if "image_url" in cleaned_data and cleaned_data["image_url"] and image_error_msg:
            self.add_error("image_url", image_error_msg)

        icon_error_msg = self._get_icon_error_msg(cleaned_data)
        if "icon_url" in cleaned_data and cleaned_data["icon_url"] and icon_error_msg:
            self.add_error("icon_url", icon_error_msg)

        url_error_msg = self._get_url_error_msg(cleaned_data)
        if "url" in cleaned_data and cleaned_data["url"] and url_error_msg:
            self.add_error("url", url_error_msg)

        video_asset_id_error_msg = self._get_video_asset_id_error_msg(cleaned_data)
        if "video_asset_id" in cleaned_data and video_asset_id_error_msg:
            self.add_error("video_asset_id", video_asset_id_error_msg)

        primary_tracker_url_error_msg = self._get_tracker_error_msg(cleaned_data, "primary_tracker_url")
        if (
            "primary_tracker_url" in cleaned_data
            and cleaned_data["primary_tracker_url"]
            and primary_tracker_url_error_msg
        ):
            self.add_error("primary_tracker_url", primary_tracker_url_error_msg)

        secondary_tracker_url_error_msg = self._get_tracker_error_msg(cleaned_data, "secondary_tracker_url")
        if (
            "secondary_tracker_url" in cleaned_data
            and cleaned_data["secondary_tracker_url"]
            and secondary_tracker_url_error_msg
        ):
            self.add_error("secondary_tracker_url", secondary_tracker_url_error_msg)

        trackers_error_msg = self._get_trackers_error_msg(cleaned_data)
        if "trackers" in cleaned_data and trackers_error_msg:
            self.add_error("trackers", trackers_error_msg)

        if self.original_content_ad:
            cleaned_data["original_content_ad_id"] = self.original_content_ad.id
            cleaned_data["state"] = self.original_content_ad.state

        return cleaned_data


class ImageAdForm(ContentAdForm):
    title = PlainCharField(
        max_length=90,
        error_messages={
            "required": "Missing ad name",
            "max_length": "Ad name too long (max %(limit_value)d characters)",
        },
    )
    type = forms.TypedChoiceField(
        choices=constants.AdType.get_choices(),
        error_messages={"invalid_choice": "Choose a valid ad type", "required": "Missing ad type"},
        coerce=int,
    )
    image_crop = forms.ChoiceField(choices=constants.ImageCrop.get_choices(), required=False)
    brand_name = PlainCharField(required=False)
    description = PlainCharField(required=False)
    call_to_action = PlainCharField(required=False)

    MAX_IMAGE_FILE_SIZE = 153600

    def clean_type(self):
        if not self.cleaned_data.get("type") == constants.AdType.IMAGE:
            raise forms.ValidationError("Invalid display ad type")
        return self.cleaned_data["type"]

    def _get_status_error_msg(self, cleaned_data):
        finished_statuses = [constants.AsyncUploadJobStatus.FAILED, constants.AsyncUploadJobStatus.OK]
        field_statuses = [cleaned_data["image_status"], cleaned_data["url_status"]]
        if not all(field_status in finished_statuses for field_status in field_statuses):
            return "Content ad still processing"

    def _validate_image_size(self, cleaned_data):
        if not cleaned_data.get("image_width") or not cleaned_data.get("image_height"):
            return

        file_size = cleaned_data.get("image_file_size")
        if file_size and file_size > self.MAX_IMAGE_FILE_SIZE:
            return "Image file size too big (maximum size is 150kb)"

        supported_sizes = constants.DisplayAdSize.get_all()
        if all(
            cleaned_data["image_width"] != size[0] or cleaned_data["image_height"] != size[1]
            for size in supported_sizes
        ):
            sizes = ", ".join([str(s[0]) + "x" + str(s[1]) for s in supported_sizes])
            return "Image size invalid. Supported sizes are (width x height): {sizes}".format(sizes=sizes)

    def _set_defaults(self, cleaned_data):
        self.cleaned_data["brand_name"] = ""
        self.cleaned_data["description"] = ""
        self.cleaned_data["additional_data"] = None
        self.cleaned_data["icon_url"] = None
        self.cleaned_data["icon_id"] = None
        self.cleaned_data["icon_hash"] = None
        self.cleaned_data["icon_width"] = None
        self.cleaned_data["icon_height"] = None
        self.cleaned_data["icon_file_size"] = None
        self.cleaned_data["icon_status"] = constants.AsyncUploadJobStatus.OK
        self.cleaned_data["ad_tag"] = None

    def clean(self):
        self._set_defaults(self.cleaned_data)
        return super().clean()


class AdTagForm(ImageAdForm):
    image_url = PlainCharField(required=False)
    ad_tag = forms.CharField(error_messages={"required": "Missing ad tag"})

    image_width = forms.IntegerField(error_messages={"required": "Missing ad width"})
    image_height = forms.IntegerField(error_messages={"required": "Missing ad height"})

    def clean_type(self):
        if not self.cleaned_data.get("type") == constants.AdType.AD_TAG:
            raise forms.ValidationError("Invalid display ad type")
        return self.cleaned_data["type"]

    def clean_image_url(self):
        return self.cleaned_data.get("image_url")

    def clean_ad_tag(self):
        return self.cleaned_data.get("ad_tag")

    def _get_image_error_msg(self, cleaned_data):
        return

    def _set_defaults(self, cleaned_data):
        self.cleaned_data["brand_name"] = ""
        self.cleaned_data["description"] = ""
        self.cleaned_data["additional_data"] = None
        self.cleaned_data["image_url"] = None
        self.cleaned_data["image_id"] = None
        self.cleaned_data["image_hash"] = None
        self.cleaned_data["image_file_size"] = None
        self.cleaned_data["image_status"] = constants.AsyncUploadJobStatus.OK
        self.cleaned_data["icon_url"] = None
        self.cleaned_data["icon_id"] = None
        self.cleaned_data["icon_hash"] = None
        self.cleaned_data["icon_width"] = None
        self.cleaned_data["icon_height"] = None
        self.cleaned_data["icon_file_size"] = None
        self.cleaned_data["icon_status"] = constants.AsyncUploadJobStatus.OK

    def clean(self):
        ad_size_error = self._validate_image_size(self.cleaned_data)
        if ad_size_error:
            self.add_error("image_url", ad_size_error)
        return super().clean()


class AudienceRuleForm(forms.Form):
    type = forms.ChoiceField(
        choices=constants.AudienceRuleType.get_choices(),
        error_messages={"required": "Please select a type of the rule."},
    )
    value = PlainCharField(required=False, max_length=255)

    def clean_value(self):
        value = self.cleaned_data.get("value")
        rule_type = self.cleaned_data.get("type")

        if not value and rule_type != str(constants.AudienceRuleType.VISIT):
            raise forms.ValidationError("Please enter conditions for the audience.")

        if rule_type == str(constants.AudienceRuleType.STARTS_WITH):
            for url in value.split(","):
                validate_url = validators.URLValidator(schemes=["http", "https"])
                try:
                    validate_url(url)
                except forms.ValidationError:
                    raise forms.ValidationError("Please enter valid URLs.")

        return value


class AudienceRulesField(forms.Field):
    def clean(self, rules):
        if not rules:
            raise forms.ValidationError(self.error_messages["required"])

        for rule in rules:
            rule_form = AudienceRuleForm(rule)
            if not rule_form.is_valid():
                for key, error in rule_form.errors.items():
                    raise forms.ValidationError(error, code=key)
                return

        return rules


class AudienceForm(forms.Form):
    name = PlainCharField(
        max_length=127,
        error_messages={
            "required": "Please specify audience name.",
            "max_length": "Name is too long (max %(limit_value)d characters)",
        },
    )
    pixel_id = forms.IntegerField(error_messages={"required": "Please select a pixel."})
    ttl = forms.IntegerField(
        max_value=365,
        error_messages={
            "required": "Please specify the user retention in days.",
            "max_value": "Maximum number of days is 365.",
        },
    )
    prefill_days = forms.IntegerField(
        required=False, max_value=365, error_messages={"max_value": "Maximum number of days is 365."}
    )
    rules = AudienceRulesField(error_messages={"required": "Please select a rule."})

    def __init__(self, account, user, *args, **kwargs):
        super(AudienceForm, self).__init__(*args, **kwargs)

        self.account = account
        self.user = user


class AudienceUpdateForm(forms.Form):
    name = PlainCharField(
        max_length=127,
        error_messages={
            "required": "Please specify audience name.",
            "max_length": "Name is too long (max %(limit_value)d characters)",
        },
    )


class PublisherGroupEntryForm(forms.Form):
    publisher = PlainCharField(required=True, max_length=127)
    source = forms.ModelChoiceField(queryset=models.Source.objects.all(), required=False)
    placement = PlainCharField(required=False, max_length=127)
    include_subdomains = forms.BooleanField(required=False)
    user = None

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(PublisherGroupEntryForm, self).__init__(*args, **kwargs)

    def clean_placement(self):
        try:
            core.features.publisher_groups.validate_placement(self.data.get("placement"))
        except utils.exc.ValidationError as e:
            raise exceptions.ValidationError(str(e))

        if self.cleaned_data["placement"] == "":
            # If data["placement"] is None, cleaned_data will have an empty string
            return None

        return self.cleaned_data["placement"]


class PublisherTargetingForm(forms.Form):
    entries = forms.Field(required=False)
    status = forms.TypedChoiceField(choices=constants.PublisherTargetingStatus.get_choices(), required=True, coerce=int)
    ad_group = forms.ModelChoiceField(queryset=None, required=False)
    campaign = forms.ModelChoiceField(queryset=None, required=False)
    account = forms.ModelChoiceField(queryset=None, required=False)

    level = forms.TypedChoiceField(choices=constants.PublisherBlacklistLevel.get_choices(), required=False)

    user = None

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PublisherTargetingForm, self).__init__(*args, **kwargs)
        ad_group_qs = models.AdGroup.objects.all().filter_by_entity_permission(user, Permission.WRITE)
        campaign_qs = models.Campaign.objects.all().filter_by_entity_permission(user, Permission.WRITE)
        account_qs = models.Account.objects.all().filter_by_entity_permission(user, Permission.WRITE)

        self.fields["ad_group"].queryset = ad_group_qs
        self.fields["campaign"].queryset = campaign_qs
        self.fields["account"].queryset = account_qs

    def _clean_entries(self, entries):
        clean_entries = []
        for entry in entries if entries else []:
            entry_form = PublisherGroupEntryForm(entry, user=self.user)
            if not entry_form.is_valid():
                for key, error in entry_form.errors.items():
                    raise forms.ValidationError(error, code=key)
                return
            clean_entries.append(entry_form.cleaned_data)

        return clean_entries

    def clean_entries(self):
        entries = self.cleaned_data["entries"]
        return self._clean_entries(entries)

    def clean(self):
        provided_objs = [
            self.cleaned_data.get("ad_group"),
            self.cleaned_data.get("campaign"),
            self.cleaned_data.get("account"),
        ]
        if len([x for x in provided_objs if x]) > 1:
            raise forms.ValidationError("Provide only one of the following constraints: ad group, campaign or account")

        # TODO: hierarchy data is currently not easily available on frontend, make it accessible via levels
        if self.cleaned_data.get("ad_group") and self.cleaned_data.get("level"):
            level = self.cleaned_data["level"]
            if level == constants.PublisherBlacklistLevel.CAMPAIGN:
                self.cleaned_data["campaign"] = self.cleaned_data["ad_group"].campaign
                self.cleaned_data["ad_group"] = None
            elif level == constants.PublisherBlacklistLevel.ACCOUNT:
                self.cleaned_data["account"] = self.cleaned_data["ad_group"].campaign.account
                self.cleaned_data["ad_group"] = None

        return self.cleaned_data

    def get_publisher_group_level_obj(self):
        """
        Returns the lowest non-null object in the adgroup-campaign-account hierarchy
        """

        if self.cleaned_data.get("ad_group"):
            return self.cleaned_data["ad_group"]
        elif self.cleaned_data.get("campaign"):
            return self.cleaned_data["campaign"]
        elif self.cleaned_data.get("account"):
            return self.cleaned_data["account"]
        return None


class PublisherGroupUploadForm(forms.Form, ParseCSVExcelFile):
    id = forms.IntegerField(required=False)
    name = PlainCharField(
        required=True,
        max_length=127,
        error_messages={
            "required": "Please enter a name for this publisher group",
            "max_length": "Publisher group name is too long (%(show_value)d/%(limit_value)d).",
        },
    )
    include_subdomains = forms.BooleanField(required=False)
    agency_id = forms.IntegerField(required=False)
    account_id = forms.IntegerField(required=False)
    entries = forms.FileField(required=False)
    user = None

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(PublisherGroupUploadForm, self).__init__(*args, **kwargs)

    def _get_column_names(self, header):
        # this function maps original CSV column names to internal, normalized
        # ones that are then used across the application
        column_names = [col.lower().replace("(optional)", "").strip(" _").replace(" ", "_") for col in header]

        if "publisher" not in column_names:
            raise forms.ValidationError("Publisher column is required")

        allowed_columns = {"publisher", "source", "placement"}

        extra_columns = []
        for column in header:
            column_name = column.lower().replace("(optional)", "").strip(" _").replace(" ", "_")
            if column_name not in allowed_columns:
                extra_columns.append(column)

        if extra_columns:
            if len(extra_columns) == 1:
                message = "Column {} is not supported"
            else:
                message = "Columns {} are not supported"

            raise forms.ValidationError(message.format(", ".join('"{}"'.format(e) for e in extra_columns)))

        return column_names

    def clean_entries(self):
        entries_file = self.cleaned_data.get("entries")

        if not entries_file:
            if not self.cleaned_data.get("id"):
                raise forms.ValidationError("Please choose a file to upload")
            return entries_file

        rows = self._parse_file(entries_file)
        if len(rows) < 1:
            raise forms.ValidationError("Uploaded file is empty.")

        column_names = self._get_column_names(rows[0])

        data = (dict(list(zip(column_names, row))) for row in rows[1:])
        data = [self._remove_unnecessary_fields(row) for row in data if not self._is_example_row(row)]
        data = [row for row in data if not self._is_empty_row(row)]

        if len(data) < 1:
            raise forms.ValidationError("Uploaded file is empty.")

        for row in data:
            row["include_subdomains"] = bool(self.cleaned_data.get("include_subdomains"))

        return data


class DirectDealConnectionAdminForm(forms.ModelForm):

    # This check couldn't be done one the model validation because it requires the relation to deal to exist.
    def clean_deal(self):
        if (
            self.cleaned_data.get("agency") is not None
            or self.cleaned_data.get("account") is not None
            or self.cleaned_data.get("campaign") is not None
            or self.cleaned_data.get("adgroup") is not None
        ):
            query = (
                models.DirectDealConnection.objects.filter(
                    adgroup__isnull=True,
                    agency__isnull=True,
                    account__isnull=True,
                    campaign__isnull=True,
                    deal_id=self.cleaned_data.get("deal"),
                )
                .values_list("deal__deal_id", flat=True)
                .distinct()
            )
            if query:
                err = "Deal with deal_id {id} already used as global deal".format(id=list(query)[0])
                raise core.features.deals.direct_deal_connection.exceptions.DealAlreadyUsedAsGlobalDeal(err)
        return self.cleaned_data.get("deal")

    def full_clean(self):
        try:
            super(DirectDealConnectionAdminForm, self).full_clean()
        except core.features.deals.direct_deal_connection.exceptions.CannotSetExclusiveAndGlobal as err:
            self.add_error("exclusive", err)
        except core.features.deals.direct_deal_connection.exceptions.CannotSetMultipleEntities as err:
            self.add_error(None, err)
        except core.features.deals.direct_deal_connection.exceptions.DealAlreadyUsedAsGlobalDeal as err:
            self.add_error(None, err)
