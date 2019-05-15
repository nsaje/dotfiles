import decimal

from rest_framework import serializers

import core.models
import dash.constants
import restapi.serializers.base
import restapi.serializers.fields
from zemauth.models import User as zemUser

from . import constants
from . import exceptions as exc


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


class TagSerializer(serializers.BaseSerializer):
    class Meta:
        model = core.models.EntityTag
        fields = ("name",)

    def to_representation(self, instance):
        return instance.name

    def to_internal_value(self, data):
        return data


class AgencySerializer(serializers.ModelSerializer):
    tags = TagSerializer(source="entity_tags", many=True, required=False)
    custom_attributes = serializers.JSONField(required=False)  # Without this GET would serialize it as a string
    modified_dt = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    is_externally_managed = serializers.BooleanField(read_only=True)

    class Meta:
        model = core.models.Agency
        fields = core.models.Agency._externally_managed_fields + ("tags", "is_externally_managed")

    def validate_name(self, value):
        agency = core.models.Agency.objects.filter(name=value).first()
        if agency:
            raise exc.ValidationError("Agency with same name already exists.")
        return value


class AccountSerializer(serializers.ModelSerializer):
    agency_id = serializers.PrimaryKeyRelatedField(source="agency", queryset=core.models.Agency.objects.all())
    sales_representative = serializers.EmailField(required=False, source="settings.default_sales_representative")
    account_manager = serializers.EmailField(required=False, source="settings.default_account_manager")
    tags = TagSerializer(source="entity_tags", many=True, required=False)
    custom_attributes = serializers.JSONField(required=False)
    is_archived = serializers.BooleanField(read_only=True)
    modified_dt = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    is_externally_managed = serializers.BooleanField(read_only=True)

    class Meta:
        model = core.models.Account
        fields = core.models.Account._externally_managed_fields + (
            "agency_id",
            "sales_representative",
            "account_manager",
            "tags",
            "custom_attributes",
            "is_archived",
            "modified_dt",
            "is_externally_managed",
        )

    def validate_agency_id(self, value):
        agency = core.models.Agency.objects.filter(id=value.id, is_externally_managed=True).first()
        if not agency:
            raise exc.AgencyNotExternallyManaged("Agency provided does not exists or is not externally manageable.")
        if agency.is_disabled:
            raise exc.CreatingAccountOnDisabledAgency("Creating account on a disabled agency is not allowed.")
        return agency

    def validate_sales_representative(self, value):
        sales_rep = zemUser.objects.filter(email=value).first()
        if not sales_rep:
            raise exc.SalesRepresentativeNotFound("Sales representative e-mail not found.")
        return sales_rep

    def validate_account_manager(self, value):
        account_manager = zemUser.objects.filter(email=value).first()
        if not account_manager:
            raise exc.SalesRepresentativeNotFound("Account manager e-mail not found.")
        return account_manager


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(input_formats=["%d-%m-%Y"], format="%d-%m-%Y", required=False)
    end_date = serializers.DateField(input_formats=["%d-%m-%Y"], format="%d-%m-%Y", required=False)
