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

        self.public_fields_legacy = {"total_fee_projection", "total_fee", "flat_fee", "margin", "local_margin"}

        self.public_fields_no_extra_costs = self.public_fields_legacy | {
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
            "clicks",
            "impressions",
            "ctr",
            "etfm_cpc",
            "local_etfm_cpc",
            "etfm_cpm",
            "local_etfm_cpm",
            "etfm_cost",
            "local_etfm_cost",
            "yesterday_etfm_cost",
            "local_yesterday_etfm_cost",
            "avg_etfm_cost_per_visit",
            "local_avg_etfm_cost_per_visit",
            "avg_etfm_cost_for_new_visitor",
            "local_avg_etfm_cost_for_new_visitor",
            "avg_etfm_cost_per_minute",
            "local_avg_etfm_cost_per_minute",
            "avg_etfm_cost_per_non_bounced_visit",
            "local_avg_etfm_cost_per_non_bounced_visit",
            "avg_etfm_cost_per_pageview",
            "local_avg_etfm_cost_per_pageview",
            "pixel_1_168",
            "pixel_1_2160",
            "pixel_1_24",
            "pixel_1_720",
            "avg_etfm_cost_per_pixel_1_168",
            "local_avg_etfm_cost_per_pixel_1_168",
            "avg_etfm_cost_per_pixel_1_2160",
            "local_avg_etfm_cost_per_pixel_1_2160",
            "avg_etfm_cost_per_pixel_1_24",
            "local_avg_etfm_cost_per_pixel_1_24",
            "avg_etfm_cost_per_pixel_1_720",
            "local_avg_etfm_cost_per_pixel_1_720",
            "etfm_roas_pixel_1_168",
            "etfm_roas_pixel_1_2160",
            "etfm_roas_pixel_1_24",
            "etfm_roas_pixel_1_720",
            "conversion_rate_per_pixel_1_24",
            "conversion_rate_per_pixel_1_168",
            "conversion_rate_per_pixel_1_720",
            "conversion_rate_per_pixel_1_2160",
            "video_complete",
            "video_first_quartile",
            "video_midpoint",
            "video_playback_method",
            "video_progress_3s",
            "video_start",
            "video_third_quartile",
            "video_etfm_cpcv",
            "local_video_etfm_cpcv",
            "video_etfm_cpv",
            "local_video_etfm_cpv",
        }

        self.public_fields = self.public_fields_no_extra_costs | {
            "b_data_cost",
            "local_b_data_cost",
            "e_data_cost",
            "local_e_data_cost",
            "b_media_cost",
            "local_b_media_cost",
            "e_media_cost",
            "local_e_media_cost",
            "bt_cost",
            "local_bt_cost",
            "et_cost",
            "local_et_cost",
            "service_fee",
            "local_service_fee",
            "license_fee",
            "local_license_fee",
            "license_fee_projection",
            "pacing",
            "spend_projection",
        }

    def _mock_constraints(self):
        return {"account": magic_mixer.blend(models.Account)}

    def test_filter_columns_by_permission_no_perm(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(list(rows[0].keys()), self.public_fields_no_extra_costs - self.public_fields_legacy)

    def test_filter_columns_by_permission_actual_cost(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_view_actual_costs"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_no_extra_costs,
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
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(
            ["can_view_platform_cost_breakdown", "can_see_viewthrough_conversions", "can_see_service_fee"]
        )

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "service_fee",
                "local_service_fee",
                "license_fee",
                "local_license_fee",
                "license_fee_projection",
                "pacing",
                "spend_projection",
                "b_data_cost",
                "local_b_data_cost",
                "b_media_cost",
                "local_b_media_cost",
                "e_data_cost",
                "local_e_data_cost",
                "e_media_cost",
                "local_e_media_cost",
                "bt_cost",
                "local_bt_cost",
                "pixel_1_24_view",
                "avg_etfm_cost_per_pixel_1_24_view",
                "local_avg_etfm_cost_per_pixel_1_24_view",
                "conversion_rate_per_pixel_1_24_view",
                "etfm_roas_pixel_1_24_view",
            ],
        )

    def test_filter_columns_by_permission_platform_cost_derived(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown_derived"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.maxDiff = None
        self.assertCountEqual(set(rows[0].keys()) - self.public_fields_no_extra_costs, ["et_cost", "local_et_cost"])

    def test_filter_columns_by_permission_agency_cost(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_view_agency_cost_breakdown", "can_view_agency_margin"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_no_extra_costs | {"margin", "local_margin"},
            ["etf_cost", "local_etf_cost", "margin", "local_margin"],
        )

    def test_filter_columns_by_permission_campaign_goal_optimization(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["campaign_goal_optimization", "can_view_platform_cost_breakdown"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            [
                "avg_etfm_cost_per_conversion_goal_2",
                "local_avg_etfm_cost_per_conversion_goal_2",
                "avg_etfm_cost_per_conversion_goal_3",
                "local_avg_etfm_cost_per_conversion_goal_3",
                "avg_etfm_cost_per_conversion_goal_4",
                "local_avg_etfm_cost_per_conversion_goal_4",
                "avg_etfm_cost_per_conversion_goal_5",
                "local_avg_etfm_cost_per_conversion_goal_5",
            ],
        )

    def test_filter_columns_by_permission_performance(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["campaign_goal_performance"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            ["etfm_performance_campaign_goal_1", "etfm_performance_campaign_goal_2", "styles"],
        )

    def test_filter_columns_by_permission_conversion_goals(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_redshift_postclick_statistics"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields,
            [
                "conversion_goal_2",
                "conversion_goal_3",
                "conversion_goal_4",
                "conversion_goal_5",
                "conversion_rate_per_conversion_goal_2",
                "conversion_rate_per_conversion_goal_3",
                "conversion_rate_per_conversion_goal_4",
                "conversion_rate_per_conversion_goal_5",
            ],
        )

    def test_filter_columns_by_permission_projections(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_projections", "can_view_flat_fees"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, ["allocated_budgets"])

    def test_filter_columns_by_permission_agency(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_view_account_agency_information"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, ["agency", "agency_id"])

    def test_filter_columns_by_permission_managers(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_managers_in_accounts_table", "can_see_managers_in_campaigns_table"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

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
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_media_source_status_on_submission_popover"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertEqual(rows[0]["status_per_source"], {1: {"source_id": 1, "source_status": 1}})

    def test_filter_columns_by_permission_viewthrough(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_viewthrough_conversions"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "pixel_1_24_view",
                "avg_etfm_cost_per_pixel_1_24_view",
                "local_avg_etfm_cost_per_pixel_1_24_view",
                "etfm_roas_pixel_1_24_view",
                "conversion_rate_per_pixel_1_24_view",
            ],
        )

    def test_filter_columns_by_permission_placement(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))

        user = magic_mixer.blend_user(["can_use_placement_targeting"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)
        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, ["placement_id", "placement", "placement_type"])

    def test_filter_columns_by_permission_placement_no_permission(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))

        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(user, rows, self.goals)
        self.assertCountEqual(set(rows[0].keys()) - self.public_fields, [])

    def test_filter_columns_by_permission_refund(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_credit_refunds"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "media_cost_refund",
                "e_media_cost_refund",
                "at_cost_refund",
                "et_cost_refund",
                "etf_cost_refund",
                "etfm_cost_refund",
                "license_fee_refund",
                "margin_refund",
            ],
        )

    def test_filter_columns_by_permission_service_fee_refund(self):
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))
        user = magic_mixer.blend_user(["can_see_credit_refunds", "can_see_service_fee"])

        permission_filter.filter_columns_by_permission(user, rows, self.goals)

        self.assertCountEqual(
            set(rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "b_media_cost",
                "b_data_cost",
                "local_b_media_cost",
                "local_b_data_cost",
                "bt_cost",
                "local_bt_cost",
                "service_fee",
                "local_service_fee",
                "media_cost_refund",
                "e_media_cost_refund",
                "at_cost_refund",
                "et_cost_refund",
                "etf_cost_refund",
                "etfm_cost_refund",
                "service_fee_refund",
                "license_fee_refund",
                "margin_refund",
            ],
        )


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

        self.add_permission_and_test(Level.ALL_ACCOUNTS, ["placement_id"], ["can_use_placement_targeting"])
        self.add_permission_and_test(Level.ACCOUNTS, ["placement_id"], ["can_use_placement_targeting"])
        self.add_permission_and_test(Level.CAMPAIGNS, ["placement_id"], ["can_use_placement_targeting"])
        self.add_permission_and_test(Level.AD_GROUPS, ["placement_id"], ["can_use_placement_targeting"])

        self.add_permission_and_test(Level.AD_GROUPS, ["publisher_id"], ["can_see_publishers"])

        user = User.objects.get(pk=1)
        delivery_fields = ["device_type", "device_os", "environment", "country", "region", "dma"]
        for field in delivery_fields:
            with self.assertRaises(exc.MissingDataError):
                permission_filter.validate_breakdown_by_permissions(Level.CAMPAIGNS, user, [field])
            self.add_permission_and_test(Level.AD_GROUPS, [field], ["can_see_top_level_delivery_breakdowns"])

    def test_breakdown_validate_by_permissions_placement_type(self):
        user = User.objects.get(pk=1)

        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ["placement_type"])
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.ACCOUNTS, user, ["placement_type"])
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.CAMPAIGNS, user, ["placement_type"])
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.AD_GROUPS, user, ["placement_type"])

        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ["can_use_placement_targeting", "can_see_top_level_delivery_breakdowns"])

        # invalid base dimension
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ["placement_type"])
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.ACCOUNTS, user, ["placement_type"])
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.CAMPAIGNS, user, ["placement_type"])
        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.AD_GROUPS, user, ["placement_type"])

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

    def test_validate_breakdown_structure_placement(self):
        permission_filter.validate_breakdown_by_structure(["ad_group_id", "placement_id", "week"])
        permission_filter.validate_breakdown_by_structure(["ad_group_id", "placement_id"])
        permission_filter.validate_breakdown_by_structure(["ad_group_id", "placement_id", "day"])
        permission_filter.validate_breakdown_by_structure(["ad_group_id", "week"])
        permission_filter.validate_breakdown_by_structure(["ad_group_id", "placement_id"])

        permission_filter.validate_breakdown_by_structure(["placement_id"])
        permission_filter.validate_breakdown_by_structure(["placement_id", "week"])
        permission_filter.validate_breakdown_by_structure(["publisher_id", "placement_id", "week"])

        permission_filter.validate_breakdown_by_structure(["placement_id", "publisher_id"])

        # Placement type is not a valid breakdown
        with self.assertRaises(exc.InvalidBreakdownError):
            permission_filter.validate_breakdown_by_structure(["placement", "placement_type"])

        # Publisher and placement are both structure dimensions so ad group breakdown (on campaign level) by both is
        # currently not supported.
        with self.assertRaises(exc.InvalidBreakdownError):
            permission_filter.validate_breakdown_by_structure(["ad_group_id", "publisher_id", "placement_id"])
        with self.assertRaises(exc.InvalidBreakdownError):
            permission_filter.validate_breakdown_by_structure(["ad_group_id", "placement_id", "publisher_id"])

        # Placement broken down by delivery breakdowns (except placement type) is currently not supported.
        with self.assertRaisesMessage(
            exc.InvalidBreakdownError, "Unsupported breakdown - placements can not be broken down by dma"
        ):
            permission_filter.validate_breakdown_by_structure(["placement_id", "dma"])

        # Content ad breakdown by placement dimensions is currently not supported due to data size concerns.
        with self.assertRaisesMessage(
            exc.InvalidBreakdownError, "Unsupported breakdown - content ads can not be broken down by placement"
        ):
            permission_filter.validate_breakdown_by_structure(["ad_group_id", "content_ad_id", "placement_id"])
        with self.assertRaisesMessage(
            exc.InvalidBreakdownError, "Unsupported breakdown - content ads can not be broken down by placement"
        ):
            permission_filter.validate_breakdown_by_structure(["content_ad_id", "placement_id"])
