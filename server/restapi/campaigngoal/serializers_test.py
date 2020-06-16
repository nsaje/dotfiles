from restapi.campaigngoal.v1 import serializers
from restapi.common.views_base_test_case import RESTAPITestCase


class CampaignGoalsSerializerTest(RESTAPITestCase):
    def test_conversion_goal_empty_partial_request(self):
        serializer = serializers.ConversionGoalSerializer(data={}, partial=True)
        serializer.is_valid(raise_exception=True)
