from rest_framework import serializers

import restapi.serializers.fields
from dash import constants


class TargetingIncludeExcludeSerializer(serializers.Serializer):
    included = serializers.ListField(child=serializers.IntegerField(), source="whitelist_publisher_groups")
    excluded = serializers.ListField(child=serializers.IntegerField(), source="blacklist_publisher_groups")


class AccountTargetingSerializer(serializers.Serializer):
    publisher_groups = TargetingIncludeExcludeSerializer(source="*")


class AccountSerializer(restapi.serializers.serializers.PermissionedFieldsMixin, serializers.Serializer):
    class Meta:
        permissioned_fields = {"frequency_capping": "zemauth.can_set_frequency_capping"}

    id = restapi.serializers.fields.IdField(read_only=True)
    agency_id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    targeting = AccountTargetingSerializer(source="settings", required=False)
    name = restapi.serializers.fields.PlainCharField(
        max_length=127, error_messages={"required": "Please specify account name."}, source="settings.name"
    )
    currency = restapi.serializers.fields.DashConstantField(
        constants.Currency, default=constants.Currency.USD, required=False
    )
    frequency_capping = serializers.IntegerField(allow_null=True, required=False, source="settings.frequency_capping")
