# -*- coding: utf-8 -*-
import re
import unicodecsv
import json

import dateutil.parser
import rfc3987
from decimal import Decimal

import utils.string

from django import forms
from django.core.validators import URLValidator

from dash import constants
from zemauth.models import User as ZemUser


class BaseApiForm(forms.Form):
    def get_errors():
        pass


class AdvancedDateTimeField(forms.fields.DateTimeField):
    def strptime(self, value, format):
        return dateutil.parser.parse(value)


class AdGroupSettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify ad group name.'}
    )
    state = forms.TypedChoiceField(
        choices=constants.AdGroupSettingsState.get_choices(),
        coerce=int,
        empty_value=None
    )
    start_date = forms.DateField(
        error_messages={
            'required': 'Please provide start date.',
        }
    )
    end_date = forms.DateField(required=False)
    cpc_cc = forms.DecimalField(
        min_value=0.03,
        max_value=2,
        decimal_places=4,
        error_messages={
            'required': 'Minimum CPC is $0.03.',
            'min_value': 'Minimum CPC is $0.03.',
            'max_value': 'Maximum CPC is $2.00.'
        }
    )
    daily_budget_cc = forms.DecimalField(
        min_value=10,
        decimal_places=4,
        error_messages={
            'required': 'Please provide budget of at least $10.00.',
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
        choices=constants.AdTargetCountry.get_choices()
    )
    tracking_code = forms.CharField(required=False)
    display_url = forms.URLField(
        max_length=25,
        required=False
    )
    brand_name = forms.CharField(
        max_length=25,
        required=False
    )
    description = forms.CharField(
        max_length=100,
        required=False
    )
    call_to_action = forms.CharField(
        max_length=25,
        required=False
    )

    def __init__(self, current_settings, *args, **kwargs):
        self.current_settings = current_settings

        super(AdGroupSettingsForm, self).__init__(*args, **kwargs)

    def clean_display_url(self):
        return self.data['display_url']

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')

        # maticz: We deal with UTC dates even if a not-UTC date date was submitted from
        # user.
        # Product guys confirmed it.
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('End date must not occur before start date.')

        return end_date


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
        if cpc_cc < 0:
            raise forms.ValidationError('This value must be positive')

        decimal_places = self.ad_group_source.source.source_type.cpc_decimal_places
        if decimal_places is not None and self._has_too_many_decimal_places(cpc_cc, decimal_places):
            raise forms.ValidationError(
                'CPC on {} cannot exceed {} decimal place{}.'.format(
                    self.ad_group_source.source.name, decimal_places, 's' if decimal_places != 1 else ''))

        min_cpc = self.ad_group_source.source.source_type.min_cpc
        if min_cpc is not None and cpc_cc < min_cpc:
            raise forms.ValidationError(
                'Minimum CPC is ${}.'.format(utils.string.format_decimal(min_cpc, 2, 3)))

        max_cpc = self.ad_group_source.source.source_type.max_cpc
        if max_cpc is not None and cpc_cc > max_cpc:
            raise forms.ValidationError(
                'Maximum CPC is ${}.'.format(utils.string.format_decimal(max_cpc, 2, 3)))

    def _has_too_many_decimal_places(self, num, decimal_places):
        rounded_num = num.quantize(Decimal('1.{}'.format('0' * decimal_places)))
        return rounded_num != num


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
        if daily_budget_cc < 0:
            raise forms.ValidationError('This value must be positive')

        min_daily_budget = self.ad_group_source.source.source_type.min_daily_budget
        if min_daily_budget is not None and daily_budget_cc < min_daily_budget:
            raise forms.ValidationError('Please provide budget of at least ${}.' \
                .format(utils.string.format_decimal(min_daily_budget, 0, 0)))

        max_daily_budget = self.ad_group_source.source.source_type.max_daily_budget
        if max_daily_budget is not None and daily_budget_cc > max_daily_budget:
            raise forms.ValidationError('Maximum allowed budget is ${}. If you want use a higher daily budget, please contact support.' \
                .format(utils.string.format_decimal(max_daily_budget, 0, 0)))


class AdGroupSourceSettingsStateForm(forms.Form):
    state = forms.TypedChoiceField(
        choices=constants.AdGroupSettingsState.get_choices(),
        coerce=int,
        empty_value=None
    )


class AdGroupAgencySettingsForm(forms.Form):
    id = forms.IntegerField()
    tracking_code = forms.CharField(required=False)

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


class AccountAgencySettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify account name.'}
    )


class CampaignSettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'}
    )
    account_manager = forms.IntegerField()
    sales_representative = forms.IntegerField(
        required=False
    )
    service_fee = forms.DecimalField(
        min_value=0,
        max_value=100,
        decimal_places=2,
    )
    iab_category = forms.ChoiceField(
        choices=constants.IABCategory.get_choices(),
    )
    promotion_goal = forms.TypedChoiceField(
        choices=constants.PromotionGoal.get_choices(),
        coerce=int,
        empty_value=None
    )

    def clean_account_manager(self):
        account_manager_id = self.cleaned_data.get('account_manager')

        err_msg = 'Invalid account manager.'

        try:
            account_manager = ZemUser.objects.\
                get_users_with_perm('campaign_settings_account_manager', True).\
                get(pk=account_manager_id)
        except ZemUser.DoesNotExist:
            raise forms.ValidationError(err_msg)

        return account_manager

    def clean_sales_representative(self):
        sales_representative_id = self.cleaned_data.get('sales_representative')

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


class CampaignBudgetForm(forms.Form):
    amount = forms.DecimalField(decimal_places=4)
    action = forms.CharField(max_length=8)

    def clean_amount(self):
        x = self.cleaned_data.get('amount')
        return float(x)

    def get_allocate_amount(self):
        x = self.cleaned_data['amount']
        a = self.cleaned_data.get('action')
        if a == 'allocate':
            return float(x)
        else:
            return 0

    def get_revoke_amount(self):
        x = self.cleaned_data['amount']
        a = self.cleaned_data.get('action')
        if a == 'revoke':
            return float(x)
        else:
            return 0


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


class AdGroupAdsPlusUploadForm(forms.Form):
    content_ads = forms.FileField(
        error_messages={'required': 'Please choose a file to upload.'}
    )
    batch_name = forms.CharField(
        required=True,
        max_length=255,
        error_messages={'required': 'Please enter a name for this upload.'}
    )

    def _validate_crops(self, crop_list):
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    if not isinstance(crop_list[i][j][k], (int, long)):
                        raise ValueError('Coordinate is not an integer')

    def _parse_crop_areas(self, crop_string):
        crop_string = crop_string.replace('(', '[').replace(')', ']')

        try:
            crop_list = json.loads(crop_string)
            self._validate_crops(crop_list)
        except (ValueError, IndexError):
            raise forms.ValidationError('File is not formatted correctly.')

        return crop_list

    def _validate_and_transform_row(self, row):
        url = row.get('url')
        title = row.get('title')
        image_url = row.get('image_url')

        validate_url = URLValidator(
            schemes=['http', 'https'],
            message='File is not formatted correctly'
        )

        validate_url(url)
        validate_url(image_url)

        if title is None or not len(title):
            raise forms.ValidationError('File is not formatted correctly.')

        crop_areas = row.get('crop_areas')
        if crop_areas is not None and len(crop_areas):
            row['crop_areas'] = self._parse_crop_areas(crop_areas)

        return row

    def clean_content_ads(self):
        content_ads = self.cleaned_data['content_ads']

        ads = []
        try:
            reader = unicodecsv.DictReader(content_ads, ['url', 'title', 'image_url', 'crop_areas'])
            next(reader, None)  # ignore header

            for row in reader:
                ads.append(self._validate_and_transform_row(row))
        except unicodecsv.Error:
            raise forms.ValidationError('File is not formatted correctly.')

        return ads
