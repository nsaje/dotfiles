from restapi.common.views_base_test import RESTAPITest

from . import serializers


class CampaignSerializerTest(RESTAPITest):
    def test_ga_tracking_empty_partial_request(self):
        serializer = serializers.GATrackingSerializer(data={}, partial=True)
        serializer.is_valid(raise_exception=True)
