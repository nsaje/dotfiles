# -*- coding: utf-8 -*-
# isort:skip_file
import magic
import decimal
import mimetypes
import re

import unicodecsv
import dateutil.parser
import rfc3987
from collections import OrderedDict
from collections import Counter

import xlrd

from django import forms
from django.contrib.postgres import forms as postgres_forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core import validators
from django.utils.html import strip_tags
from django.core import exceptions

import core.features.multicurrency
from dash import constants
from dash import models
from dash.views import helpers
from dash.features.custom_flags.forms import CustomFlagsFormMixin
from utils import dates_helper
from utils import validation_helper

from zemauth.models import User as ZemUser

import stats.constants

import restapi.serializers.targeting
import restapi.adgroup.serializers
import dash.compatibility.forms

MAX_ADS_PER_UPLOAD = 100


class BaseApiForm(forms.Form):
    def get_errors():
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


class DaypartingWidget(forms.Textarea):
    class Media:
        js = ("libs/jquery/jquery-2.1.1.min.js", "js/admin/timezones.js", "js/admin/dayparting.js")
        css = {"all": ("css/admin/dayparting.css",)}


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

    def clean_whitelist_publisher_groups(self):
        publisher_groups = self.cleaned_data.get("whitelist_publisher_groups") or []
        return [x.id for x in publisher_groups]

    def clean_blacklist_publisher_groups(self):
        publisher_groups = self.cleaned_data.get("blacklist_publisher_groups") or []
        return [x.id for x in publisher_groups]


class MulticurrencySettingsFormMixin(forms.Form):
    def get_exchange_rate(self):
        currency = self._get_currency()
        return core.features.multicurrency.get_current_exchange_rate(currency)

    def get_currency_symbol(self):
        currency = self._get_currency()
        return core.features.multicurrency.get_currency_symbol(currency)

    def _get_currency(self):
        if self.account:
            return self.account.currency
        return constants.Currency.USD


class AdGroupAdminForm(forms.ModelForm, CustomFlagsFormMixin):
    SETTINGS_FIELDS = [
        "notes",
        "bluekai_targeting",
        "interest_targeting",
        "exclusion_interest_targeting",
        "redirect_pixel_urls",
        "redirect_javascript",
        "target_devices",
        "target_placements",
        "target_os",
        "click_capping_daily_ad_group_max_clicks",
        "dayparting",
    ]
    notes = PlainCharField(
        required=False,
        widget=forms.Textarea,
        help_text="Describe what kind of additional targeting was setup on the backend.",
    )
    bluekai_targeting = postgres_forms.JSONField(
        required=False,
        help_text='Example: ["and", "bluekai:446103", ["not", ["or", "bluekai:510120", "bluekai:510122"]]]',
    )
    interest_targeting = forms.MultipleChoiceField(
        required=False,
        choices=constants.InterestCategory.get_choices(),
        widget=FilteredSelectMultiple(verbose_name="inclusion interest categories", is_stacked=False),
        help_text="Select interests and demographics you want to include.",
    )
    exclusion_interest_targeting = forms.MultipleChoiceField(
        required=False,
        choices=constants.InterestCategory.get_choices(),
        widget=FilteredSelectMultiple(verbose_name="exclusion interest categories", is_stacked=False),
        help_text="Select interests and demographics you want to exclude.",
    )
    redirect_pixel_urls = postgres_forms.SimpleArrayField(
        PlainCharField(),
        required=False,
        delimiter="\n",
        widget=forms.Textarea,
        help_text="Put every entry in a separate line. Example: https://www.facebook.com/tr?id=531027177051024&ev=PageView&noscript=1.",
    )
    redirect_javascript = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text='Example: <span style="width:600px; display:block">%s</span>' % strip_tags(REDIRECT_JS_HELP_TEXT),
    )
    target_devices = forms.MultipleChoiceField(
        required=False, help_text="Select devices you want to include.", choices=constants.AdTargetDevice.get_choices()
    )
    target_placements = forms.MultipleChoiceField(
        required=False,
        help_text="Select placement media you want to include.",
        choices=constants.Placement.get_choices(),
    )
    target_os = postgres_forms.JSONField(
        required=False,
        help_text="""Example that sets windows targeting OR android version 6.0 OR ios with version range 8.0 - 9.0:<br />
        [<br />
        &emsp;{"name": "windows"},<br />
        &emsp;{"name": "android", "version": {"exact": "android_6_0"}},<br />
        &emsp;{"name": "ios", "version": {"min": "ios_8_0", "max": "ios_9_0"}}<br />
        ]<br /><br />
        Note: version range is inclusive<br />"""
        + """
        <b>Operating system codes:</b> {}<br />
        <b>Operating system version codes:</b> {}<br />
        """.format(
            ", ".join(sorted(str(x[0]) for x in constants.OperatingSystem.get_choices())),
            ", ".join(sorted(str(x[0]) for x in constants.OperatingSystemVersion.get_choices())),
        ),
    )
    click_capping_daily_ad_group_max_clicks = forms.IntegerField(required=False)
    dayparting = postgres_forms.JSONField(
        required=False,
        widget=DaypartingWidget,
        help_text='Choosing an hour of "0" means the ad group will be active between 00:00 and 01:00.',
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
        model = models.Campaign
        fields = "__all__"


class AdGroupSettingsForm(PublisherGroupsFormMixin, MulticurrencySettingsFormMixin, forms.Form):
    bidding_type = forms.TypedChoiceField(
        choices=constants.BiddingType.get_choices(), coerce=int, empty_value=None, required=False
    )
    name = PlainCharField(max_length=127, error_messages={"required": "Please specify ad group name."})
    state = forms.TypedChoiceField(choices=constants.AdGroupSettingsState.get_choices(), coerce=int, empty_value=None)
    start_date = forms.DateField(error_messages={"required": "Please provide start date."})
    end_date = forms.DateField(required=False)
    cpc_cc = forms.DecimalField(decimal_places=4, required=False)
    max_cpm = forms.DecimalField(decimal_places=4, required=False)
    daily_budget_cc = forms.DecimalField(
        min_value=10,
        decimal_places=4,
        required=False,
        error_messages={"min_value": "Please provide budget of at least $10.00."},
    )
    target_devices = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.DevicesSerializer,
        error_messages={"required": "Please select at least one target device."},
    )
    target_os = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.OSsSerializer, required=False
    )
    target_browsers = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.BrowsersSerializer, required=False
    )
    target_placements = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.PlacementsSerializer, required=False
    )
    target_regions = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.TargetRegionsSerializer, required=False
    )
    exclusion_target_regions = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.TargetRegionsSerializer, required=False
    )
    interest_targeting = forms.MultipleChoiceField(required=False, choices=constants.InterestCategory.get_choices())
    exclusion_interest_targeting = forms.MultipleChoiceField(
        required=False, choices=constants.InterestCategory.get_choices()
    )
    tracking_code = PlainCharField(required=False)

    autopilot_state = forms.TypedChoiceField(
        required=False, choices=constants.AdGroupSettingsAutopilotState.get_choices(), coerce=int, empty_value=None
    )

    autopilot_daily_budget = forms.DecimalField(decimal_places=4, required=False)

    retargeting_ad_groups = forms.ModelMultipleChoiceField(
        required=False, queryset=None, error_messages={"invalid_choice": "Invalid ad group selection."}
    )

    exclusion_retargeting_ad_groups = forms.ModelMultipleChoiceField(
        required=False, queryset=None, error_messages={"invalid_choice": "Invalid ad group selection."}
    )

    audience_targeting = forms.ModelMultipleChoiceField(
        required=False, queryset=None, error_messages={"invalid_choice": "Invalid audience selection."}
    )

    exclusion_audience_targeting = forms.ModelMultipleChoiceField(
        required=False, queryset=None, error_messages={"invalid_choice": "Invalid audience selection."}
    )

    bluekai_targeting = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.AudienceSerializer, required=False
    )

    dayparting = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.adgroup.serializers.AdGroupDaypartingSerializer, required=False
    )

    b1_sources_group_enabled = forms.BooleanField(required=False)

    b1_sources_group_daily_budget = forms.DecimalField(decimal_places=4, required=False)

    b1_sources_group_cpc_cc = forms.DecimalField(decimal_places=4, required=False)

    b1_sources_group_cpm = forms.DecimalField(decimal_places=4, required=False)

    b1_sources_group_state = forms.TypedChoiceField(
        required=False, choices=constants.AdGroupSourceSettingsState.get_choices(), coerce=int, empty_value=None
    )

    delivery_type = forms.TypedChoiceField(
        choices=constants.AdGroupDeliveryType.get_choices(), coerce=int, empty_value=None
    )

    click_capping_daily_ad_group_max_clicks = forms.IntegerField(required=False)
    click_capping_daily_click_budget = forms.DecimalField(decimal_places=4, required=False)

    def __init__(self, ad_group, user, *args, **kwargs):
        self.ad_group = ad_group
        self.account = ad_group.campaign.account
        self.user = user

        super(AdGroupSettingsForm, self).__init__(*args, **kwargs)

        self.fields["retargeting_ad_groups"].queryset = models.AdGroup.objects.filter(
            campaign__account=ad_group.campaign.account
        ).filter_by_user(user)
        self.fields["exclusion_retargeting_ad_groups"].queryset = models.AdGroup.objects.filter(
            campaign__account=ad_group.campaign.account
        ).filter_by_user(user)
        self.fields["audience_targeting"].queryset = models.Audience.objects.filter(
            pixel__account_id=ad_group.campaign.account.pk
        )
        self.fields["exclusion_audience_targeting"].queryset = models.Audience.objects.filter(
            pixel__account_id=ad_group.campaign.account.pk
        )
        self.current_settings = self.ad_group.get_current_settings()

    def clean(self):
        cleaned_data = super(AdGroupSettingsForm, self).clean()
        return cleaned_data

    def clean_cpc_cc(self):
        cpc_cc = self.cleaned_data.get("cpc_cc")

        if cpc_cc:
            currency_symbol = self.get_currency_symbol()
            min_cpc_cc = decimal.Decimal("0.05") * self.get_exchange_rate()
            max_cpc_cc = decimal.Decimal("10") * self.get_exchange_rate()

            if cpc_cc < min_cpc_cc:
                raise forms.ValidationError(
                    "Maximum CPC can't be lower than {}{:.2f}.".format(currency_symbol, min_cpc_cc)
                )
            elif cpc_cc > max_cpc_cc:
                raise forms.ValidationError(
                    "Maximum CPC can't be higher than {}{:.2f}.".format(currency_symbol, max_cpc_cc)
                )

        return cpc_cc

    def clean_max_cpm(self):
        max_cpm = self.cleaned_data.get("max_cpm")

        if max_cpm:
            currency_symbol = self.get_currency_symbol()
            min_max_cpm = decimal.Decimal("0.05") * self.get_exchange_rate()
            max_max_cpm = decimal.Decimal("25") * self.get_exchange_rate()

            if max_cpm < min_max_cpm:
                raise forms.ValidationError(
                    "Maximum CPM can't be lower than {}{:.2f}.".format(currency_symbol, min_max_cpm)
                )
            elif max_cpm > max_max_cpm:
                raise forms.ValidationError(
                    "Maximum CPM can't be higher than {}{:.2f}.".format(currency_symbol, max_max_cpm)
                )

        return max_cpm

    def clean_retargeting_ad_groups(self):
        ad_groups = self.cleaned_data.get("retargeting_ad_groups")
        return [ag.id for ag in ad_groups]

    def clean_exclusion_retargeting_ad_groups(self):
        ad_groups = self.cleaned_data.get("exclusion_retargeting_ad_groups")
        return [ag.id for ag in ad_groups]

    def clean_audience_targeting(self):
        audiences = self.cleaned_data.get("audience_targeting")
        return [x.id for x in audiences]

    def clean_exclusion_audience_targeting(self):
        audiences = self.cleaned_data.get("exclusion_audience_targeting")
        return [x.id for x in audiences]

    def clean_end_date(self):
        state = self.cleaned_data.get("state")
        end_date = self.cleaned_data.get("end_date")
        start_date = self.cleaned_data.get("start_date")

        if end_date:
            if start_date and end_date < start_date:
                raise forms.ValidationError("End date must not occur before start date.")

            if end_date < dates_helper.local_today() and state == constants.AdGroupSettingsState.ACTIVE:
                raise forms.ValidationError("End date cannot be set in the past.")

        return end_date

    def clean_tracking_code(self):
        tracking_code = self.cleaned_data.get("tracking_code")

        if tracking_code:
            # This is a bit of a hack we're doing here but if we don't prepend 'http:' to
            # the provided tracking code, then rfc3987 doesn't know how to
            # parse it.
            if not tracking_code.startswith("?"):
                tracking_code = "?" + tracking_code

            test_url = "http:{0}".format(tracking_code)
            # We use { } for macros which rfc3987 doesn't allow so here we replace macros
            # with a single world so that it can still be correctly validated.
            test_url = re.sub("{[^}]+}", "MACRO", test_url)

            try:
                rfc3987.parse(test_url, rule="IRI")
            except ValueError:
                raise forms.ValidationError("Tracking code structure is not valid.")

        return self.cleaned_data.get("tracking_code")

    def clean_target_regions(self):
        target_regions = self.cleaned_data.get("target_regions")
        return target_regions

    def clean_autopilot_state(self):
        autopilot_state = self.cleaned_data.get("autopilot_state")
        return autopilot_state

    def clean_dayparting(self):
        dayparting = self.cleaned_data.get("dayparting")
        if not dayparting:
            dayparting = {}
        return dayparting


class B1SourcesGroupSettingsForm(forms.Form):
    b1_sources_group_daily_budget = forms.DecimalField(decimal_places=4, required=False)

    b1_sources_group_cpc_cc = forms.DecimalField(decimal_places=4, required=False)

    b1_sources_group_cpm = forms.DecimalField(decimal_places=4, required=False)

    b1_sources_group_state = forms.TypedChoiceField(
        required=False, choices=constants.AdGroupSourceSettingsState.get_choices(), coerce=int, empty_value=None
    )

    def __init__(self, ad_group_settings, *args, **kwargs):
        self.ad_group_settings = ad_group_settings
        self.bcm_modifiers = self.ad_group_settings.ad_group.campaign.get_bcm_modifiers()
        super(B1SourcesGroupSettingsForm, self).__init__(*args, **kwargs)


class AdGroupSourceSettingsForm(forms.Form):
    cpc_cc = forms.DecimalField(decimal_places=4, required=False)
    cpm = forms.DecimalField(decimal_places=4, required=False)
    daily_budget_cc = forms.DecimalField(decimal_places=4, required=False)
    state = forms.TypedChoiceField(
        choices=constants.AdGroupSettingsState.get_choices(), coerce=int, required=False, empty_value=None
    )


class AccountSettingsForm(PublisherGroupsFormMixin, forms.Form):
    id = forms.IntegerField()
    name = PlainCharField(max_length=127, required=False, error_messages={"required": "Please specify account name."})
    agency = PlainCharField(max_length=127, required=False)
    default_account_manager = forms.IntegerField(required=False)
    default_sales_representative = forms.IntegerField(required=False)
    default_cs_representative = forms.IntegerField(required=False)
    ob_representative = forms.IntegerField(required=False)
    account_type = forms.IntegerField(required=False)
    # this is a dict with custom validation
    allowed_sources = forms.Field(required=False)
    facebook_page = PlainCharField(max_length=255, required=False)
    salesforce_url = PlainCharField(max_length=255, required=False)
    currency = forms.TypedChoiceField(
        choices=constants.Currency.get_choices(), error_messages={"required": "Please choose currency for account."}
    )
    auto_add_new_sources = forms.BooleanField(required=False)

    def __init__(self, account, *args, **kwargs):
        self.account = account
        super(AccountSettingsForm, self).__init__(*args, **kwargs)

    def clean_currency(self):
        currency = self.cleaned_data.get("currency")
        if self.account.currency != currency and self.account.campaign_set.count() > 0:
            raise forms.ValidationError("Cannot set currency for account with campaigns")
        return currency

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if not name:
            return None

        return name

    def clean_default_account_manager(self):
        account_manager_id = self.cleaned_data.get("default_account_manager")

        if not account_manager_id:
            return None

        try:
            account_manager = ZemUser.objects.get(pk=account_manager_id)
        except ZemUser.DoesNotExist:
            raise forms.ValidationError("Invalid account manager.")

        return account_manager

    def clean_default_sales_representative(self):
        sales_representative_id = self.cleaned_data.get("default_sales_representative")

        if sales_representative_id is None:
            return None

        try:
            sales_representative = ZemUser.objects.get_users_with_perm("campaign_settings_sales_rep").get(
                pk=sales_representative_id
            )
        except ZemUser.DoesNotExist:
            raise forms.ValidationError("Invalid sales representative.")

        return sales_representative

    def clean_default_cs_representative(self):
        cs_representative_id = self.cleaned_data.get("default_cs_representative")

        if cs_representative_id is None:
            return None

        try:
            cs_representative = ZemUser.objects.get_users_with_perm("campaign_settings_cs_rep").get(
                pk=cs_representative_id
            )
        except ZemUser.DoesNotExist:
            raise forms.ValidationError("Invalid CS representative.")

        return cs_representative

    def clean_ob_representative(self):
        ob_representative_id = self.cleaned_data.get("ob_representative")

        if ob_representative_id is None:
            return None

        try:
            ob_representative = ZemUser.objects.get_users_with_perm("can_be_ob_representative").get(
                pk=ob_representative_id
            )
        except ZemUser.DoesNotExist:
            raise forms.ValidationError("Invalid OB representative.")

        return ob_representative

    def clean_account_type(self):
        account_type = self.cleaned_data.get("account_type")

        if account_type is None:
            return None

        if account_type not in constants.AccountType.get_all():
            raise forms.ValidationError("Invalid account type.")

        return account_type

    def clean_allowed_sources(self):
        err = forms.ValidationError("Invalid allowed source.")

        allowed_sources_dict = self.cleaned_data["allowed_sources"]

        if allowed_sources_dict is None:
            return None

        if not isinstance(allowed_sources_dict, dict):
            raise err

        allowed_sources = {}
        for k, v in allowed_sources_dict.items():
            if not isinstance(k, str):
                raise err
            if not isinstance(v, dict):
                raise err

            try:
                key = int(k)
            except Exception:
                raise err

            allowed = v.get("allowed", False)
            allowed_sources[key] = {"allowed": allowed, "name": v.get("name", "")}

        return allowed_sources

    def clean_facebook_page(self):
        facebook_page = self.cleaned_data.get("facebook_page")

        if not facebook_page:
            return None

        return facebook_page


class ConversionPixelForm(forms.Form):
    archived = forms.BooleanField(required=False)
    name = PlainCharField(
        max_length=50,
        required=True,
        error_messages={
            "required": "Please specify a name.",
            "max_length": "Name is too long (%(show_value)d/%(limit_value)d).",
        },
    )
    audience_enabled = forms.BooleanField(required=False)
    redirect_url = forms.URLField(max_length=2048, required=False)
    notes = PlainCharField(required=False)
    additional_pixel = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(ConversionPixelForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ConversionPixelForm, self).clean()
        if cleaned_data.get("additional_pixel") and cleaned_data.get("audience_enabled"):
            self.add_error(
                "additional_pixel",
                ("Additional audience and custom audience cannot " "be enabled at the same time on the same pixel."),
            )


class ConversionGoalForm(forms.Form):
    type = forms.TypedChoiceField(required=True, choices=constants.ConversionGoalType.get_choices(), coerce=int)
    conversion_window = forms.TypedChoiceField(
        required=False, choices=constants.ConversionWindows.get_choices(), coerce=int, empty_value=None
    )
    goal_id = PlainCharField(
        required=True,
        max_length=100,
        error_messages={"max_length": "Conversion goal id is too long (%(show_value)d/%(limit_value)d)."},
    )

    def __init__(self, *args, **kwargs):
        self.campaign_id = kwargs.pop("campaign_id")
        super(ConversionGoalForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ConversionGoalForm, self).clean()

        if not cleaned_data.get("goal_id"):
            return

        if cleaned_data.get("type") == constants.ConversionGoalType.PIXEL:
            self._clean_pixel_goal(cleaned_data)
            return

        self._clean_non_pixel_goal(cleaned_data)

    def _clean_pixel_goal(self, cleaned_data):
        conversion_window = cleaned_data.get("conversion_window")
        if not conversion_window and not self.errors.get("conversion_window"):
            self.add_error("conversion_window", "This field is required.")

        pixel = None
        if cleaned_data["goal_id"] == "__new__":
            self.add_error("goal_id", "The new pixel not successfuly created yet, please try again in a little while.")
        else:
            try:
                pixel = models.ConversionPixel.objects.get(pk=cleaned_data["goal_id"])
            except models.ConversionPixel.DoesNotExist:
                self.add_error("goal_id", "Pixel does not exist.")

        if conversion_window and pixel:
            cleaned_data["name"] = "{} - {}".format(
                pixel.name, constants.ConversionWindows.get_text(cleaned_data["conversion_window"])
            )

    def _clean_non_pixel_goal(self, cleaned_data):
        try:
            models.ConversionGoal.objects.get(
                campaign_id=self.campaign_id, type=cleaned_data.get("type"), goal_id=cleaned_data.get("goal_id")
            )
            self.add_error("goal_id", "This field has to be unique.")
        except models.ConversionGoal.DoesNotExist:
            cleaned_data["name"] = cleaned_data["goal_id"]


class CampaignGoalForm(forms.Form):
    type = forms.TypedChoiceField(required=True, choices=constants.CampaignGoalKPI.get_choices(), coerce=int)
    primary = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.campaign_id = kwargs.pop("campaign_id")
        self.id = kwargs.pop("id") if "id" in kwargs else None
        super(CampaignGoalForm, self).__init__(*args, **kwargs)

    def clean_primary(self):
        primary = self.cleaned_data.get("primary")
        if not primary:
            return False
        goals = models.CampaignGoal.objects.filter(campaign_id=self.campaign_id, primary=True)
        if self.id:
            goals.exclude(pk=self.id)
        if goals.count():
            raise forms.ValidationError("Only one goal can be primary")
        return True

    def clean_type(self):
        goal_type = self.cleaned_data["type"]
        if goal_type == constants.CampaignGoalKPI.CPA:
            goals = models.CampaignGoal.objects.filter(campaign_id=self.campaign_id, type=goal_type)
            if self.id:
                goals.exclude(pk=self.id)
            if goals.count() >= constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
                raise forms.ValidationError("Max conversion goals per campaign exceeded")
            return goal_type

        goals = models.CampaignGoal.objects.filter(campaign_id=self.campaign_id, type=goal_type)
        if self.id:
            goals.exclude(pk=self.id)
        if goals.exists():
            raise forms.ValidationError("Multiple goals of the same type not allowed")
        return goal_type


class CampaignForm(forms.Form):
    campaign_type = forms.TypedChoiceField(choices=constants.CampaignType.get_choices(), coerce=int, required=True)


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
        if "instance" in kwargs:
            self.agency = kwargs.get("instance")
            settings = self.agency.get_current_settings()
            for field in self.SETTINGS_FIELDS:
                initial[field] = getattr(settings, field)
        kwargs["initial"] = initial

        super(AgencyAdminForm, self).__init__(*args, **kwargs)

        self.fields["sales_representative"].queryset = (
            ZemUser.objects.all().exclude(first_name="").exclude(last_name="").order_by("first_name", "last_name")
        )
        self.fields["sales_representative"].label_from_instance = lambda obj: "{} <{}>".format(
            obj.get_full_name(), obj.email or ""
        )
        self.fields["cs_representative"].queryset = (
            ZemUser.objects.all().exclude(first_name="").exclude(last_name="").order_by("first_name", "last_name")
        )
        self.fields["cs_representative"].label_from_instance = lambda obj: "{} <{}>".format(
            obj.get_full_name(), obj.email or ""
        )


class CampaignSettingsForm(PublisherGroupsFormMixin, forms.Form):
    id = forms.IntegerField()
    name = PlainCharField(max_length=127, error_messages={"required": "Please specify campaign name."})
    campaign_goal = forms.TypedChoiceField(choices=constants.CampaignGoal.get_choices(), coerce=int, empty_value=None)
    target_devices = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.DevicesSerializer,
        error_messages={"required": "Please select at least one target device."},
    )
    target_os = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.OSsSerializer, required=False
    )
    target_placements = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.PlacementsSerializer, required=False
    )

    target_regions = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.TargetRegionsSerializer, required=False
    )
    exclusion_target_regions = dash.compatibility.forms.RestFrameworkSerializer(
        restapi.serializers.targeting.TargetRegionsSerializer, required=False
    )

    campaign_manager = forms.IntegerField(required=False)

    language = forms.TypedChoiceField(
        choices=constants.Language.get_choices(),
        error_messages={"required": "Please choose a language in which ads will be created."},
    )

    type = forms.TypedChoiceField(
        coerce=int,
        choices=constants.CampaignType.get_choices(),
        error_messages={"required": "Please choose the type of the campaign."},
    )

    iab_category = forms.ChoiceField(choices=constants.IABCategory.get_choices(), required=False)

    enable_ga_tracking = forms.NullBooleanField(required=False)

    ga_tracking_type = forms.TypedChoiceField(
        required=False, choices=constants.GATrackingType.get_choices(), coerce=int, empty_value=None
    )

    ga_property_id = PlainCharField(max_length=25, required=False)

    enable_adobe_tracking = forms.NullBooleanField(required=False)

    adobe_tracking_param = PlainCharField(max_length=10, required=False)

    autopilot = forms.BooleanField(required=False)

    def __init__(self, campaign, *args, **kwargs):
        self.campaign = campaign
        self.account = campaign.account
        super(CampaignSettingsForm, self).__init__(*args, **kwargs)

    def clean_language(self):
        language = self.cleaned_data.get("language")
        if self.campaign.settings.language != language and self.campaign.adgroup_set.count() > 0:
            raise forms.ValidationError("Cannot set language for campaign with ad groups")
        return language

    def clean_campaign_manager(self):
        campaign_manager_id = self.cleaned_data.get("campaign_manager")
        if campaign_manager_id is None:
            return

        try:
            campaign_manager = ZemUser.objects.get(pk=campaign_manager_id)
        except ZemUser.DoesNotExist:
            raise forms.ValidationError("Invalid campaign manager.")

        return campaign_manager

    def clean_enable_ga_tracking(self):
        # return True if the field is not set or set to True
        return self.cleaned_data.get("enable_ga_tracking", True) is not False

    def clean_ga_property_id(self):
        property_id = self.cleaned_data.get("ga_property_id").strip()
        tracking_type = self.cleaned_data.get("ga_tracking_type")
        enable_ga_tracking = self.cleaned_data.get("enable_ga_tracking")

        if not enable_ga_tracking or tracking_type == constants.GATrackingType.EMAIL:
            return ""  # property ID should not be set when email type is selected

        if not property_id:
            raise forms.ValidationError("Web property ID is required.")

        if not re.match(constants.GA_PROPERTY_ID_REGEX, property_id):
            raise forms.ValidationError("Web property ID is not valid.")

        return property_id

    def clean_enable_adobe_tracking(self):
        # return False if the field is not set or set to False
        return self.cleaned_data.get("enable_adobe_tracking", False) or False


class UserForm(forms.Form):
    email = forms.EmailField(max_length=127, error_messages={"required": "Please specify user's email."})
    first_name = PlainCharField(max_length=127, error_messages={"required": "Please specify first name."})
    last_name = PlainCharField(max_length=127, error_messages={"required": "Please specify last name."})


DISPLAY_URL_MAX_LENGTH = 35
MANDATORY_CSV_FIELDS = ["url", "title", "image_url"]
OPTIONAL_CSV_FIELDS = [
    "display_url",
    "brand_name",
    "description",
    "call_to_action",
    "label",
    "image_crop",
    "primary_tracker_url",
    "secondary_tracker_url",
]
ALL_CSV_FIELDS = MANDATORY_CSV_FIELDS + OPTIONAL_CSV_FIELDS
IGNORED_CSV_FIELDS = ["errors"]

EXPRESSIVE_FIELD_NAME_MAPPING = {
    "primary_impression_tracker_url": "primary_tracker_url",
    "secondary_impression_tracker_url": "secondary_tracker_url",
}
INVERSE_EXPRESSIVE_FIELD_NAME_MAPPING = {v: k for k, v in EXPRESSIVE_FIELD_NAME_MAPPING.items()}

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
        ["display_url", "Display URL"],
        ["brand_name", "Brand name"],
        ["call_to_action", "Call to action"],
        ["description", "Description"],
        ["primary_tracker_url", "Primary impression tracker URL"],
        ["secondary_tracker_url", "Secondary impression tracker URL"],
        ["label", "Label"],
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


EXCEL_MIMETYPES = ("application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


class ParseCSVExcelFile(object):
    def _parse_file(self, candidates_file):
        content = candidates_file.read()
        filename_mimetype, _ = mimetypes.guess_type(candidates_file.name)
        content_mimetype = magic.from_buffer(content, mime=True).split("/")

        if filename_mimetype in EXCEL_MIMETYPES and content_mimetype[0] == "application":
            return self._parse_excel_file(content)
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

    def _get_sheet_row(self, sheet, i):
        return [cell.value for cell in sheet.row(i)]

    def _parse_excel_file(self, content):
        wb = xlrd.open_workbook(file_contents=content)

        if wb.nsheets < 1:
            raise forms.ValidationError("No sheets in excel file.")
        sheet = wb.sheet_by_index(0)

        return [self._get_sheet_row(sheet, i) for i in range(sheet.nrows)]

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


class AdGroupAdsUploadForm(AdGroupAdsUploadBaseForm, ParseCSVExcelFile):
    candidates = forms.FileField(error_messages={"required": "Please choose a file to upload."})

    def _get_column_names(self, header):
        # this function maps original CSV column names to internal, normalized
        # ones that are then used across the application
        column_names = [col.strip(" _").lower().replace(" ", "_") for col in header]

        if len(column_names) < 1 or column_names[0] != "url":
            raise forms.ValidationError("First column in header should be URL.")

        if len(column_names) < 2 or column_names[1] != "title":
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

    def clean_candidates(self):
        candidates_file = self.cleaned_data["candidates"]

        rows = self._parse_file(candidates_file)

        if len(rows) < 1:
            raise forms.ValidationError("Uploaded file is empty.")

        column_names = self._get_column_names(rows[0])

        data = (dict(list(zip(column_names, row))) for row in rows[1:])
        data = [self._remove_unnecessary_fields(row) for row in data if not self._is_example_row(row)]

        if len(data) < 1:
            raise forms.ValidationError("Uploaded file is empty.")

        if len(data) > MAX_ADS_PER_UPLOAD:
            raise forms.ValidationError("Too many content ads (max. {})".format(MAX_ADS_PER_UPLOAD))

        return data


class CreditLineItemForm(forms.ModelForm):
    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]
        if not self.instance.pk or start_date != self.instance.start_date:
            today = dates_helper.local_today()
            if start_date < today:
                raise forms.ValidationError("Start date has to be in the future.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data["end_date"]
        today = dates_helper.local_today()
        if end_date < today:
            raise forms.ValidationError("End date has to be greater or equal to today.")
        return end_date

    def save(self, commit=True, request=None, action_type=None):
        m = super(CreditLineItemForm, self).save(commit=False)
        if commit:
            m.save(request=request, action_type=action_type)
        return m

    class Meta:
        model = models.CreditLineItem
        fields = [
            "account",
            "agency",
            "start_date",
            "end_date",
            "amount",
            "license_fee",
            "status",
            "comment",
            "currency",
            "contract_id",
            "contract_number",
        ]


class BudgetLineItemForm(forms.ModelForm):
    credit = forms.ModelChoiceField(queryset=models.CreditLineItem.objects.all())
    margin = forms.DecimalField(decimal_places=4, max_digits=5, required=False)

    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]
        if not self.instance.pk or start_date != self.instance.start_date:
            today = dates_helper.local_today()
            if start_date < today:
                raise forms.ValidationError("Start date has to be in the future.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data["end_date"]
        if self.instance.pk or end_date != self.instance.end_date:
            today = dates_helper.local_today()
            if end_date < today:
                raise forms.ValidationError("End date has to be in the future.")
        return end_date

    def save(self, commit=True, request=None, action_type=None):
        m = super(BudgetLineItemForm, self).save(commit=False)
        if commit:
            m.save(request=request, action_type=action_type)
        return m

    class Meta:
        model = models.BudgetLineItem
        fields = ["campaign", "credit", "start_date", "end_date", "amount", "comment", "margin"]


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


class ScheduleReportForm(forms.Form):
    granularity = forms.TypedChoiceField(
        required=True, choices=constants.ScheduledReportGranularity.get_choices(), coerce=int
    )
    report_name = PlainCharField(
        required=True,
        max_length=100,
        error_messages={"max_length": "Report name is too long (%(show_value)d/%(limit_value)d)."},
    )
    frequency = forms.TypedChoiceField(
        required=True, choices=constants.ScheduledReportSendingFrequency.get_choices(), coerce=int
    )
    day_of_week = forms.TypedChoiceField(
        required=True, choices=constants.ScheduledReportTimePeriod.get_choices(), coerce=int
    )
    time_period = forms.TypedChoiceField(
        required=True, choices=constants.ScheduledReportTimePeriod.get_choices(), coerce=int
    )
    recipient_emails = MultiEmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(ScheduleReportForm, self).__init__(*args, **kwargs)


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
            "flat_fee_cc",
            "flat_fee_start_date",
            "flat_fee_end_date",
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


class BreakdownForm(forms.Form):
    def __init__(self, user, breakdown, request_body, *args, **kwargs):
        request_body["breakdown"] = breakdown
        self.user = user

        super(BreakdownForm, self).__init__(request_body, *args, **kwargs)

    start_date = forms.DateField(error_messages={"required": "Please provide start date."})

    end_date = forms.DateField(error_messages={"required": "Please provide end date."})

    show_archived = forms.BooleanField(required=False)
    show_blacklisted_publishers = forms.TypedChoiceField(
        required=False, choices=constants.PublisherBlacklistFilter.get_choices(), coerce=str, empty_value=None
    )

    offset = forms.IntegerField(min_value=0, required=True)
    limit = forms.IntegerField(min_value=0, max_value=100, required=True)

    parents = TypedMultipleAnyChoiceField(required=False, coerce=str)

    filtered_sources = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_agencies = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_account_types = TypedMultipleAnyChoiceField(required=False, coerce=str)

    order = PlainCharField(required=False)

    breakdown = PlainCharField(required=True)

    def clean_filtered_sources(self):
        return helpers.get_filtered_sources(self.user, self.cleaned_data.get("filtered_sources"))

    def clean_filtered_agencies(self):
        return helpers.get_filtered_agencies(self.cleaned_data.get("filtered_agencies"))

    def clean_filtered_account_types(self):
        return helpers.get_filtered_account_types(self.cleaned_data.get("filtered_account_types"))

    def clean_breakdown(self):
        return [stats.constants.get_dimension_identifier(x) for x in self.cleaned_data["breakdown"].split("/") if x]

    def clean_parents(self):
        parents = []
        if self.data.get("parents"):
            parents = [str(x) for x in self.data["parents"] if x]
        return parents


class ContentAdCandidateForm(forms.ModelForm):
    image = forms.ImageField(required=False, error_messages={"invalid_image": "Invalid image file"})
    # TODO: Set queryset in __init__ to filter video assets by account
    video_asset_id = forms.ModelChoiceField(queryset=models.VideoAsset.objects.all(), required=False)

    def __init__(self, data, files=None):
        if files and "image" in files:
            files["image"].seek(0)
        super(ContentAdCandidateForm, self).__init__(data, files)

    def clean_image_crop(self):
        image_crop = self.cleaned_data.get("image_crop")
        if not image_crop:
            return constants.ImageCrop.CENTER

        return image_crop.lower()

    def clean_video_asset_id(self):
        video_asset = self.cleaned_data.get("video_asset_id")
        return str(video_asset.id) if video_asset else None

    def clean_call_to_action(self):
        call_to_action = self.cleaned_data.get("call_to_action")
        if not call_to_action:
            return constants.DEFAULT_CALL_TO_ACTION

        return call_to_action

    class Meta:
        model = models.ContentAdCandidate
        fields = [
            "label",
            "url",
            "title",
            "image_url",
            "image_crop",
            "video_asset_id",
            "display_url",
            "brand_name",
            "description",
            "call_to_action",
            "primary_tracker_url",
            "secondary_tracker_url",
            "additional_data",
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
    image_width = forms.IntegerField(required=False)
    image_height = forms.IntegerField(required=False)

    image_status = forms.IntegerField(required=False)
    url_status = forms.IntegerField(required=False)

    MIN_IMAGE_SIZE = 300
    MAX_IMAGE_SIZE = 10000

    def __init__(self, campaign, *args, **kwargs):
        super(ContentAdForm, self).__init__(*args, **kwargs)
        self.campaign = campaign

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

    def _get_image_error_msg(self, cleaned_data):
        image_status = cleaned_data["image_status"]
        if image_status not in [constants.AsyncUploadJobStatus.FAILED, constants.AsyncUploadJobStatus.OK]:
            return

        if image_status == constants.AsyncUploadJobStatus.FAILED:
            return "Image could not be processed"

        if image_status == constants.AsyncUploadJobStatus.OK and not (
            cleaned_data["image_id"]
            and cleaned_data["image_hash"]
            and cleaned_data["image_width"]
            and cleaned_data["image_height"]
        ):
            return "Image could not be processed"

        if cleaned_data["image_width"] < self.MIN_IMAGE_SIZE or cleaned_data["image_height"] < self.MIN_IMAGE_SIZE:
            return "Image too small (minimum size is {min}x{min} px)".format(min=self.MIN_IMAGE_SIZE)

        if cleaned_data["image_width"] > self.MAX_IMAGE_SIZE or cleaned_data["image_height"] > self.MAX_IMAGE_SIZE:
            return "Image too big (maximum size is {max}x{max} px)".format(max=self.MAX_IMAGE_SIZE)

    def _get_url_error_msg(self, cleaned_data):
        url_status = cleaned_data["url_status"]
        if url_status == constants.AsyncUploadJobStatus.FAILED:
            return "Content unreachable"

    def _get_video_asset_id_error_msg(self, cleaned_data):
        if not self.campaign:
            return None
        video_asset_id = cleaned_data["video_asset_id"]
        if self.campaign.type == constants.CampaignType.VIDEO and not video_asset_id:
            return "Video asset required on video campaigns"

        if self.campaign.type != constants.CampaignType.VIDEO and video_asset_id:
            return "Video asset only allowed on video campaigns"

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

        finished_statuses = [constants.AsyncUploadJobStatus.FAILED, constants.AsyncUploadJobStatus.OK]
        if cleaned_data["image_status"] not in finished_statuses or cleaned_data["url_status"] not in finished_statuses:
            self.add_error(None, "Content ad still processing")

        image_error_msg = self._get_image_error_msg(cleaned_data)
        if "image_url" in cleaned_data and cleaned_data["image_url"] and image_error_msg:
            self.add_error("image_url", image_error_msg)

        url_error_msg = self._get_url_error_msg(cleaned_data)
        if "url" in cleaned_data and cleaned_data["url"] and url_error_msg:
            self.add_error("url", url_error_msg)

        video_asset_id_error_msg = self._get_video_asset_id_error_msg(cleaned_data)
        if "video_asset_id" in cleaned_data and video_asset_id_error_msg:
            self.add_error("video_asset_id", video_asset_id_error_msg)

        return cleaned_data


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
    pixel_id = forms.IntegerField(error_messages={"required": "Please select pixel."})
    ttl = forms.IntegerField(
        max_value=365, error_messages={"required": "Please select days.", "max_value": "Maximum number of days is 365."}
    )
    prefill_days = forms.IntegerField(
        required=False, max_value=365, error_messages={"max_value": "Maximum number of days is 365."}
    )
    rules = AudienceRulesField(error_messages={"required": "Please select a rule."})

    def __init__(self, account, user, *args, **kwargs):
        super(AudienceForm, self).__init__(*args, **kwargs)

        self.account = account
        self.user = user

    def clean_prefill_days(self):
        value = self.cleaned_data.get("prefill_days")
        return value if value is not None else 0

    def clean_pixel_id(self):
        pixel_id = self.cleaned_data.get("pixel_id")
        pixel = models.ConversionPixel.objects.filter(pk=pixel_id, account=self.account)
        if not pixel:
            raise forms.ValidationError("Pixel does not exist.")

        pixel = pixel[0]
        if pixel.archived:
            raise forms.ValidationError("Pixel is archived.")

        return pixel_id

    def clean(self):
        if self.cleaned_data.get("rules") is None:
            return self.cleaned_data

        ttl = self.cleaned_data.get("ttl")
        rules = [(rule["type"], rule["value"] or "") for rule in self.cleaned_data.get("rules")]
        pixel_id = self.cleaned_data.get("pixel_id")
        audience_ids = models.Audience.objects.filter(ttl=ttl, pixel_id=pixel_id, archived=False).values("id")
        audience_ids = [a["id"] for a in audience_ids]

        for rule in models.AudienceRule.objects.filter(audience_id__in=audience_ids).values(
            "audience_id", "value", "type"
        ):
            row = (rule["type"], rule["value"])
            if row in rules:
                existing_audience_names = models.Audience.objects.filter(id=rule["audience_id"]).values("name")
                if len(existing_audience_names) > 0:
                    self.add_error(
                        "pixel_id",
                        'Audience rule "%s" with the same ttl and rule already exists.'
                        % existing_audience_names[0]["name"],
                    )
                    break

        return self.cleaned_data


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
    include_subdomains = forms.BooleanField(required=False)


class PublisherTargetingForm(forms.Form):
    entries = forms.Field(required=False)
    status = forms.TypedChoiceField(choices=constants.PublisherTargetingStatus.get_choices(), required=True, coerce=int)
    ad_group = forms.ModelChoiceField(queryset=None, required=False)
    campaign = forms.ModelChoiceField(queryset=None, required=False)
    account = forms.ModelChoiceField(queryset=None, required=False)

    level = forms.TypedChoiceField(choices=constants.PublisherBlacklistLevel.get_choices(), required=False)

    enforce_cpc = forms.BooleanField(required=False)

    # bulk selection fields
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    select_all = forms.BooleanField(required=False)
    entries_not_selected = forms.Field(required=False)
    filtered_sources = TypedMultipleAnyChoiceField(required=False, coerce=str)

    def __init__(self, user, *args, **kwargs):
        super(PublisherTargetingForm, self).__init__(*args, **kwargs)
        self.user = user

        self.fields["ad_group"].queryset = models.AdGroup.objects.all().filter_by_user(user)
        self.fields["campaign"].queryset = models.Campaign.objects.all().filter_by_user(user)
        self.fields["account"].queryset = models.Account.objects.all().filter_by_user(user)

    def _clean_entries(self, entries):
        clean_entries = []
        for entry in entries if entries else []:
            entry_form = PublisherGroupEntryForm(entry)
            if not entry_form.is_valid():
                for key, error in entry_form.errors.items():
                    raise forms.ValidationError(error, code=key)
                return
            clean_entries.append(entry_form.cleaned_data)

        return clean_entries

    def clean_entries(self):
        entries = self.cleaned_data["entries"]
        return self._clean_entries(entries)

    def clean_entries_not_selected(self):
        entries = self.cleaned_data["entries_not_selected"]
        return self._clean_entries(entries)

    def clean_select_all(self):
        if self.cleaned_data["select_all"] and not (
            self.cleaned_data.get("start_date") and self.cleaned_data.get("end_date")
        ):
            raise forms.ValidationError("Please specify start and end date when selecting all publishers")
        return self.cleaned_data["select_all"]

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

    def clean_filtered_sources(self):
        return helpers.get_filtered_sources(self.user, self.cleaned_data.get("filtered_sources"))


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
    entries = forms.FileField(required=False)

    def _get_column_names(self, header):
        # this function maps original CSV column names to internal, normalized
        # ones that are then used across the application
        column_names = [col.strip(" _").lower().replace(" ", "_") for col in header]

        if len(column_names) < 1 or column_names[0] != "publisher":
            raise forms.ValidationError("First column in header should be Publisher.")

        if len(column_names) >= 2 and column_names[1] != "source":
            raise forms.ValidationError("Second column in header should be Source.")

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
