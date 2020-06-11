import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers


class UserQueryParamsExpectations(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(default=None)
    account_id = restapi.serializers.fields.IdField(default=None)
    show_internal = rest_framework.serializers.NullBooleanField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)


class EntityPermissionsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    agency_id = rest_framework.serializers.CharField(required=False)
    account_id = rest_framework.serializers.CharField(required=False)
    account_name = rest_framework.serializers.CharField(source="account.name", required=False)
    permission = rest_framework.serializers.CharField()


class UserSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    email = rest_framework.serializers.EmailField()
    first_name = rest_framework.serializers.CharField(required=False)
    last_name = rest_framework.serializers.CharField(required=False)
    entity_permissions = EntityPermissionsSerializer(many=True)


class CreateUserSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    users = UserSerializer(many=True, allow_empty=False)
