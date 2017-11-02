from rest_framework import serializers

import restapi.fields

from . import constants


class ClientSerializer(serializers.Serializer):
    salesforce_account_id = restapi.fields.PlainCharField()
    name = restapi.fields.PlainCharField()
    type = serializers.ChoiceField([constants.CLIENT_TYPE_AGENCY, constants.CLIENT_TYPE_CLIENT_DIRECT])


class CreditLineSerializer(serializers.Serializer):
    salesforce_contract_id = restapi.fields.PlainCharField()
    salesforce_account_id = restapi.fields.PlainCharField()
    z1_account_id = restapi.fields.PlainCharField()
    contract_number = restapi.fields.PlainCharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    description = restapi.fields.PlainCharField()
    special_terms = restapi.fields.PlainCharField(required=False, default='')
    pf_schedule = serializers.ChoiceField(
        [constants.PF_SCHEDULE_FLAT_FEE, constants.PF_SCHEDULE_PCT_FEE, constants.PF_SCHEDULE_UPFRONT])
    amount_at_signing = serializers.DecimalField(max_digits=8, decimal_places=2)

    pct_of_budget = serializers.DecimalField(max_digits=6, decimal_places=4, required=False, default=None)
    calc_variable_fee = serializers.DecimalField(max_digits=12, decimal_places=4, required=False, default=None)

    def validate(self, data):
        if not (data['pct_of_budget'] or data['calc_variable_fee']):
            raise serializers.ValidationError('Fee not provided')
        fee_type = data['pf_schedule']
        if fee_type == constants.PF_SCHEDULE_PCT_FEE and not data['pct_of_budget']:
            raise serializers.ValidationError({
                'pct_of_budget': 'Field required when pf_schedule is {}'.format(fee_type)
            })
        if fee_type in (constants.PF_SCHEDULE_FLAT_FEE, constants.PF_SCHEDULE_UPFRONT) and not data['calc_variable_fee']:
            raise serializers.ValidationError({
                'calc_variable_fee': 'Field required when pf_schedule is {}'.format(fee_type)
            })
        return data


class AgencyAccountsSerializer(serializers.Serializer):
    z1_account_id = restapi.fields.PlainCharField()

    def validate_z1_account_id(self, value):
        if value[0] != constants.ACCOUNT_ID_PREFIX_AGENCY:
            raise serializers.ValidationError('An agency account must be provided.')
        return value
