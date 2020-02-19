from django.test import TestCase

from dash import campaign_goals
from dash import models
from dash.constants import Level
from stats import permission_filter
from stats.helpers import Goals
from utils import exc
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.models import User


def generate_rows(fields):
    rows = [{f: 1 for f in fields}]

    if "status_per_source" in fields:
        rows[0]["status_per_source"] = {1: {"source_id": 1, "source_status": 1}}
    return rows


class HasPermBCMTest(TestCase):
    def test_has_perm_bcm_v2(self):
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown"])
        self.assertTrue(permission_filter.has_perm_bcm_v2(user, "zemauth.can_view_platform_cost_breakdown", True))
        self.assertTrue(permission_filter.has_perm_bcm_v2(user, "zemauth.can_view_platform_cost_breakdown", False))

        user = magic_mixer.blend_user(["can_view_actual_costs"])
        self.assertFalse(permission_filter.has_perm_bcm_v2(user, "zemauth.can_view_platform_cost_breakdown", True))
        # this permission doesnot acutally exist for non-bcm-v2
        self.assertTrue(permission_filter.has_perm_bcm_v2(user, "zemauth.can_view_platform_cost_breakdown", False))

    def test_has_perms_bcm_v2(self):
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown"])
        self.assertTrue(permission_filter.has_perms_bcm_v2(user, ["zemauth.can_view_platform_cost_breakdown"], True))
        self.assertTrue(permission_filter.has_perms_bcm_v2(user, ["zemauth.can_view_platform_cost_breakdown"], False))

        user = magic_mixer.blend_user(["can_view_actual_costs"])
        self.assertFalse(permission_filter.has_perms_bcm_v2(user, ["zemauth.can_view_platform_cost_breakdown"], True))
        self.assertTrue(permission_filter.has_perms_bcm_v2(user, ["zemauth.can_view_platform_cost_breakdown"], False))
        self.assertFalse(
            permission_filter.has_perms_bcm_v2(
                user, ["zemauth.can_view_platform_cost_breakdown", "zemauth.can_view_end_user_cost_breakdown"], False
            )
        )


class FilterTestCase(TestCase):

    fixtures = ["test_augmenter"]

    def setUp(self):
        self.superuser = magic_mixer.blend_user(is_superuser=True)
        self.campaign = models.Campaign.objects.get(pk=1)
        self.conversion_goals = self.campaign.conversiongoal_set.all()
        self.campaign_goal_values = campaign_goals.get_campaign_goal_values(self.campaign)
        self.pixels = self.campaign.account.conversionpixel_set.all()

        self.goals = Goals(
            [x.campaign_goal for x in self.campaign_goal_values],  # campaign goals without values can exist
            self.conversion_goals,
            self.campaign_goal_values,
            self.pixels,
            self.campaign_goal_values[0].campaign_goal,
        )

        self.public_fields = {
            "id",
            "breakdown_id",
            "breakdown_name",
            "name",
            "parent_breakdown_id",
            "account",
            "account_id",
            "account_status",
            "campaign",
            "campaign_has_available_budget",
            "campaign_id",
            "campaign_status",
            "ad_group",
            "ad_group_id",
            "ad_group_status",
            "content_ad",
            "content_ad_id",
            "content_ad_status",
            "call_to_action",
            "brand_name",
            "description",
            "display_url",
            "domain",
            "domain_link",
            "editable_fields",
            "batch_id",
            "batch_name",
            "image_hash",
            "image_url",
            "ad_tag",
            "image_urls",
            "label",
            "creative_type",
            "creative_size",
            "redirector_url",
            "title",
            "tracker_urls",
            "upload_time",
            "url",
            "publisher",
            "publisher_id",
            "publisher_status",
            "blacklisted",
            "blacklisted_level",
            "blacklisted_level_description",
            "can_blacklist_publisher",
            "external_id",
            "source",
            "source_id",
            "source_name",
            "source_slug",
            "source_status",
            "exchange",
            "supply_dash_disabled_message",
            "supply_dash_url",
            "amplify_promoted_link_id",
            "amplify_live_preview_link",
            "age",
            "age_gender",
            "country",
            "day",
            "device_type",
            "dma",
            "region",
            "gender",
            "month",
            "zem_placement_type",
            "week",
            "device_os",
            "device_os_version",
            "environment",
            "archived",
            "maintenance",
            "notifications",
            "state",
            "status",
            "status_per_source",
            "status_setting",
            "daily_budget",
            "local_daily_budget",
            "bid_cpc",
            "local_bid_cpc",
            "current_bid_cpc",
            "local_current_bid_cpc",
            "bid_cpm",
            "local_bid_cpm",
            "current_bid_cpm",
            "local_current_bid_cpm",
            "current_daily_budget",
            "local_current_daily_budget",
            "max_bid_cpc",
            "min_bid_cpc",
            "max_bid_cpm",
            "min_bid_cpm",
            "billing_cost",
            "local_billing_cost",
            "clicks",
            "impressions",
            "cpc",
            "local_cpc",
            "cpm",
            "local_cpm",
            "ctr",
            "avg_cost_per_minute",
            "local_avg_cost_per_minute",
            "avg_cost_per_non_bounced_visit",
            "local_avg_cost_per_non_bounced_visit",
            "avg_cost_per_pageview",
            "local_avg_cost_per_pageview",
            "avg_cost_for_new_visitor",
            "local_avg_cost_for_new_visitor",
            "avg_cost_per_visit",
            "local_avg_cost_per_visit",
            "avg_cost_per_pixel_1_168",
            "local_avg_cost_per_pixel_1_168",
            "avg_cost_per_pixel_1_2160",
            "local_avg_cost_per_pixel_1_2160",
            "avg_cost_per_pixel_1_24",
            "local_avg_cost_per_pixel_1_24",
            "avg_cost_per_pixel_1_720",
            "local_avg_cost_per_pixel_1_720",
            "pixel_1_168",
            "pixel_1_2160",
            "pixel_1_24",
            "pixel_1_720",
            "roas_pixel_1_168",
            "roas_pixel_1_2160",
            "roas_pixel_1_24",
            "roas_pixel_1_720",
            "video_cpcv",
            "local_video_cpcv",
            "video_cpv",
            "local_video_cpv",
            "video_complete",
            "video_first_quartile",
            "video_midpoint",
            "video_playback_method",
            "video_progress_3s",
            "video_start",
            "video_third_quartile",
            "agency_cost",
            "local_agency_cost",
            "total_fee_projection",
            "total_fee",
            "flat_fee",
            "margin",
            "local_margin",
        }

        self.public_fields_uses_bcm_v2 = (
            self.public_fields
            - permission_filter.BCM2_DEPRECATED_FIELDS
            - {
                "roas_pixel_1_168",
                "roas_pixel_1_2160",
                "roas_pixel_1_24",
                "roas_pixel_1_720",
                "avg_cost_per_pixel_1_168",
                "local_avg_cost_per_pixel_1_168",
                "avg_cost_per_pixel_1_2160",
                "local_avg_cost_per_pixel_1_2160",
                "avg_cost_per_pixel_1_24",
                "local_avg_cost_per_pixel_1_24",
                "avg_cost_per_pixel_1_720",
                "local_avg_cost_per_pixel_1_720",
                "agency_cost",
                "local_agency_cost",
                "total_fee_projection",
                "total_fee",
                "flat_fee",
                "margin",
                "local_margin",
            }
        )

        # add public fields in non-bcm-v2 mode
        self.public_fields |= {
            "e_data_cost",
            "local_e_data_cost",
            "e_media_cost",
            "local_e_media_cost",
            "e_yesterday_cost",
            "local_e_yesterday_cost",
            "et_cost",
            "local_et_cost",
            "avg_et_cost_per_visit",
            "local_avg_et_cost_per_visit",
            "avg_et_cost_for_new_visitor",
            "local_avg_et_cost_for_new_visitor",
            "avg_et_cost_per_minute",
            "local_avg_et_cost_per_minute",
            "avg_et_cost_per_non_bounced_visit",
            "local_avg_et_cost_per_non_bounced_visit",
            "avg_et_cost_per_pageview",
            "local_avg_et_cost_per_pageview",
            "avg_et_cost_per_pixel_1_168",
            "local_avg_et_cost_per_pixel_1_168",
            "avg_et_cost_per_pixel_1_2160",
            "local_avg_et_cost_per_pixel_1_2160",
            "avg_et_cost_per_pixel_1_24",
            "local_avg_et_cost_per_pixel_1_24",
            "avg_et_cost_per_pixel_1_720",
            "local_avg_et_cost_per_pixel_1_720",
            "et_cpc",
            "local_et_cpc",
            "et_cpm",
            "local_et_cpm",
            "et_roas_pixel_1_168",
            "et_roas_pixel_1_2160",
            "et_roas_pixel_1_24",
            "et_roas_pixel_1_720",
            "license_fee",
            "local_license_fee",
            "license_fee_projection",
            "pacing",
            "spend_projection",
            "video_et_cpcv",
            "local_video_et_cpcv",
            "video_et_cpv",
            "local_video_et_cpv",
            "yesterday_et_cost",
            "local_yesterday_et_cost",
        }

    def _mock_constraints(self, uses_bcm_v2):
        return {"account": magic_mixer.blend(models.Account, uses_bcm_v2=uses_bcm_v2)}

    def test_filter_columns_by_permission_no_perm(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )
        self.assertCountEqual(list(rows[0].keys()), self.public_fields)

    def test_filter_columns_by_permission_no_perm_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(list(rows[0].keys()), self.public_fields_uses_bcm_v2)

    def test_filter_columns_by_permission_actual_cost(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_actual_costs"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            [
                "data_cost",
                "local_data_cost",
                "yesterday_cost",
                "local_yesterday_cost",
                "at_cost",
                "local_at_cost",
                "media_cost",
                "local_media_cost",
                "yesterday_at_cost",
                "local_yesterday_at_cost",
            ],
        )

    def test_filter_columns_by_permission_actual_cost_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_actual_costs"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_uses_bcm_v2,
            [
                "data_cost",
                "local_data_cost",
                "at_cost",
                "local_at_cost",
                "media_cost",
                "local_media_cost",
                "yesterday_at_cost",
                "local_yesterday_at_cost",
            ],
        )

    def test_filter_columns_by_permission_platform_cost(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(set(rows[0].keys()), self.public_fields)

    def test_filter_columns_by_permission_platform_cost_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown", "can_see_viewthrough_conversions"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_uses_bcm_v2,
            [
                "avg_et_cost_for_new_visitor",
                "local_avg_et_cost_for_new_visitor",
                "avg_et_cost_per_minute",
                "local_avg_et_cost_per_minute",
                "avg_et_cost_per_non_bounced_visit",
                "local_avg_et_cost_per_non_bounced_visit",
                "avg_et_cost_per_pageview",
                "local_avg_et_cost_per_pageview",
                "avg_et_cost_per_pixel_1_168",
                "local_avg_et_cost_per_pixel_1_168",
                "avg_et_cost_per_pixel_1_2160",
                "local_avg_et_cost_per_pixel_1_2160",
                "avg_et_cost_per_pixel_1_24",
                "local_avg_et_cost_per_pixel_1_24",
                "avg_et_cost_per_pixel_1_720",
                "local_avg_et_cost_per_pixel_1_720",
                "avg_et_cost_per_visit",
                "local_avg_et_cost_per_visit",
                "e_data_cost",
                "local_e_data_cost",
                "e_media_cost",
                "local_e_media_cost",
                "et_roas_pixel_1_168",
                "et_roas_pixel_1_2160",
                "et_roas_pixel_1_24",
                "et_roas_pixel_1_720",
                "license_fee",
                "local_license_fee",
                "license_fee_projection",
                "pacing",
                "spend_projection",
                "pixel_1_24_view",
                "avg_et_cost_per_pixel_1_24_view",
                "local_avg_et_cost_per_pixel_1_24_view",
                "et_roas_pixel_1_24_view",
            ],
        )

    def test_filter_columns_by_permission_platform_cost_derived_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown_derived"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.maxDiff = None
        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_uses_bcm_v2,
            [
                "et_cost",
                "local_et_cost",
                "et_cpc",
                "local_et_cpc",
                "et_cpm",
                "local_et_cpm",
                "video_et_cpcv",
                "local_video_et_cpcv",
                "video_et_cpv",
                "local_video_et_cpv",
                "yesterday_et_cost",
                "local_yesterday_et_cost",
            ],
        )

    def test_filter_columns_by_permission_agency_cost(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_agency_cost_breakdown", "can_view_agency_margin"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, ["etf_cost", "local_etf_cost"])

    def test_filter_columns_by_permission_agency_cost_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_agency_cost_breakdown", "can_view_agency_margin"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_uses_bcm_v2,
            ["etf_cost", "local_etf_cost", "margin", "local_margin"],
        )

    def test_filter_columns_by_permission_campaign_goal_optimization(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["campaign_goal_optimization"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            [
                "avg_cost_per_conversion_goal_2",
                "local_avg_cost_per_conversion_goal_2",
                "avg_cost_per_conversion_goal_3",
                "local_avg_cost_per_conversion_goal_3",
                "avg_cost_per_conversion_goal_4",
                "local_avg_cost_per_conversion_goal_4",
                "avg_cost_per_conversion_goal_5",
                "local_avg_cost_per_conversion_goal_5",
                "avg_et_cost_per_conversion_goal_2",
                "local_avg_et_cost_per_conversion_goal_2",
                "avg_et_cost_per_conversion_goal_3",
                "local_avg_et_cost_per_conversion_goal_3",
                "avg_et_cost_per_conversion_goal_4",
                "local_avg_et_cost_per_conversion_goal_4",
                "avg_et_cost_per_conversion_goal_5",
                "local_avg_et_cost_per_conversion_goal_5",
            ],
        )

    def test_filter_columns_by_permission_performance(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["campaign_goal_performance"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            ["performance_campaign_goal_1", "performance_campaign_goal_2", "performance", "styles"],
        )

    def test_filter_columns_by_permission_conversion_goals(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_see_redshift_postclick_statistics"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            ["conversion_goal_2", "conversion_goal_3", "conversion_goal_4", "conversion_goal_5"],
        )

    def test_filter_columns_by_permission_projections(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_see_projections", "can_view_flat_fees"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, ["allocated_budgets"])

    def test_filter_columns_by_permission_agency(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_view_account_agency_information"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, ["agency", "agency_id"])

    def test_filter_columns_by_permission_managers(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_see_managers_in_accounts_table", "can_see_managers_in_campaigns_table"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            [
                "default_account_manager",
                "default_sales_representative",
                "campaign_manager",
                "default_cs_representative",
                "ob_sales_representative",
                "ob_account_manager",
            ],
        )

    def test_filter_columns_by_permission_content_ad_source_status(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_see_media_source_status_on_submission_popover"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )

        self.assertEqual(rows[0]["status_per_source"], {1: {"source_id": 1, "source_status": 1}})

    def test_filter_columns_by_permission_viewthrough(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_see_viewthrough_conversions"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )
        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            [
                "pixel_1_24_view",
                "avg_cost_per_pixel_1_24_view",
                "local_avg_cost_per_pixel_1_24_view",
                "roas_pixel_1_24_view",
                "avg_et_cost_per_pixel_1_24_view",
                "local_avg_et_cost_per_pixel_1_24_view",
                "et_roas_pixel_1_24_view",
            ],
        )

    def test_filter_columns_by_permission_viewthrough_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(["can_see_viewthrough_conversions"])

        permission_filter.filter_columns_by_permission(
            user, rows, self.goals, self._mock_constraints(uses_bcm_v2), Level.ACCOUNTS
        )
        self.assertCountEqual(set(rows[0].keys()) - self.public_fields_uses_bcm_v2, ["pixel_1_24_view"])


class BreakdownAllowedTest(TestCase):
    fixtures = ["test_non_superuser"]

    def add_permission_and_test(self, level, breakdown, permissions):
        user = User.objects.get(pk=1)
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(level, user, breakdown)

        # load it again as it seems that user backend caches permissions collection once it is asked about it
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, permissions)
        permission_filter.validate_breakdown_by_permissions(level, user, breakdown)

        test_helper.remove_permissions(user, permissions)

    def test_breakdown_validate_by_permissions(self):
        self.add_permission_and_test(Level.ALL_ACCOUNTS, ["account_id"], ["all_accounts_accounts_view"])
        self.add_permission_and_test(Level.ALL_ACCOUNTS, ["source_id"], ["all_accounts_sources_view"])

        self.add_permission_and_test(Level.ACCOUNTS, ["campaign_id"], ["account_campaigns_view"])
        self.add_permission_and_test(Level.ACCOUNTS, ["source_id"], ["account_sources_view"])

        self.add_permission_and_test(Level.AD_GROUPS, ["publisher_id"], ["can_see_publishers"])

        user = User.objects.get(pk=1)
        delivery_fields = ["device_type", "device_os", "environment", "country", "region", "dma"]
        for field in delivery_fields:
            with self.assertRaises(exc.MissingDataError):
                permission_filter.validate_breakdown_by_permissions(Level.CAMPAIGNS, user, [field])
            self.add_permission_and_test(Level.AD_GROUPS, [field], ["can_see_top_level_delivery_breakdowns"])

    def test_breakdown_validate_by_delivery_permissions(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ["all_accounts_accounts_view"])

        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ["account_id", "dma"])

        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ["all_accounts_accounts_view", "can_view_breakdown_by_delivery"])

        permission_filter.validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ["account_id", "dma"])

    def test_validate_breakdown_structure(self):
        # should succeed, no exception
        permission_filter.validate_breakdown_by_structure(["account_id", "campaign_id", "device_type", "week"])
        permission_filter.validate_breakdown_by_structure(["account_id"])
        permission_filter.validate_breakdown_by_structure([])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Unsupported breakdowns: bla"):
            permission_filter.validate_breakdown_by_structure(["account_id", "bla", "device_type"])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
            permission_filter.validate_breakdown_by_structure(["account_id", "day", "device_type"])

    def test_validate_first_level_environment_breakdown_structure(self):
        delivery_fields = ["device_type", "device_os", "environment", "country", "region", "dma"]
        for field in delivery_fields:
            permission_filter.validate_breakdown_by_structure([field])

        for field in delivery_fields:
            with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
                permission_filter.validate_breakdown_by_structure([field, "day"])

        for field in delivery_fields:
            with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
                permission_filter.validate_breakdown_by_structure([field, field])
