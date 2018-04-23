import rest_framework.serializers

import restapi.fields
import restapi.serializers
import restapi.serializers.base
import restapi.common.serializers

from dash import constants
import pytz


class AdGroupGeoSerializer(rest_framework.serializers.Serializer):
    included = restapi.serializers.targeting.TargetRegionsSerializer(
        source='target_regions',
        required=False,
    )
    excluded = restapi.serializers.targeting.TargetRegionsSerializer(
        source='exclusion_target_regions',
        required=False
    )


class AdGroupInterestSerializer(rest_framework.serializers.Serializer):
    included = rest_framework.serializers.ListField(
        child=restapi.fields.DashConstantField(constants.InterestCategory),
        source='interest_targeting',
        required=False,
    )
    excluded = rest_framework.serializers.ListField(
        child=restapi.fields.DashConstantField(constants.InterestCategory),
        source='exclusion_interest_targeting',
        required=False
    )


class AdGroupPublisherGroupsSerializer(rest_framework.serializers.Serializer):
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


class AdGroupCustomAudiencesSerializer(rest_framework.serializers.Serializer):
    included = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        source='audience_targeting',
        required=False,
    )
    excluded = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        source='exclusion_audience_targeting',
        required=False,
    )


class AdGroupRetargetingSerializer(rest_framework.serializers.Serializer):
    included = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        source='retargeting_ad_groups',
        required=False,
    )
    excluded = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        source='exclusion_retargeting_ad_groups',
        required=False,
    )


class AdGroupDaypartingSerializer(rest_framework.serializers.Serializer):
    sunday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    monday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    tuesday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    wednesday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    thursday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    friday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    saturday = rest_framework.serializers.ListField(
        child=rest_framework.serializers.IntegerField(),
        required=False,
    )
    timezone = restapi.fields.PlainCharField(required=False, allow_blank=True)

    def validate(self, data):
        for key, value in data.items():
            if key == 'timezone':
                try:
                    pytz.timezone(value)
                except pytz.UnknownTimeZoneError:
                    raise rest_framework.serializers.ValidationError(
                        'Invalid timezone: {}'.format(value),
                    )
            else:
                for hour in value:
                    if hour < 0 or hour > 23:
                        raise rest_framework.serializers.ValidationError(
                            'Invalid hour: {}'.format(hour),
                        )
        return data


class AdGroupTargetingSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    devices = restapi.serializers.targeting.DevicesSerializer(
        source='target_devices',
        allow_empty=False,
        error_messages={'required': 'Please select at least one target device.'},
    )
    placements = restapi.serializers.targeting.PlacementsSerializer(
        source='target_placements',
        required=False,
    )
    os = restapi.serializers.targeting.OSsSerializer(
        source='target_os',
        required=False,
    )
    browsers = restapi.serializers.targeting.BrowsersSerializer(
        source='target_browsers',
        required=False,
    )
    audience = restapi.serializers.targeting.AudienceSerializer(
        source='bluekai_targeting',
        required=False,
    )
    geo = AdGroupGeoSerializer(source='*', required=False)
    interest = AdGroupInterestSerializer(source='*', required=False)
    publisher_groups = AdGroupPublisherGroupsSerializer(source='*', required=False)
    custom_audiences = AdGroupCustomAudiencesSerializer(source='*', required=False)
    retargeting_ad_groups = AdGroupRetargetingSerializer(source='*', required=False)


class AdGroupAutopilotSerializer(rest_framework.serializers.Serializer):
    state = restapi.fields.DashConstantField(
        constants.AdGroupSettingsAutopilotState,
        source='autopilot_state',
        required=False,
    )
    daily_budget = rest_framework.serializers.DecimalField(
        source='local_autopilot_daily_budget',
        max_digits=10,
        decimal_places=4,
        allow_null=True,
        required=False,
    )


class AdGroupSerializer(restapi.common.serializers.PermissionedFieldsMixin,
                        restapi.serializers.base.RESTAPIBaseSerializer):
    class Meta:
        permissioned_fields = {'click_capping_daily_ad_group_max_clicks': 'zemauth.can_set_click_capping',
                               'click_capping_daily_click_budget': 'zemauth.can_set_click_capping'}

    id = restapi.fields.IdField(read_only=True, source='ad_group.id')
    campaign_id = restapi.fields.IdField(source='ad_group.campaign.id')
    name = restapi.fields.PlainCharField(
        source='ad_group_name',
        max_length=127,
        error_messages={'required': 'Please specify ad group name.'},
    )
    state = restapi.fields.DashConstantField(
        constants.AdGroupSettingsState,
        default=constants.AdGroupSettingsState.INACTIVE,
    )
    archived = rest_framework.serializers.BooleanField(
        default=False,
        required=False,
    )
    start_date = rest_framework.serializers.DateField(required=False)
    end_date = rest_framework.serializers.DateField(required=False, allow_null=True)
    tracking_code = restapi.fields.PlainCharField(required=False, allow_blank=True)
    max_cpc = rest_framework.serializers.DecimalField(
        source='local_cpc_cc',
        max_digits=10,
        decimal_places=4,
        allow_null=True,
        required=False,
    )
    max_cpm = rest_framework.serializers.DecimalField(
        source='local_max_cpm',
        max_digits=10,
        decimal_places=4,
        allow_null=True,
        required=False,
    )
    daily_budget = rest_framework.serializers.DecimalField(
        source='daily_budget_cc',
        max_digits=10,
        decimal_places=4,
        required=False,
    )
    delivery_type = restapi.fields.DashConstantField(
        constants.AdGroupDeliveryType,
        required=False,
    )
    click_capping_daily_ad_group_max_clicks = rest_framework.serializers.IntegerField(
        allow_null=True,
        required=False,
    )
    click_capping_daily_click_budget = rest_framework.serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        allow_null=True,
        required=False,
    )
    dayparting = AdGroupDaypartingSerializer(required=False)
    targeting = AdGroupTargetingSerializer(source='*', required=False)
    autopilot = AdGroupAutopilotSerializer(source='*', required=False)
