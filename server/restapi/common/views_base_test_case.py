import json

from django.test import override_settings
from rest_framework.test import APIClient

from utils import json_helper
from utils.base_test_case import BaseTestCase
from utils.base_test_case import FutureBaseTestCase


@override_settings(R1_DEMO_MODE=True)
class RESTAPITestCase(BaseTestCase):
    """
    RESTAPITestCase will be replaced with FutureRESTAPITestCase
    after User Roles will be released.
    """

    permissions = [
        "can_use_restapi",
        "can_see_campaign_goals",
        "can_modify_publisher_blacklist_status",
        "can_edit_publisher_groups",
        "can_see_rtb_sources_as_one",
        "can_set_rtb_sources_as_one_cpc",
        "can_set_adgroup_to_auto_pilot",
        "can_set_ad_group_max_cpc",
        "fea_can_use_cpm_buying",
        "can_modify_account_name",
        "can_set_white_blacklist_publisher_groups",
        "can_modify_campaign_iab_category",
        "can_set_advanced_device_targeting",
        "can_use_bluekai_targeting",
        "can_set_click_capping",
        "can_set_click_capping_daily_click_budget",
        "can_manage_credit_refunds",
        "can_set_frequency_capping",
        "can_use_language_targeting",
        "can_see_pixel_notes",
        "can_see_pixel_traffic",
        "can_set_bid_modifiers",
        "can_modify_campaign_manager",
        "can_view_platform_cost_breakdown",
        "can_set_agency_for_account",
        "can_modify_account_type",
        "can_modify_account_manager",
        "can_set_account_sales_representative",
        "can_set_account_cs_representative",
        "can_set_account_ob_representative",
        "can_set_auto_add_new_sources",
        "can_see_salesforce_url",
        "can_modify_allowed_sources",
        "can_see_all_available_sources",
        "can_manage_agency_margin",
        "can_see_deals_in_ui",
        "can_see_direct_deals_section",
        "can_use_creative_icon",
        "account_credit_view",
        "can_clone_campaigns",
        "can_see_backend_hacks",
        "can_see_service_fee",
        "can_use_browser_targeting",
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


@override_settings(R1_DEMO_MODE=True)
class FutureRESTAPITestCase(FutureBaseTestCase, RESTAPITestCase):
    pass
