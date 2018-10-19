from mock import patch
import json

from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient

from utils.magic_mixer import magic_mixer


class SegmentReachViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend_user(
            permissions=["can_use_bluekai_targeting", "can_use_restapi"], is_superuser=False
        )
        self.client.force_authenticate(user=self.user)

    @patch("dash.features.bluekai.service.get_reach")
    def test_post(self, mock_get_reach):
        mock_get_reach.return_value = {"value": pow(10, 9), "relative": 90}
        response = self.client.post(
            reverse("internal_bluekai_reach"), data={"AND": [{"OR": [{"category": "bluekai:12345"}]}]}, format="json"
        )
        self.assertEqual(200, response.status_code)
        response_json = json.loads(response.content)
        self.assertEqual({"data": {"value": pow(10, 9), "relative": 90}}, response_json)
