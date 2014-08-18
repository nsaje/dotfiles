import datetime
from decimal import Decimal

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

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']

        # maticz: We deal with UTC dates even if a valid date was submitted from user's
        # point of view but was done in a different timezone (eg. client date is 14.3.2014
        # while on server it is already 15.3.2014). We just validate that this date is
        # a possible date today somewhere in the world.
        # Product guys confirmed it.
        min_date = (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).date()
        if start_date != self.current_settings.start_date and \
                start_date < min_date:
            raise forms.ValidationError("Start date can't be set in past.")

        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')

        # maticz: We deal with UTC dates even if a not-UTC date date was submitted from
        # user.
        # Product guys confirmed it.
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('End date must not occur before start date.')

        return end_date

    def clean_tracking_code(self):
        tracking_code = self.cleaned_data.get('tracking_code')

        err_msg = 'Tracking code structure is not valid.'

        if tracking_code:
            # This is a bit of a hack we're doing here but if we don't prepend 'http:' to
            # the provided tracking code, then rfc3987 doesn't know how to parse it.
            if not tracking_code.startswith('?'):
                tracking_code = '?' + tracking_code

            test_url = 'http:{0}'.format(tracking_code)

            try:
                result = rfc3987.parse(test_url, rule='IRI')
                if '?' + result['query'] != tracking_code:
                    raise forms.ValidationError(err_msg)
            except ValueError:
                raise forms.ValidationError(err_msg)

        return self.cleaned_data.get('tracking_code')


class CampaignSettingsForm(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'}
    )
    account_manager = forms.ModelChoiceField(
        queryset=ZemUser.objects.get_users_with_perm('campaign_settings_account_manager')
    )
    sales_representative = forms.ModelChoiceField(
        queryset=ZemUser.objects.get_users_with_perm('campaign_settings_sales_rep')
    )
    service_fee = forms.TypedChoiceField(
        choices=constants.ServiceFee.get_choices(),
        coerce=Decimal,
        empty_value=None
    )
    iab_category = forms.TypedChoiceField(
        choices=constants.IABCategory.get_choices(),
        coerce=int,
        empty_value=None
    )
    promotion_goal = forms.TypedChoiceField(
        choices=constants.PromotionGoal.get_choices(),
        coerce=int,
        empty_value=None
    )
