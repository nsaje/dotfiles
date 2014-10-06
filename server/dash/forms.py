# -*- coding: utf-8 -*-
import re

import dateutil.parser
import rfc3987

from django import forms

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

    def __init__(self, current_settings, *args, **kwargs):
        self.current_settings = current_settings

        super(AdGroupSettingsForm, self).__init__(*args, **kwargs)

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')

        # maticz: We deal with UTC dates even if a not-UTC date date was submitted from
        # user.
        # Product guys confirmed it.
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('End date must not occur before start date.')

        return end_date


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
    allocate = forms.DecimalField(decimal_places=4)
    revoke = forms.DecimalField(decimal_places=4)
    comment = forms.CharField(max_length=256, required=False)

    def clean_allocate(self):
        allocate_amount = self.cleaned_data.get('allocate')
        err_msg = 'Please allocate at least $10'
        if allocate_amount > 0 and allocate_amount < 10:
            raise forms.ValidationError(err_msg)
        return float(allocate_amount)

    def clean_revoke(self):
        revoke_amount = self.cleaned_data.get('revoke')
        err_msg = 'Please revoke at least $10'
        if revoke_amount > 0 and revoke_amount < 10:
            raise forms.ValidationError(err_msg)
        return float(revoke_amount)

