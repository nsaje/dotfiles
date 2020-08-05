import decimal

from rest_framework import serializers

import core.models
import dash.constants
import restapi.serializers.base
import restapi.serializers.fields
import serviceapi.common.serializers
import zemauth.models

from . import constants


class ClientSerializer(serializers.Serializer):
    salesforce_account_id = restapi.serializers.fields.PlainCharField()
    name = restapi.serializers.fields.PlainCharField()
    type = serializers.ChoiceField([constants.CLIENT_TYPE_AGENCY, constants.CLIENT_TYPE_CLIENT_DIRECT])
    currency = restapi.serializers.fields.DashConstantField(
        dash.constants.Currency, required=False, default=dash.constants.Currency.USD
    )
    tags = restapi.serializers.fields.NullListField(required=False)


class AgencyAccountsSerializer(serializers.Serializer):
    z1_account_id = restapi.serializers.fields.PlainCharField()

    def validate_z1_account_id(self, value):
        if value[0] != constants.ACCOUNT_ID_PREFIX_AGENCY:
            raise serializers.ValidationError("An agency account must be provided.")
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = zemauth.models.User
        fields = ("email",)

    def to_representation(self, instance):
        return instance.email


class AccountSerializer(serializers.ModelSerializer):
    z1_account_id = serializers.CharField(source="get_salesforce_id")
    name = serializers.CharField()

    class Meta:
        model = core.models.Account
        fields = ("name", "z1_account_id")


class AgencySerializer(serializers.ModelSerializer):
    cs_representative = UserSerializer(required=False, read_only=True)
    sales_representative = UserSerializer(required=False, read_only=True)
    default_account_type = serializers.IntegerField(default=constants.DEFAULT_ACCOUNT_TYPE)
    tags = serviceapi.common.serializers.TagSerializer(required=False, many=True, read_only=True, source="entity_tags")
    z1_account_id = serializers.CharField(required=False, read_only=True, source="get_salesforce_id")
    accounts = serializers.SerializerMethodField()

    client_type = serializers.CharField(required=False, write_only=True)
    client_size = serializers.CharField(required=False, write_only=True)
    region = serializers.CharField(required=False, write_only=True)

    class Meta:
        depth = 1
        model = core.models.Agency
        fields = [
            "id",
            "name",
            "default_account_type",
            "tags",
            "cs_representative",
            "sales_representative",
            "z1_account_id",
            "accounts",
            "client_type",
            "client_size",
            "region",
        ]

    def get_accounts(self, instance):
        ordered_accounts = instance.account_set.all().order_by("name")
        return AccountSerializer(ordered_accounts, many=True).data


class CreditLineSerializer(serializers.Serializer):
    salesforce_contract_id = restapi.serializers.fields.PlainCharField()
    salesforce_account_id = restapi.serializers.fields.PlainCharField()
    z1_account_id = restapi.serializers.fields.PlainCharField()
    contract_number = restapi.serializers.fields.PlainCharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    description = restapi.serializers.fields.PlainCharField()
    special_terms = restapi.serializers.fields.PlainCharField(required=False, default="")
    pf_schedule = serializers.ChoiceField([constants.PF_SCHEDULE_PCT_FEE])
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
        return data


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
    contract_id = restapi.serializers.fields.NullPlainCharField()
    contract_number = restapi.serializers.fields.PlainCharField()
    status = restapi.serializers.fields.DashConstantField(
        dash.constants.CreditLineItemStatus, default=dash.constants.CreditLineItemStatus.PENDING
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
