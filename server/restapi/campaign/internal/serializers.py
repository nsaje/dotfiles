import rest_framework.serializers

import dash.constants
import restapi.campaign.v1.serializers
import restapi.campaigngoal.serializers
import restapi.serializers.base
import restapi.serializers.deals
import restapi.serializers.fields
import restapi.serializers.hack
import zemauth.models


# TODO: refactor to common serializer if necessary
class ExtraDataCampaignManagerSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = rest_framework.serializers.IntegerField(required=False)
    name = rest_framework.serializers.CharField(required=False)


class ExtraDataSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    language = restapi.serializers.fields.DashConstantField(dash.constants.Language, required=False)
    can_archive = rest_framework.serializers.BooleanField(default=False, required=False)
    can_restore = rest_framework.serializers.BooleanField(default=False, required=False)
    goals_defaults = restapi.campaigngoal.serializers.CampaignGoalsDefaultsSerializer()
    campaign_managers = rest_framework.serializers.ListField(
        child=ExtraDataCampaignManagerSerializer(), default=[], allow_empty=True
    )
    hacks = rest_framework.serializers.ListField(
        child=restapi.serializers.hack.HackSerializer(), default=[], allow_empty=True
    )
    deals = rest_framework.serializers.ListField(
        child=restapi.serializers.deals.DealSerializer(), default=[], allow_empty=True
    )


class CampaignSerializer(restapi.campaign.v1.serializers.CampaignSerializer):
    class Meta:
        permissioned_fields = {
            "frequency_capping": "zemauth.can_set_frequency_capping",
            "iab_category": "zemauth.can_modify_campaign_iab_category",
            "campaign_manager": "zemauth.can_modify_campaign_manager",
        }

    campaign_manager = rest_framework.serializers.IntegerField(source="campaign_manager.id", required=False)
    goals = rest_framework.serializers.ListSerializer(
        child=restapi.campaigngoal.serializers.CampaignGoalSerializer(), default=[], allow_empty=True
    )

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value["campaign_manager"] = self.to_internal_value_campaign_manager(data.get("campaign_manager"))
        return value

    def to_internal_value_campaign_manager(self, data):
        if data is None:
            return data
        try:
            value = zemauth.models.User.objects.get(pk=data)
        except zemauth.models.User.DoesNotExist:
            raise rest_framework.serializers.ValidationError({"campaign_manager": ["Invalid campaign manager."]})
        return value
