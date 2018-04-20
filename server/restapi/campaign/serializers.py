import rest_framework.serializers

import restapi.fields
import restapi.serializers
import restapi.serializers.base

from dash import constants


class GATrackingSerializer(rest_framework.serializers.Serializer):
    enabled = rest_framework.serializers.NullBooleanField(
        source='enable_ga_tracking',
        required=False,
    )
    type = restapi.fields.DashConstantField(
        constants.GATrackingType,
        source='ga_tracking_type',
        required=False,
    )
    web_property_id = rest_framework.serializers.RegexField(
        constants.GA_PROPERTY_ID_REGEX,
        source='ga_property_id',
        required=False,
        max_length=25,
        allow_blank=True,
        error_messages={'web_property_id': 'Web property ID is not valid.'},
    )


class AdobeTrackingSerializer(rest_framework.serializers.Serializer):
    enabled = rest_framework.serializers.NullBooleanField(
        source='enable_adobe_tracking',
        required=False,
    )
    tracking_parameter = restapi.fields.PlainCharField(
        source='adobe_tracking_param',
        required=False,
        max_length=10,
        allow_blank=True,
    )


class CampaignTrackingSerializer(rest_framework.serializers.Serializer):
    ga = GATrackingSerializer(source='*', required=False)
    adobe = AdobeTrackingSerializer(source='*', required=False)


class PublisherGroupsSerializer(rest_framework.serializers.Serializer):
    included = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        source='whitelist_publisher_groups',
        required=False,
    )
    excluded = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        source='blacklist_publisher_groups',
        required=False,
    )


class CampaignTargetingSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    devices = restapi.serializers.targeting.DevicesSerializer(
        source='target_devices',
        required=False,
    )
    placements = restapi.serializers.targeting.PlacementsSerializer(
        source='target_placements',
        required=False,
    )
    os = restapi.serializers.targeting.OSsSerializer(
        source='target_os',
        required=False,
    )
    publisher_groups = PublisherGroupsSerializer(source='*', required=False)


class CampaignSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.fields.IdField(read_only=True, source='campaign.id')
    account_id = restapi.fields.IdField(source='campaign.account_id')
    name = restapi.fields.PlainCharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'},
    )
    iab_category = restapi.fields.DashConstantField(
        constants.IABCategory,
        required=False,
    )
    language = restapi.fields.DashConstantField(
        constants.Language,
        required=False,
    )
    archived = rest_framework.serializers.BooleanField(required=False)
    tracking = CampaignTrackingSerializer(source='*', required=False)
    targeting = CampaignTargetingSerializer(source='*', required=False)

    def validate_iab_category(self, value):
        if value != constants.IABCategory.IAB24 and '-' not in value:
            raise rest_framework.serializers.ValidationError(
                'Tier 1 IAB categories not allowed, please use Tier 2 IAB categories.'
            )
        return value
