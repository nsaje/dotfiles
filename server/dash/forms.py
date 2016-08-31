# -*- coding: utf-8 -*-
import magic
import decimal
import re
import unicodecsv
import dateutil.parser
import rfc3987
from collections import OrderedDict

from collections import Counter

from django import forms
from django.contrib.postgres import forms as postgres_forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import transaction
from django.core import validators

from automation import autopilot_budgets
from dash import api
from dash import constants
from dash import models
from dash import regions
from dash import validation_helpers
from dash.views import helpers
from utils import dates_helper

from zemauth.models import User as ZemUser

import actionlog.api_contentads
import actionlog.zwei_actions

import stats.constants


MAX_ADS_PER_UPLOAD = 100
DEFAULT_CALL_TO_ACTION = 'Read more'


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


class AdGroupAdminForm(forms.ModelForm):
    SETTINGS_FIELDS = [
        'notes',
        'bluekai_targeting',
        'interest_targeting',
        'exclusion_interest_targeting',
        'redirect_pixel_urls',
        'redirect_javascript'
    ]
    notes = forms.CharField(required=False, widget=forms.Textarea)
    bluekai_targeting = postgres_forms.JSONField(required=False)
    interest_targeting = forms.MultipleChoiceField(
        required=False,
        choices=constants.InterestCategory.get_choices(),
        widget=FilteredSelectMultiple(verbose_name="inclusion interest categories",
                                      is_stacked=False)
    )
    exclusion_interest_targeting = forms.MultipleChoiceField(
        required=False,
        choices=constants.InterestCategory.get_choices(),
        widget=FilteredSelectMultiple(verbose_name="exclusion interest categories",
                                      is_stacked=False)
    )
    redirect_pixel_urls = postgres_forms.SimpleArrayField(
        forms.CharField(),
        required=False,
        delimiter='\n',
        widget=forms.Textarea,
        help_text='Put every entry on a separate line'
    )
    redirect_javascript = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial['bluekai_targeting'] = []  # default to empty list instead of null
        if 'instance' in kwargs:
            settings = kwargs['instance'].get_current_settings()
            for field in self.SETTINGS_FIELDS:
                initial[field] = getattr(settings, field)
        kwargs['initial'] = initial
        super(AdGroupAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.Campaign
        fields = '__all__'


class AdGroupSettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify ad group name.'}
    )
    start_date = forms.DateField(
        error_messages={
            'required': 'Please provide start date.',
        }
    )
    end_date = forms.DateField(required=False)
    cpc_cc = forms.DecimalField(
        min_value=decimal.Decimal('0.05'),
        max_value=decimal.Decimal('10'),
        decimal_places=4,
        required=False,
        error_messages={
            'min_value': 'Maximum CPC can\'t be lower than $0.05.',
            'max_value': 'Maximum CPC can\'t be higher than $10.00.'
        }
    )
    daily_budget_cc = forms.DecimalField(
        min_value=10,
        decimal_places=4,
        required=False,
        error_messages={
            'min_value': 'Please provide budget of at least $10.00.'
        }
    )
    target_devices = forms.MultipleChoiceField(
        choices=constants.AdTargetDevice.get_choices(),
        error_messages={
            'required': 'Please select at least one target device.',
        }
    )
    target_regions = forms.MultipleChoiceField(
        required=False,
        choices=constants.AdTargetLocation.get_choices()
    )
    tracking_code = forms.CharField(required=False)

    enable_ga_tracking = forms.NullBooleanField(required=False)

    ga_tracking_type = forms.TypedChoiceField(
        required=False,
        choices=constants.GATrackingType.get_choices(),
        coerce=int,
        empty_value=None
    )

    ga_property_id = forms.CharField(max_length=25, required=False)

    enable_adobe_tracking = forms.NullBooleanField(required=False)

    adobe_tracking_param = forms.CharField(max_length=10, required=False)

    autopilot_state = forms.TypedChoiceField(
        required=False,
        choices=constants.AdGroupSettingsAutopilotState.get_choices(),
        coerce=int,
        empty_value=None
    )

    autopilot_daily_budget = forms.DecimalField(
        decimal_places=4,
        required=False
    )

    retargeting_ad_groups = forms.ModelMultipleChoiceField(
        required=False,
        queryset=None,
        error_messages={
            'invalid_choice': 'Invalid ad group selection.'
        }
    )

    def __init__(self, ad_group, user, *args, **kwargs):
        super(AdGroupSettingsForm, self).__init__(*args, **kwargs)

        self.ad_group = ad_group
        self.fields['retargeting_ad_groups'].queryset = models.AdGroup.objects.filter(
            campaign__account=ad_group.campaign.account).filter_by_user(user)
        self.current_settings = self.ad_group.get_current_settings()

    def clean_retargeting_ad_groups(self):
        ad_groups = self.cleaned_data.get('retargeting_ad_groups')
        return [ag.id for ag in ad_groups]

    def clean_end_date(self):
        state = self.current_settings.state
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')

        if end_date:
            if start_date and end_date < start_date:
                raise forms.ValidationError('End date must not occur before start date.')

            if end_date < dates_helper.local_today() and state == constants.AdGroupSettingsState.ACTIVE:
                raise forms.ValidationError('End date cannot be set in the past.')

        if self.current_settings.landing_mode:
            raise forms.ValidationError('End date cannot be set when campaign is in landing mode.')

        return end_date

    def clean_enable_ga_tracking(self):
        # return True if the field is not set or set to True
        return self.cleaned_data.get('enable_ga_tracking', True) is not False

    def clean_ga_property_id(self):
        property_id = self.cleaned_data.get('ga_property_id').strip()
        tracking_type = self.cleaned_data.get('ga_tracking_type')
        enable_ga_tracking = self.cleaned_data.get('enable_ga_tracking')

        if not enable_ga_tracking or tracking_type == constants.GATrackingType.EMAIL:
            return None  # property ID should not be set when email type is selected

        if not property_id:
            raise forms.ValidationError('Web property ID is required.')

        if not re.match(constants.GA_PROPERTY_ID_REGEX, property_id):
            raise forms.ValidationError('Web property ID is not valid.')

        return property_id

    def clean_enable_adobe_tracking(self):
        # return False if the field is not set or set to False
        return self.cleaned_data.get('enable_adobe_tracking', False) or False

    def clean_tracking_code(self):
        tracking_code = self.cleaned_data.get('tracking_code')

        err_msg = 'Tracking code structure is not valid.'

        if tracking_code:
            # This is a bit of a hack we're doing here but if we don't prepend 'http:' to
            # the provided tracking code, then rfc3987 doesn't know how to parse it.
            if not tracking_code.startswith('?'):
                tracking_code = '?' + tracking_code

            test_url = 'http:{0}'.format(tracking_code)
            # We use { } for macros which rfc3987 doesn't allow so here we replace macros
            # with a single world so that it can still be correctly validated.
            test_url = re.sub('{[^}]+}', 'MACRO', test_url)

            try:
                rfc3987.parse(test_url, rule='IRI')
            except ValueError:
                raise forms.ValidationError(err_msg)

        return self.cleaned_data.get('tracking_code')

    def clean_target_regions(self):
        target_regions = self.cleaned_data.get('target_regions')

        if 'US' in target_regions and any([tr in regions.DMA_BY_CODE for tr in target_regions]):
            raise forms.ValidationError('DMAs are a subset of United States demographic targeting.')

        return target_regions

    def clean_autopilot_state(self):
        autopilot_state = self.cleaned_data.get('autopilot_state')
        return autopilot_state

    def clean_autopilot_daily_budget(self):
        budget = self.cleaned_data.get('autopilot_daily_budget', 0)
        ap_state = self.cleaned_data.get('autopilot_state')
        budget_ap_is_active = ap_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        budget_insufficient = budget < autopilot_budgets.get_adgroup_minimum_daily_budget(self.ad_group)
        if budget_ap_is_active and budget_insufficient:
            raise forms.ValidationError(message='Total Daily Budget must be at least $' +
                                        str(autopilot_budgets.get_adgroup_minimum_daily_budget(self.ad_group)))
        return self.cleaned_data.get('autopilot_daily_budget')


class AdGroupSourceSettingsCpcForm(forms.Form):
    cpc_cc = forms.DecimalField(
        decimal_places=4,
        error_messages={
            'required': 'This value is required'
        }
    )

    def __init__(self, *args, **kwargs):
        self.ad_group_source = kwargs.pop('ad_group_source')
        super(AdGroupSourceSettingsCpcForm, self).__init__(*args, **kwargs)

    def clean_cpc_cc(self):
        cpc_cc = self.cleaned_data.get('cpc_cc')
        validation_helpers.validate_ad_group_source_cpc_cc(cpc_cc, self.ad_group_source)


class AdGroupSourceSettingsDailyBudgetForm(forms.Form):
    daily_budget_cc = forms.DecimalField(
        decimal_places=4,
        error_messages={
            'required': 'This value is required',
        }
    )

    def __init__(self, *args, **kwargs):
        self.ad_group_source = kwargs.pop('ad_group_source')
        super(AdGroupSourceSettingsDailyBudgetForm, self).__init__(*args, **kwargs)

    def clean_daily_budget_cc(self):
        daily_budget_cc = self.cleaned_data.get('daily_budget_cc')
        source_type = self.ad_group_source.source.source_type

        validation_helpers.validate_daily_budget_cc(daily_budget_cc, source_type)


class AdGroupSourceSettingsStateForm(forms.Form):
    state = forms.TypedChoiceField(
        choices=constants.AdGroupSettingsState.get_choices(),
        coerce=int,
        empty_value=None
    )


class AccountSettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        required=False,
        error_messages={'required': 'Please specify account name.'}
    )
    agency = forms.CharField(
        max_length=127,
        required=False,
    )
    default_account_manager = forms.IntegerField(
        required=False
    )
    default_sales_representative = forms.IntegerField(
        required=False
    )
    account_type = forms.IntegerField(
        required=False
    )
    # this is a dict with custom validation
    allowed_sources = forms.Field(required=False)
    facebook_page = forms.CharField(max_length=255, required=False)

    def clean_name(self):
        name = self.cleaned_data.get('name')

        if not name:
            return None

        account_id = self.cleaned_data.get('id')

        if models.Account.objects.filter(name=name).exclude(id=account_id).exists():
            raise forms.ValidationError("Invalid account name.")

        return name

    def clean_default_account_manager(self):
        account_manager_id = self.cleaned_data.get('default_account_manager')

        if not account_manager_id:
            return None

        err_msg = 'Invalid account manager.'
        try:
            account_manager = ZemUser.objects.get(pk=account_manager_id)
        except ZemUser.DoesNotExist:
            raise forms.ValidationError(err_msg)

        return account_manager

    def clean_default_sales_representative(self):
        sales_representative_id = self.cleaned_data.get('default_sales_representative')

        if sales_representative_id is None:
            return None

        err_msg = 'Invalid sales representative.'

        try:
            sales_representative = ZemUser.objects.\
                get_users_with_perm('campaign_settings_sales_rep').\
                get(pk=sales_representative_id)
        except ZemUser.DoesNotExist:
            raise forms.ValidationError(err_msg)

        return sales_representative

    def clean_account_type(self):
        account_type = self.cleaned_data.get('account_type')

        if account_type is None:
            return None

        if account_type not in constants.AccountType.get_all():
            raise forms.ValidationError('Invalid account type.')

        return account_type

    def clean_allowed_sources(self):
        err = forms.ValidationError('Invalid allowed source.')

        allowed_sources_dict = self.cleaned_data['allowed_sources']

        if allowed_sources_dict is None:
            return None

        if not isinstance(allowed_sources_dict, dict):
            raise err

        allowed_sources = {}
        for k, v in allowed_sources_dict.iteritems():
            if not isinstance(k, basestring):
                raise err
            if not isinstance(v, dict):
                raise err

            try:
                key = int(k)
            except:
                raise err

            allowed = v.get('allowed', False)
            allowed_sources[key] = {'allowed': allowed, 'name': v.get('name', '')}

        return allowed_sources

    def clean_facebook_page(self):
        facebook_page = self.cleaned_data.get('facebook_page')

        if not facebook_page:
            return None

        return facebook_page


class ConversionPixelForm(forms.Form):
    archived = forms.BooleanField(required=False)
    name = forms.CharField(
        max_length=50,
        required=True,
        error_messages={
            'required': 'Please specify a name.',
            'max_length': 'Name is too long (%(show_value)d/%(limit_value)d).',
        }
    )


class ConversionGoalForm(forms.Form):
    type = forms.TypedChoiceField(
        required=True,
        choices=constants.ConversionGoalType.get_choices(),
        coerce=int,
    )
    conversion_window = forms.TypedChoiceField(
        required=False,
        choices=constants.ConversionWindows.get_choices(),
        coerce=int,
        empty_value=None,
    )
    goal_id = forms.CharField(
        required=True,
        max_length=100,
        error_messages={
            'max_length': 'Conversion goal id is too long (%(show_value)d/%(limit_value)d).',
        }
    )

    def __init__(self, *args, **kwargs):
        self.campaign_id = kwargs.pop('campaign_id')
        super(ConversionGoalForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ConversionGoalForm, self).clean()

        if not cleaned_data.get('goal_id'):
            return

        if cleaned_data.get('type') == constants.ConversionGoalType.PIXEL:
            self._clean_pixel_goal(cleaned_data)
            return

        self._clean_non_pixel_goal(cleaned_data)

    def _clean_pixel_goal(self, cleaned_data):
        conversion_window = cleaned_data.get('conversion_window')
        if not conversion_window and not self.errors.get('conversion_window'):
            self.add_error('conversion_window', 'This field is required.')

        pixel = None
        try:
            pixel = models.ConversionPixel.objects.get(pk=cleaned_data['goal_id'])
        except models.ConversionPixel.DoesNotExist:
            self.add_error('goal_id', 'Pixel does not exist.')

        if conversion_window and pixel:
            cleaned_data['name'] = '{} - {}'.format(
                pixel.name,
                constants.ConversionWindows.get_text(cleaned_data['conversion_window'])
            )

    def _clean_non_pixel_goal(self, cleaned_data):
        try:
            models.ConversionGoal.objects.get(campaign_id=self.campaign_id,
                                              type=cleaned_data.get('type'),
                                              goal_id=cleaned_data.get('goal_id'))
            self.add_error('goal_id', 'This field has to be unique.')
        except models.ConversionGoal.DoesNotExist:
            cleaned_data['name'] = cleaned_data['goal_id']


class CampaignGoalForm(forms.Form):
    type = forms.TypedChoiceField(
        required=True,
        choices=constants.CampaignGoalKPI.get_choices(),
        coerce=int
    )
    primary = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.campaign_id = kwargs.pop('campaign_id')
        self.id = kwargs.pop('id') if 'id' in kwargs else None
        super(CampaignGoalForm, self).__init__(*args, **kwargs)

    def clean_primary(self):
        primary = self.cleaned_data.get('primary')
        if not primary:
            return False
        goals = models.CampaignGoal.objects.filter(campaign_id=self.campaign_id, primary=True)
        if self.id:
            goals.exclude(pk=self.id)
        if goals.count():
            raise forms.ValidationError('Only one goal can be primary')
        return True

    def clean_type(self):
        goal_type = self.cleaned_data['type']
        if goal_type == constants.CampaignGoalKPI.CPA:
            goals = models.CampaignGoal.objects.filter(campaign_id=self.campaign_id, type=goal_type)
            if self.id:
                goals.exclude(pk=self.id)
            if goals.count() > constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
                raise forms.ValidationError('Max conversion goals per campaign exceeded')
            return goal_type

        goals = models.CampaignGoal.objects.filter(campaign_id=self.campaign_id, type=goal_type)
        if self.id:
            goals.exclude(pk=self.id)
        if goals.count():
            raise forms.ValidationError('Multiple goals of the same type not allowed')
        return goal_type


class CampaignAdminForm(forms.ModelForm):
    automatic_campaign_stop = forms.BooleanField(required=False,
                                                 label='Automatic campaign stop on low budget')

    def __init__(self, *args, **kwargs):
        initial = {
            'automatic_campaign_stop': True,
        }
        if 'instance' in kwargs:
            settings = kwargs['instance'].get_current_settings()
            initial['automatic_campaign_stop'] = settings.automatic_campaign_stop
        super(CampaignAdminForm, self).__init__(initial=initial, *args, **kwargs)

    class Meta:
        model = models.Campaign
        exclude = (
            'users', 'groups', 'created_dt', 'modified_dt', 'modified_by',
        )


class CampaignSettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'}
    )
    campaign_goal = forms.TypedChoiceField(
        choices=constants.CampaignGoal.get_choices(),
        coerce=int,
        empty_value=None
    )
    goal_quantity = forms.DecimalField(decimal_places=4)
    target_devices = forms.MultipleChoiceField(
        choices=constants.AdTargetDevice.get_choices(),
        error_messages={
            'required': 'Please select at least one target device.',
        }
    )
    target_regions = forms.MultipleChoiceField(
        required=False,
        choices=constants.AdTargetLocation.get_choices()
    )

    campaign_manager = forms.IntegerField(required=False)
    iab_category = forms.ChoiceField(
        choices=constants.IABCategory.get_choices(),
        required=False,
    )

    def clean_campaign_manager(self):
        campaign_manager_id = self.cleaned_data.get('campaign_manager')
        if campaign_manager_id is None:
            return

        err_msg = 'Invalid campaign manager.'

        try:
            campaign_manager = ZemUser.objects.get(pk=campaign_manager_id)
        except ZemUser.DoesNotExist:
            raise forms.ValidationError(err_msg)

        return campaign_manager


class UserForm(forms.Form):
    email = forms.EmailField(
        max_length=127,
        error_messages={'required': 'Please specify user\'s email.'}
    )
    first_name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify first name.'}
    )
    last_name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify last name.'}
    )


DISPLAY_URL_MAX_LENGTH = 25
MANDATORY_CSV_FIELDS = ['url', 'title', 'image_url']
OPTIONAL_CSV_FIELDS = ['display_url', 'brand_name', 'description', 'call_to_action', 'label', 'image_crop',
                       'primary_tracker_url', 'secondary_tracker_url']
ALL_CSV_FIELDS = MANDATORY_CSV_FIELDS + OPTIONAL_CSV_FIELDS
IGNORED_CSV_FIELDS = ['errors']

EXPRESSIVE_FIELD_NAME_MAPPING = {
    'primary_impression_tracker_url': 'primary_tracker_url',
    'secondary_impression_tracker_url': 'secondary_tracker_url',
}
INVERSE_EXPRESSIVE_FIELD_NAME_MAPPING = {v: k for k, v in EXPRESSIVE_FIELD_NAME_MAPPING.iteritems()}

# Example CSV content - must be ignored if mistakenly uploaded
# Example File is served by client (Zemanta_Content_Ads_Template.csv)
EXAMPLE_CSV_CONTENT = {
    'url': 'http://www.zemanta.com/insights/2016/6/13/8-tips-for-creating-clickable-content',
    'title': '8 Tips for Creating Clickable Content',
    'image_url': 'http://static1.squarespace.com/static/56bbb88007eaa031a14e3472/'
                 '56ce2a0206dcb7970cb2a080/575f341659827ef48ecb2253/1466510434775/'
                 'coffee-apple-iphone-laptop.jpg?format=1500w',
}

CSV_EXPORT_COLUMN_NAMES_DICT = OrderedDict([
    ['url', 'URL'],
    ['title', 'Title'],
    ['image_url', 'Image URL'],
    ['image_crop', 'Image crop'],
    ['display_url', 'Display URL'],
    ['brand_name', 'Brand name'],
    ['call_to_action', 'Call to action'],
    ['description', 'Description'],
    ['primary_tracker_url', 'Primary impression tracker URL'],
    ['secondary_tracker_url', 'Secondary impression tracker URL'],
    ['label', 'Label'],
])


class DisplayURLField(forms.URLField):

    def clean(self, value):
        display_url = super(forms.URLField, self).clean(value)
        display_url = display_url.strip()
        display_url = re.sub(r'^https?://', '', display_url)
        display_url = re.sub(r'/$', '', display_url)

        validate_length = validators.MaxLengthValidator(
            DISPLAY_URL_MAX_LENGTH, message=self.error_messages['max_length'])
        validate_length(display_url)

        return display_url


class AdGroupAdsUploadBaseForm(forms.Form):
    batch_name = forms.CharField(
        required=True,
        max_length=255,
        error_messages={
            'required': 'Please enter a name for this upload.',
            'max_length': 'Batch name is too long (%(show_value)d/%(limit_value)d).'
        }
    )


class AdGroupAdsUploadForm(AdGroupAdsUploadBaseForm):
    candidates = forms.FileField(
        error_messages={'required': 'Please choose a file to upload.'}
    )

    def _get_csv_header(self, lines):
        reader = unicodecsv.reader(lines)

        try:
            return next(reader)
        except StopIteration:
            raise forms.ValidationError('Uploaded file is empty.')

    def _get_csv_column_names(self, header):
        # this function maps original CSV column names to internal, normalized
        # ones that are then used across the application
        column_names = [col.strip(" _").lower().replace(' ', '_') for col in header]

        if len(column_names) < 1 or column_names[0] != 'url':
            raise forms.ValidationError('First column in header should be URL.')

        if len(column_names) < 2 or column_names[1] != 'title':
            raise forms.ValidationError('Second column in header should be Title.')

        if len(column_names) < 3 or column_names[2] != 'image_url':
            raise forms.ValidationError('Third column in header should be Image URL.')

        for n, field in enumerate(column_names):
            # We accept "(optional)" in the names of optional columns.
            # That's how those columns are presented in our csv template (that user can download)
            # If the user downloads the template, fills it in and uploades, it immediately works.
            field = re.sub("_*\(optional\)", "", field)
            field = EXPRESSIVE_FIELD_NAME_MAPPING.get(field, field)
            if n >= 3 and field not in OPTIONAL_CSV_FIELDS and field not in IGNORED_CSV_FIELDS:
                raise forms.ValidationError('Unrecognized column name "{0}".'.format(header[n]))
            column_names[n] = field

        # Make sure each column_name appears only once
        for column_name, count in Counter(column_names).iteritems():
            expr_column_name = INVERSE_EXPRESSIVE_FIELD_NAME_MAPPING.get(column_name, column_name)
            formatted_name = expr_column_name.replace('_', ' ').capitalize()
            if count > 1:
                raise forms.ValidationError(
                    "Column \"{0}\" appears multiple times ({1}) in the CSV file.".format(formatted_name, count))

        return column_names

    def _get_csv_content_ad_data(self, reader):
        next(reader)  # ignore header

        count_rows = 0
        data = []
        for row in reader:
            # unicodecsv stores values of all unneeded columns
            # under key None. This can be removed.
            if None in row:
                del row[None]

            if all(row[example_key] == example_value for example_key, example_value in EXAMPLE_CSV_CONTENT.iteritems()):
                continue

            count_rows += 1

            # Remove ignored fields from row dict
            for ignored_field in IGNORED_CSV_FIELDS:
                row.pop(ignored_field, None)

            data.append(row)

        if count_rows == 0:
            raise forms.ValidationError('Uploaded file is empty.')

        return data

    def is_valid_input_file(self, content):
        # detect file content type
        m = magic.Magic(mime=True)
        mime = m.from_buffer(content[:1024])
        if 'text' in mime:  # accept variants of text/plain, text/html, etc.
            return True
        else:
            return False

    def clean_candidates(self):
        candidates_file = self.cleaned_data['candidates']

        file_content = candidates_file.read()
        valid = self.is_valid_input_file(file_content)
        if not valid:
            raise forms.ValidationError('Input file was not recognized.')

        # If the file contains ctrl-M chars instead of
        # new line breaks, DictReader will fail to parse it.
        # Therefore we split the file by lines first and
        # pass that to DictReader. If this proves to be too
        # slow, we can instead save the file to a temporary
        # location on upload and then open it with 'rU'
        # (universal-newline mode).
        # Additionally remove empty lines and Example CSV content if present.
        lines = [line for line in file_content.splitlines() if line]

        encodings = ['utf-8', 'windows-1252']
        data = None

        # try all supported encodings one by one
        for encoding in encodings:
            try:
                header = self._get_csv_header(lines)
                # we save self.csv_column_names to be used by form-wide clean()
                self.csv_column_names = self._get_csv_column_names(header)

                reader = unicodecsv.DictReader(lines, self.csv_column_names, encoding=encoding)
                data = self._get_csv_content_ad_data(reader)
                break
            except unicodecsv.Error:
                raise forms.ValidationError('Uploaded file is not a valid CSV file.')
            except UnicodeDecodeError:
                pass

        if data is None:
            raise forms.ValidationError('Unknown file encoding.')

        if len(data) > MAX_ADS_PER_UPLOAD:
            raise forms.ValidationError('Too many content ads (max. {})'.format(MAX_ADS_PER_UPLOAD))

        return data


class CreditLineItemForm(forms.ModelForm):

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if not self.instance.pk or start_date != self.instance.start_date:
            today = dates_helper.local_today()
            if start_date < today:
                raise forms.ValidationError('Start date has to be in the future.')
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data['end_date']
        today = dates_helper.local_today()
        if end_date < today:
            raise forms.ValidationError('End date has to be greater or equal to today.')
        return end_date

    def save(self, commit=True, request=None, action_type=None):
        m = super(CreditLineItemForm, self).save(commit=False)
        if commit:
            m.save(request=request, action_type=action_type)
        return m

    class Meta:
        model = models.CreditLineItem
        fields = [
            'account', 'agency', 'start_date', 'end_date', 'amount', 'license_fee', 'status', 'comment'
        ]


class BudgetLineItemForm(forms.ModelForm):
    credit = forms.ModelChoiceField(queryset=models.CreditLineItem.objects.all())
    margin = forms.DecimalField(
        decimal_places=4,
        max_digits=5,
        required=False,
    )

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if not self.instance.pk or start_date != self.instance.start_date:
            today = dates_helper.local_today()
            if start_date < today:
                raise forms.ValidationError('Start date has to be in the future.')
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data['end_date']
        if not self.instance.pk:
            today = dates_helper.local_today()
            if end_date < today:
                raise forms.ValidationError('End date has to be in the future.')
        return end_date

    def save(self, commit=True, request=None, action_type=None):
        m = super(BudgetLineItemForm, self).save(commit=False)
        if commit:
            m.save(request=request, action_type=action_type)
        return m

    class Meta:
        model = models.BudgetLineItem
        fields = [
            'campaign', 'credit', 'start_date', 'end_date',
            'amount', 'comment', 'margin'
        ]


class MultiEmailField(forms.Field):

    def to_python(self, value):
        if not value:
            return []
        value = "".join(value.split())
        return value.split(',')

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
                ', '.join(invalid_addresses) +
                (' is' if len(invalid_addresses) == 1 else ' are') +
                ' not valid email address' +
                ('es' if len(invalid_addresses) > 1 else '') +
                '.')


class ScheduleReportForm(forms.Form):
    granularity = forms.TypedChoiceField(
        required=True,
        choices=constants.ScheduledReportGranularity.get_choices(),
        coerce=int
    )
    report_name = forms.CharField(
        required=True,
        max_length=100,
        error_messages={
            'max_length': 'Report name is too long (%(show_value)d/%(limit_value)d).'
        }
    )
    frequency = forms.TypedChoiceField(
        required=True,
        choices=constants.ScheduledReportSendingFrequency.get_choices(),
        coerce=int
    )
    day_of_week = forms.TypedChoiceField(
        required=True,
        choices=constants.ScheduledReportTimePeriod.get_choices(),
        coerce=int
    )
    time_period = forms.TypedChoiceField(
        required=True,
        choices=constants.ScheduledReportTimePeriod.get_choices(),
        coerce=int
    )
    recipient_emails = MultiEmailField(
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(ScheduleReportForm, self).__init__(*args, **kwargs)


class PublisherBlacklistForm(forms.ModelForm):

    def save(self, commit=True):
        instance = super(PublisherBlacklistForm, self).save(commit=False)

        instance.status = constants.PublisherStatus.BLACKLISTED
        instance.everywhere = True

        self._reenable_global(instance.name)

        if commit:
            instance.save()
        return instance

    def _reenable_global(self, name):
        global_blacklist = []
        # currently only support enabling global blacklist
        matching_sources = models.Source.objects.filter(
            deprecated=False
        )
        candidate_source = None
        for source in matching_sources:
            if source.can_modify_publisher_blacklist_automatically():
                candidate_source = source
                break

        global_blacklist.append({
            'domain': name,
            'source': candidate_source,
        })

        actionlogs_to_send = []
        with transaction.atomic():
            actionlogs_to_send.extend(
                api.create_global_publisher_blacklist_actions(
                    None,
                    self.request,
                    constants.PublisherStatus.BLACKLISTED,
                    global_blacklist,
                    send=False
                )
            )
        actionlog.zwei_actions.send(actionlogs_to_send)

    class Meta:
        model = models.PublisherBlacklist
        exclude = ['everywhere', 'account', 'campaign', 'ad_group', 'source', 'status']


class CreditLineItemAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CreditLineItemAdminForm, self).__init__(*args, **kwargs)
        # archived state is stored in settings, we need to have a more stupid query
        not_archived = [
            a.pk for a in models.Account.objects.all() if not a.is_archived()
        ]
        # workaround to not change model __unicode__ methods
        self.fields['account'].label_from_instance = lambda obj: u'{} - {}'.format(obj.id, obj.name)
        self.fields['account'].queryset = models.Account.objects.filter(
            pk__in=not_archived
        ).order_by('id')

        self.fields['agency'].label_from_instance = lambda obj: u'{} - {}'.format(obj.id, obj.name)
        self.fields['agency'].queryset = models.Agency.objects.all().order_by('id')

    class Meta:
        model = models.CreditLineItem
        fields = ['account', 'agency', 'start_date', 'end_date', 'amount',
                  'flat_fee_cc', 'flat_fee_start_date', 'flat_fee_end_date',
                  'license_fee', 'status', 'comment']


class BudgetLineItemAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(BudgetLineItemAdminForm, self).__init__(*args, **kwargs)
        # archived state is stored in settings, we need to have a more stupid query
        not_archived = set([
            c.id for c in models.Campaign.objects.all() if not c.is_archived()
        ])
        if self.instance and self.instance.campaign_id:
            not_archived.add(self.instance.campaign_id)

        # workaround to not change model __unicode__ methods

        self.fields['campaign'].label_from_instance = lambda obj: u'{} - {}'.format(obj.id, obj.name)
        self.fields['campaign'].queryset = models.Campaign.objects.filter(
            pk__in=not_archived
        ).order_by('id')

        self.fields['credit'].queryset = models.CreditLineItem.objects.filter(
            status=constants.CreditLineItemStatus.SIGNED
        ).order_by('account_id')

    class Meta:
        model = models.BudgetLineItem
        fields = ['campaign', 'credit', 'start_date', 'end_date', 'amount', 'comment']


class BreakdownForm(forms.Form):

    def __init__(self, user, breakdown, request_body, *args, **kwargs):
        request_body['breakdown'] = breakdown
        self.user = user

        super(BreakdownForm, self).__init__(request_body, *args, **kwargs)

    start_date = forms.DateField(
        error_messages={
            'required': 'Please provide start date.',
        }
    )

    end_date = forms.DateField(
        error_messages={
            'required': 'Please provide end date.',
        }
    )

    show_archived = forms.BooleanField(required=False)
    show_blacklisted_publishers = forms.TypedChoiceField(
            required=False,
            choices=constants.PublisherBlacklistFilter.get_choices(),
            coerce=str,
            empty_value=None
    )

    offset = forms.IntegerField(min_value=0, required=True)
    limit = forms.IntegerField(min_value=0, max_value=100, required=True)

    parents = TypedMultipleAnyChoiceField(
        required=False,
        coerce=str,
    )

    filtered_sources = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_agencies = TypedMultipleAnyChoiceField(required=False, coerce=str)
    filtered_account_types = TypedMultipleAnyChoiceField(required=False, coerce=str)

    order = forms.CharField(required=False)

    breakdown = forms.CharField(required=True)

    def clean_filtered_sources(self):
        return helpers.get_filtered_sources(self.user, ','.join(self.cleaned_data.get('filtered_sources')))

    def clean_filtered_agencies(self):
        return helpers.get_filtered_agencies(self.cleaned_data.get('filtered_agencies'))

    def clean_filtered_account_types(self):
        return helpers.get_filtered_account_types(self.cleaned_data.get('filtered_account_types'))

    def clean_breakdown(self):
        return [stats.constants.get_dimension_identifier(x) for x in self.cleaned_data['breakdown'].split('/') if x]


class ContentAdCandidateForm(forms.ModelForm):

    def clean_image_crop(self):
        image_crop = self.cleaned_data.get('image_crop')
        if not image_crop:
            return constants.ImageCrop.CENTER

        return image_crop.lower()

    def clean_call_to_action(self):
        call_to_action = self.cleaned_data.get('call_to_action')
        if not call_to_action:
            return DEFAULT_CALL_TO_ACTION

        return call_to_action

    class Meta:
        model = models.ContentAdCandidate
        fields = [
            'label',
            'url',
            'title',
            'image_url',
            'image_crop',
            'display_url',
            'brand_name',
            'description',
            'call_to_action',
            'primary_tracker_url',
            'secondary_tracker_url',
        ]


class ContentAdForm(ContentAdCandidateForm):
    label = forms.CharField(
        max_length=100,
        required=False,
        error_messages={
            'max_length': 'Label too long (max %(limit_value)d characters)',
        }
    )
    url = forms.CharField(
        max_length=936,
        error_messages={
            'required': 'Missing URL',
            'max_length': 'URL too long (max %(limit_value)d characters)',
        }
    )
    title = forms.CharField(
        max_length=90,
        error_messages={
            'required': 'Missing title',
            'max_length': 'Title too long (max %(limit_value)d characters)',
        },
    )
    image_url = forms.CharField(
        error_messages={
            'required': 'Missing image URL',
        }
    )
    image_crop = forms.ChoiceField(
        choices=constants.ImageCrop.get_choices(),
        error_messages={
            'invalid_choice': 'Choose a valid image crop',
            'required': 'Choose a valid image crop',
        },
    )
    display_url = DisplayURLField(
        error_messages={
            'required': 'Missing display URL',
            'max_length': 'Display URL too long (max %(limit_value)d characters)',
        },
    )
    brand_name = forms.CharField(
        max_length=25,
        error_messages={
            'required': 'Missing brand name',
            'max_length': 'Brand name too long (max %(limit_value)d characters)',
        },
    )
    description = forms.CharField(
        max_length=140,
        error_messages={
            'required': 'Missing description',
            'max_length': 'Description too long (max %(limit_value)d characters)',
        },
    )
    call_to_action = forms.CharField(
        max_length=25,
        error_messages={
            'required': 'Missing call to action',
            'max_length': 'Call to action too long (max %(limit_value)d characters)',
        },
    )
    primary_tracker_url = forms.CharField(
        max_length=936,
        required=False,
        error_messages={
            'max_length': 'URL too long (max %(limit_value)d characters)',
        }
    )
    secondary_tracker_url = forms.CharField(
        max_length=936,
        required=False,
        error_messages={
            'max_length': 'URL too long (max %(limit_value)d characters)',
        }
    )

    image_id = forms.CharField(
        required=False,
    )
    image_hash = forms.CharField(
        required=False,
    )
    image_width = forms.IntegerField(
        required=False,
    )
    image_height = forms.IntegerField(
        required=False,
    )

    image_status = forms.IntegerField(
        required=False,
    )
    url_status = forms.IntegerField(
        required=False,
    )

    MIN_IMAGE_SIZE = 300
    MAX_IMAGE_SIZE = 10000

    def _validate_url(self, url):
        validate_url = validators.URLValidator(schemes=['http', 'https'])
        try:
            validate_url(url)
            return url
        except forms.ValidationError:
            pass

        url = u'http://{}'.format(url)
        validate_url(url)

        return url

    def _validate_tracker_url(self, url):
        validate_url = validators.URLValidator(schemes=['https'])
        if url.lower().startswith('http://'):
            raise forms.ValidationError('Impression tracker URLs have to be HTTPS')
        try:
            # URL is considered invalid if it contains any unicode chars
            url = url.encode('ascii')
            validate_url(url)
        except (forms.ValidationError, UnicodeEncodeError):
            raise forms.ValidationError('Invalid impression tracker URLs')
        return url

    def clean_url(self):
        url = self.cleaned_data.get('url').strip()
        try:
            return self._validate_url(url)
        except forms.ValidationError:
            raise forms.ValidationError('Invalid URL')

    def clean_image_url(self):
        image_url = self.cleaned_data.get('image_url').strip()
        try:
            return self._validate_url(image_url)
        except forms.ValidationError:
            raise forms.ValidationError('Invalid image URL')

    def clean_primary_tracker_url(self):
        url = self.cleaned_data.get('primary_tracker_url').strip()
        if not url:
            return

        return self._validate_tracker_url(url)

    def clean_secondary_tracker_url(self):
        url = self.cleaned_data.get('secondary_tracker_url').strip()
        if not url:
            return

        return self._validate_tracker_url(url)

    def clean_image_crop(self):
        image_crop = self.cleaned_data.get('image_crop')
        if not image_crop:
            return constants.ImageCrop.CENTER

        if image_crop.lower() in constants.ImageCrop.get_all():
            return image_crop.lower()

        raise forms.ValidationError('Image crop {} is not supported'.format(image_crop))

    def _get_image_error_msg(self, cleaned_data):
        image_status = cleaned_data['image_status']
        if image_status != constants.AsyncUploadJobStatus.OK or\
           not cleaned_data['image_id'] or\
           not cleaned_data['image_hash'] or\
           not cleaned_data['image_width'] or\
           not cleaned_data['image_height']:
            return 'Image could not be processed'

        if cleaned_data['image_width'] < self.MIN_IMAGE_SIZE or cleaned_data['image_height'] < self.MIN_IMAGE_SIZE:
            return 'Image too small (minimum size is {min}x{min} px)'.format(min=self.MIN_IMAGE_SIZE)

        if cleaned_data['image_width'] > self.MAX_IMAGE_SIZE or cleaned_data['image_height'] > self.MAX_IMAGE_SIZE:
            return 'Image too big (maximum size is {max}x{max} px)'.format(max=self.MAX_IMAGE_SIZE)

    def _get_url_error_msg(self, cleaned_data):
        url_status = cleaned_data['url_status']
        if url_status != constants.AsyncUploadJobStatus.OK:
            return 'Content unreachable'

    def _set_tracker_urls(self, cleaned_data):
        cleaned_data['tracker_urls'] = []
        primary_tracker_url = cleaned_data.get('primary_tracker_url')
        if primary_tracker_url:
            cleaned_data['tracker_urls'].append(primary_tracker_url)

        secondary_tracker_url = self.cleaned_data.get('secondary_tracker_url')
        if secondary_tracker_url:
            cleaned_data['tracker_urls'].append(secondary_tracker_url)

    def clean(self):
        cleaned_data = super(ContentAdForm, self).clean()
        self._set_tracker_urls(cleaned_data)

        pending_statuses = [constants.AsyncUploadJobStatus.PENDING_START,
                            constants.AsyncUploadJobStatus.WAITING_RESPONSE]
        if cleaned_data['image_status'] in pending_statuses or cleaned_data['url_status'] in pending_statuses:
            self.add_error(None, 'Content ad still processing')
            return cleaned_data

        image_error_msg = self._get_image_error_msg(cleaned_data)
        if 'image_url' in cleaned_data and cleaned_data['image_url'] and image_error_msg:
            self.add_error('image_url', image_error_msg)

        url_error_msg = self._get_url_error_msg(cleaned_data)
        if 'url' in cleaned_data and cleaned_data['url'] and url_error_msg:
            self.add_error('url', url_error_msg)

        return cleaned_data
