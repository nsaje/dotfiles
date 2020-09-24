import json

from django.urls import reverse
from mock import patch

from restapi.common.views_base_test_case import RESTAPITestCase


class SegmentReachViewSetTestCase(RESTAPITestCase):
    def setUp(self):
        super().setUp()

    @patch("dash.features.bluekai.service.get_reach")
    def test_post(self, mock_get_reach):
        mock_get_reach.return_value = {"value": pow(10, 9), "relative": 90}
        response = self.client.post(
            reverse("restapi.bluekai.internal:bluekai_reach"),
            data={"AND": [{"OR": [{"category": "bluekai:12345"}]}]},
            format="json",
        )
        self.assertEqual(200, response.status_code)
        response_json = json.loads(response.content)
        self.assertEqual({"data": {"value": pow(10, 9), "relative": 90}}, response_json)
