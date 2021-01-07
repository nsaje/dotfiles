import json

from django.test import override_settings
from rest_framework.test import APIClient

from utils import json_helper
from utils.base_test_case import BaseTestCase


@override_settings(R1_DEMO_MODE=True)
class RESTAPITestCase(BaseTestCase):

    permissions = [
        "can_set_click_capping_daily_click_budget",
        "can_manage_credit_refunds",
        "can_view_platform_cost_breakdown",
        "can_modify_account_type",
        "can_modify_account_manager",
        "can_set_account_sales_representative",
        "can_set_account_cs_representative",
        "can_set_account_ob_representative",
        "can_see_salesforce_url",
        "can_see_all_available_sources",
        "can_manage_agency_margin",
        "can_see_deals_in_ui",
        "account_credit_view",
        "can_see_backend_hacks",
        "can_see_service_fee",
        "can_use_3rdparty_js_trackers",
        "can_use_oen_browser_targeting",
        "can_see_creative_library",
    ]

    def setUp(self):
        super().setUp()
        self.client = APIClient()
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
