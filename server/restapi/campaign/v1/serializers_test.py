from dash import constants
from restapi.common.views_base_test_case import RESTAPITestCase

from . import serializers


class CampaignSerializerTest(RESTAPITestCase):
    def test_ga_tracking_empty_partial_request(self):
        serializer = serializers.GATrackingSerializer(data={}, partial=True)
        serializer.is_valid(raise_exception=True)

    def test_ga_tracking_missing_property_id(self):
        serializer = serializers.GATrackingSerializer(data={"enabled": True, "type": constants.GATrackingType.API})
        self.assertFalse(serializer.is_valid())
