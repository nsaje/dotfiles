from django.test import TestCase

from dash import campaign_goals
from dash import models
from dash.constants import Level
from stats import permission_filter
from stats.helpers import Goals
from utils import exc
from utils import test_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models import User


class FilterTestCase(BaseTestCase):
    fixtures = ["test_augmenter"]

    def _generate_rows(self, fields):
        rows = [{f: 1 for f in fields}]

        if "account_id" in fields:
            rows[0]["account_id"] = self.account.id
        if "status_per_source" in fields:
            rows[0]["status_per_source"] = {1: {"source_id": 1, "source_status": 1}}
        return rows

    def setUp(self):
        self.superuser = magic_mixer.blend_user(is_superuser=True)
        self.account = models.Account.objects.get(pk=1)

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

        self.public_fields_legacy = {"margin", "local_margin"}

        self.public_fields_no_extra_costs = self.public_fields_legacy | permission_filter._get_fields_to_keep(
            magic_mixer.blend_user(), self.goals
        ) - {
            "etf_cost",
            "local_etf_cost",
            "e_media_cost",
            "local_e_media_cost",
            "e_data_cost",
            "local_e_data_cost",
            "license_fee",
            "local_license_fee",
            "b_media_cost",
            "local_b_media_cost",
            "b_data_cost",
            "local_b_data_cost",
            "bt_cost",
            "local_bt_cost",
            "service_fee",
            "local_service_fee",
            "service_fee_refund",
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
        }

        self.constraints = {"account": self.account}
        self.rows = self._generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals))

    def test_filter_columns_by_permission_no_perm(self):
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertCountEqual(list(self.rows[0].keys()), self.public_fields_no_extra_costs - self.public_fields_legacy)

    def test_filter_columns_by_permission_actual_cost(self):
        user = magic_mixer.blend_user(["can_view_actual_costs"])

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs,
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
        user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(
            user, [Permission.BASE_COSTS_SERVICE_FEE, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE], None
        )

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "service_fee",
                "local_service_fee",
                "service_fee_refund",
                "license_fee",
                "local_license_fee",
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
            ],
        )

    def test_filter_columns_by_permission_platform_cost_derived(self):
        user = magic_mixer.blend_user(["can_view_platform_cost_breakdown_derived"])

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs, ["et_cost", "local_et_cost"]
        )

    def test_filter_columns_by_permission_managers(self):
        user = magic_mixer.blend_user(["can_see_managers_in_accounts_table", "can_see_managers_in_campaigns_table"])

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields,
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
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertEqual(self.rows[0]["status_per_source"], {1: {"source_id": 1, "source_status": 1}})

    def test_filter_columns_by_permission_service_fee_refund(self):
        user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(user, [Permission.BASE_COSTS_SERVICE_FEE], None)

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)

        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "b_media_cost",
                "b_data_cost",
                "local_b_media_cost",
                "local_b_data_cost",
                "bt_cost",
                "local_bt_cost",
                "service_fee",
                "local_service_fee",
                "service_fee_refund",
            ],
        )

    def test_filter_columns_by_entity_permission_agency_spend_margin(self):
        user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(user, [Permission.READ, Permission.AGENCY_SPEND_MARGIN], self.account)

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)
        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs | {"margin", "local_margin"},
            ["margin", "local_margin", "etf_cost", "local_etf_cost"],
        )

    def test_filter_columns_without_entity_permissions(self):
        user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(user, [Permission.READ], self.account)

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)
        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs | {"margin", "local_margin"},
            ["margin", "local_margin"],
        )

    def test_filter_columns_by_entity_permission_media_cost_data_cost_licence_fee(self):
        user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(
            user, [Permission.READ, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE], self.account
        )

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)
        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "e_media_cost",
                "local_e_media_cost",
                "e_data_cost",
                "local_e_data_cost",
                "license_fee",
                "local_license_fee",
            ],
        )

    def test_filter_columns_by_entity_permission_base_cost_service_fee(self):
        user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(user, [Permission.READ, Permission.BASE_COSTS_SERVICE_FEE], self.account)

        permission_filter.filter_columns_by_permission(user, self.constraints, self.rows, self.goals)
        self.assertCountEqual(
            set(self.rows[0].keys()) - self.public_fields_no_extra_costs,
            [
                "b_media_cost",
                "local_b_media_cost",
                "b_data_cost",
                "local_b_data_cost",
                "bt_cost",
                "local_bt_cost",
                "service_fee",
                "local_service_fee",
                "service_fee_refund",
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
        delivery_fields = [
            "device_type",
            "device_os",
            "environment",
            "country",
            "region",
            "dma",
            "browser",
            "connection_type",
        ]
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
