from rest_framework import serializers

import restapi.serializers.fields


class TargetingIncludeExcludeSerializer(serializers.Serializer):
    included = serializers.ListField(child=serializers.IntegerField(), source='whitelist_publisher_groups')
    excluded = serializers.ListField(child=serializers.IntegerField(), source='blacklist_publisher_groups')


class AccountTargetingSerializer(serializers.Serializer):
    publisher_groups = TargetingIncludeExcludeSerializer(source='*')


class AccountSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    agency_id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    targeting = AccountTargetingSerializer(source='settings', required=False)
    name = restapi.serializers.fields.PlainCharField(
        max_length=127,
        error_messages={'required': 'Please specify account name.'},
        source='settings.name',
    )
