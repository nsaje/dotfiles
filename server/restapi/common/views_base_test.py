import json

from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient

from utils import json_helper
from zemauth.models import User


@override_settings(R1_DEMO_MODE=True)
class RESTAPITest(TestCase):
    fixtures = ["test_acceptance.yaml", "test_geolocations"]
    user_id = 1

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(pk=self.user_id)
        self.client.force_authenticate(user=self.user)
        self.maxDiff = None

    def assertResponseValid(self, r, status_code=200, data_type=dict):
        resp_json = json.loads(r.content)
        self.assertNotIn("errorCode", resp_json)
        self.assertEqual(r.status_code, status_code)
        self.assertIsInstance(resp_json["data"], data_type)
        return resp_json

    def assertResponseError(self, r, error_code):
        resp_json = json.loads(r.content)
        self.assertIn("errorCode", resp_json)
        self.assertEqual(resp_json["errorCode"], error_code)
        return resp_json

    @staticmethod
    def normalize(d):
        return json.loads(json.dumps(d, cls=json_helper.JSONEncoder))
