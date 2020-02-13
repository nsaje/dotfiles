from restapi.common.views_base_test import RESTAPITest

from . import serializers


class CampaignGoalsSerializerTest(RESTAPITest):
    def test_conversion_goal_empty_partial_request(self):
        serializer = serializers.ConversionGoalSerializer(data={}, partial=True)
        serializer.is_valid(raise_exception=True)
