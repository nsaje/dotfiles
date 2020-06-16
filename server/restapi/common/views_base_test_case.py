from django.test import override_settings

from utils.api_test_case import APITestCase
from utils.api_test_case import FutureAPITestCase


@override_settings(R1_DEMO_MODE=True)
class RESTAPITestCase(APITestCase):
    permissions = [
        "can_use_restapi",
        "settings_view",
        "archive_restore_entity",
        "account_campaigns_view",
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
        "account_custom_audiences_view",
        "can_set_bid_modifiers",
        "can_modify_campaign_manager",
        "can_view_platform_cost_breakdown",
        "all_accounts_accounts_add_account",
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
    ]


@override_settings(R1_DEMO_MODE=True)
class FutureRESTAPITestCase(FutureAPITestCase, RESTAPITestCase):
    pass
