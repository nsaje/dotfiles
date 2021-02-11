from rest_framework import serializers

import core.models
import serviceapi.common.serializers
from zemauth.models import User as zemUser

from . import exceptions as exc


class AgencySerializer(serializers.ModelSerializer):
    tags = serviceapi.common.serializers.TagSerializer(source="entity_tags", many=True, required=False)
    custom_attributes = serializers.JSONField(required=False)  # Without this GET would serialize it as a string
    modified_dt = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    is_externally_managed = serializers.BooleanField(read_only=True)
    amplify_review = serializers.BooleanField(read_only=True)

    class Meta:
        model = core.models.Agency
        fields = core.models.Agency._externally_managed_fields + ("tags", "is_externally_managed", "amplify_review")

    def validate_name(self, value):
        agency = core.models.Agency.objects.filter(name=value).first()
        if agency:
            raise exc.ValidationError("Agency with same name already exists.")
        return value


class AccountSerializer(serializers.ModelSerializer):
    agency_id = serializers.PrimaryKeyRelatedField(
        required=False, source="agency", queryset=core.models.Agency.objects.all()
    )
    sales_representative = serializers.EmailField(required=True, source="settings.default_sales_representative")
    account_manager = serializers.EmailField(required=False, source="settings.default_account_manager")
    tags = serviceapi.common.serializers.TagSerializer(source="entity_tags", many=True, required=False)
    custom_attributes = serializers.JSONField(required=False)
    is_archived = serializers.BooleanField(read_only=True)
    modified_dt = serializers.DateTimeField(format="%d-%m-%Y", read_only=True)
    is_externally_managed = serializers.BooleanField(read_only=True)
    external_marketer_id = serializers.CharField(required=False, max_length=255, source="outbrain_marketer_id")
    internal_marketer_id = serializers.CharField(required=False, max_length=255, source="outbrain_internal_marketer_id")
    amplify_review = serializers.BooleanField(read_only=True)

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
            "external_marketer_id",
            "internal_marketer_id",
            "amplify_review",
        )

    def validate_agency_id(self, value):
        agency = core.models.Agency.objects.filter(id=value.id, is_externally_managed=True).first()
        if not agency:
            raise exc.AgencyNotExternallyManaged("Agency provided does not exists or is not externally manageable.")
        if agency.is_disabled:
            raise exc.CreatingAccountOnDisabledAgency("Creating account on a disabled agency is not allowed.")
        return agency

    def validate_sales_representative(self, value):
        sales_rep = zemUser.objects.filter(email__iexact=value, is_externally_managed=True).first()
        if not sales_rep:
            raise exc.SalesRepresentativeNotFound("Sales representative e-mail not found.")
        return sales_rep

    def validate_account_manager(self, value):
        account_manager = zemUser.objects.filter(email__iexact=value, is_externally_managed=True).first()
        if not account_manager:
            raise exc.SalesRepresentativeNotFound("Account manager e-mail not found.")
        return account_manager


class DateRangeSerializer(serializers.Serializer):
    modified_dt_start = serializers.DateField(input_formats=["%d-%m-%Y"], format="%d-%m-%Y", required=False)
    modified_dt_end = serializers.DateField(input_formats=["%d-%m-%Y"], format="%d-%m-%Y", required=False)
    created_dt_start = serializers.DateField(input_formats=["%d-%m-%Y"], format="%d-%m-%Y", required=False)
    created_dt_end = serializers.DateField(input_formats=["%d-%m-%Y"], format="%d-%m-%Y", required=False)


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    sales_office = serializers.CharField(required=True)
    is_active = serializers.BooleanField(required=False)
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = zemUser
        fields = ("id", "email", "first_name", "last_name", "sales_office", "is_active", "date_joined")

    def validate_email(self, email):
        user_id = self.context.get("user_id")
        user = zemUser.objects.filter(email__iexact=email).first()
        if user and user.id != user_id:
            raise exc.UserAlreadyExists("User with this email already exists.")
        return email


class UserQueryParams(serializers.Serializer):
    email = serializers.EmailField(required=False)
