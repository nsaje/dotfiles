import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import zemauth.access
from utils.exc import ValidationError
from zemauth.features.entity_permission import Permission


class UserQueryParamsExpectations(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(default=None)
    account_id = restapi.serializers.fields.IdField(default=None)
    show_internal = rest_framework.serializers.NullBooleanField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)


class EntityPermissionsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    agency_id = rest_framework.serializers.CharField(required=False, allow_null=True)
    account_id = rest_framework.serializers.CharField(required=False, allow_null=True)
    account_name = rest_framework.serializers.CharField(source="account.name", required=False)
    permission = rest_framework.serializers.CharField()

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        value["agency"] = (
            zemauth.access.get_agency(self.context["request"].user, Permission.USER, value.get("agency_id"))
            if value.get("agency_id")
            else None
        )
        value["account"] = (
            zemauth.access.get_account(self.context["request"].user, Permission.USER, value.get("account_id"))
            if value.get("account_id")
            else None
        )

        return value

    def validate(self, data):
        data = super().validate(data)
        calling_user = self.context["request"].user

        if not calling_user.has_perm_on_all_entities(Permission.USER):
            account_id = data.get("account_id")
            agency_id = data.get("agency_id")

            if account_id is None and agency_id is None:
                raise ValidationError("Either agency id or account id must be provided for each entity permission.")

        return data

    def validate_agency_id(self, agency_id):
        if agency_id is not None:
            request_agency_id = self.context["request"].query_params.get("agency_id")
            if agency_id != request_agency_id:
                raise ValidationError("Incorrect agency ID")

        return agency_id

    def validate_account_id(self, account_id):
        request_agency_id = self.context["request"].query_params.get("agency_id")
        request_account_id = self.context["request"].query_params.get("account_id")
        calling_user = self.context["request"].user

        if request_account_id:
            request_account = zemauth.access.get_account(calling_user, Permission.USER, request_account_id)
        else:
            request_account = None

        if request_account and not request_agency_id:
            request_agency_id = request_account.agency.id

        if account_id is not None and account_id != "":
            permission_account = zemauth.access.get_account(calling_user, Permission.USER, account_id)
            if permission_account.agency is None or int(permission_account.agency.id) != int(request_agency_id):
                raise ValidationError("Account does not belong to the correct agency")

        return account_id


class UserSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    email = rest_framework.serializers.EmailField()
    first_name = rest_framework.serializers.CharField(required=False)
    last_name = rest_framework.serializers.CharField(required=False)
    entity_permissions = EntityPermissionsSerializer(many=True)


class CreateUserSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    users = UserSerializer(many=True, allow_empty=False)
