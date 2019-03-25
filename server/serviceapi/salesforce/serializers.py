import decimal

from rest_framework import serializers

import dash.constants
import restapi.serializers.base
import restapi.serializers.fields

from . import constants


class ClientSerializer(serializers.Serializer):
    salesforce_account_id = restapi.serializers.fields.PlainCharField()
    name = restapi.serializers.fields.PlainCharField()
    type = serializers.ChoiceField([constants.CLIENT_TYPE_AGENCY, constants.CLIENT_TYPE_CLIENT_DIRECT])
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, required=False, default=dash.constants.Currency.USD
    )
    tags = restapi.serializers.fields.NullListField(required=False)


class CreditLineSerializer(serializers.Serializer):
    salesforce_contract_id = restapi.serializers.fields.PlainCharField()
    salesforce_account_id = restapi.serializers.fields.PlainCharField()
    z1_account_id = restapi.serializers.fields.PlainCharField()
    contract_number = restapi.serializers.fields.PlainCharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    description = restapi.serializers.fields.PlainCharField()
    special_terms = restapi.serializers.fields.PlainCharField(required=False, default="")
    pf_schedule = serializers.ChoiceField(
        [constants.PF_SCHEDULE_FLAT_FEE, constants.PF_SCHEDULE_PCT_FEE, constants.PF_SCHEDULE_UPFRONT]
    )
    amount_at_signing = serializers.DecimalField(max_digits=8, decimal_places=2, rounding=decimal.ROUND_HALF_DOWN)

    pct_of_budget = serializers.DecimalField(
        max_digits=6, decimal_places=4, required=False, default=None, rounding=decimal.ROUND_HALF_DOWN
    )
    calc_variable_fee = serializers.DecimalField(
        max_digits=12, decimal_places=4, required=False, default=None, rounding=decimal.ROUND_HALF_DOWN
    )

    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, required=False, default=dash.constants.Currency.USD
    )

    def validate(self, data):
        if not (data["pct_of_budget"] or data["calc_variable_fee"]):
            raise serializers.ValidationError("Fee not provided")
        fee_type = data["pf_schedule"]
        if fee_type == constants.PF_SCHEDULE_PCT_FEE and not data["pct_of_budget"]:
            raise serializers.ValidationError(
                {"pct_of_budget": "Field required when pf_schedule is {}".format(fee_type)}
            )
        if (
            fee_type in (constants.PF_SCHEDULE_FLAT_FEE, constants.PF_SCHEDULE_UPFRONT)
            and not data["calc_variable_fee"]
        ):
            raise serializers.ValidationError(
                {"calc_variable_fee": "Field required when pf_schedule is {}".format(fee_type)}
            )
        return data


class AgencyAccountsSerializer(serializers.Serializer):
    z1_account_id = restapi.serializers.fields.PlainCharField()

    def validate_z1_account_id(self, value):
        if value[0] != constants.ACCOUNT_ID_PREFIX_AGENCY:
            raise serializers.ValidationError("An agency account must be provided.")
        return value


class Z1IdSerializer(serializers.Serializer):
    z1_account_id = restapi.serializers.fields.PlainCharField()


class CreditsListSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    z1_cli_id = serializers.IntegerField(source="pk")
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    amount = serializers.IntegerField()
    license_fee = restapi.serializers.fields.BlankDecimalField(
        max_digits=5, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
    flat_fee_cc = serializers.IntegerField()
    flat_fee_start_date = restapi.serializers.fields.BlankDateField()
    flat_fee_end_date = restapi.serializers.fields.BlankDateField()
    contract_id = restapi.serializers.fields.NullPlainCharField()
    contract_number = restapi.serializers.fields.PlainCharField()
    status = restapi.serializers.fields.DashConstantField(
        dash.constants.CreditLineItemStatus  # , default=dash.constants.CreditLineItemStatus.PENDING
    )
    refund = serializers.BooleanField()
    comment = restapi.serializers.fields.PlainCharField()
    special_terms = restapi.serializers.fields.PlainCharField()
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, default=dash.constants.Currency.USD
    )
    created_dt = serializers.DateTimeField()
    modified_dt = serializers.DateTimeField()
    created_by = serializers.EmailField()
