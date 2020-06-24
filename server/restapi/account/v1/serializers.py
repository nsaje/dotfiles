from rest_framework import serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
from dash import constants


class TargetingIncludeExcludeSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = serializers.ListField(
        child=serializers.IntegerField(), source="whitelist_publisher_groups", required=False
    )
    excluded = serializers.ListField(
        child=serializers.IntegerField(), source="blacklist_publisher_groups", required=False
    )


class AccountTargetingSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    publisher_groups = TargetingIncludeExcludeSerializer(source="*", required=False)


class AccountSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, restapi.serializers.base.RESTAPIBaseSerializer
):
    class Meta:
        permissioned_fields = {
            "frequency_capping": "zemauth.can_set_frequency_capping",
            "default_icon_url": "zemauth.can_use_creative_icon",
        }

    id = restapi.serializers.fields.IdField(read_only=True)
    agency_id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    targeting = AccountTargetingSerializer(source="settings", required=False)
    name = restapi.serializers.fields.PlainCharField(
        max_length=127, error_messages={"required": "Please specify account name."}, source="settings.name"
    )
    archived = serializers.BooleanField(default=False, required=False, source="settings.archived")
    currency = restapi.serializers.fields.DashConstantField(
        constants.Currency, default=constants.Currency.USD, required=False
    )
    frequency_capping = restapi.serializers.fields.BlankIntegerField(
        allow_null=True, required=False, source="settings.frequency_capping"
    )
    default_icon_url = serializers.URLField(required=False, allow_blank=True)

    def to_representation(self, instance):
        self.fields["default_icon_url"] = serializers.SerializerMethodField()
        return super().to_representation(instance)

    def get_default_icon_url(self, account):
        return account.settings.get_base_default_icon_url()
