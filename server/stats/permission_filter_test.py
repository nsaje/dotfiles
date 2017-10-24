from django.test import TestCase

from utils import exc
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.models import User

from dash import models
from dash import campaign_goals
from dash.constants import Level

from stats import permission_filter
from stats.helpers import Goals


def generate_rows(fields):
    rows = [{f: 1 for f in fields}]

    if 'status_per_source' in fields:
        rows[0]['status_per_source'] = {
            1: {
                'source_id': 1,
                'source_status': 1,
            }
        }
    return rows


class HasPermBCMTest(TestCase):

    def test_has_perm_bcm_v2(self):
        user = magic_mixer.blend_user(['can_view_platform_cost_breakdown'])
        self.assertTrue(permission_filter.has_perm_bcm_v2(user, 'zemauth.can_view_platform_cost_breakdown', True))
        self.assertTrue(permission_filter.has_perm_bcm_v2(user, 'zemauth.can_view_platform_cost_breakdown', False))

        user = magic_mixer.blend_user(['can_view_actual_costs'])
        self.assertFalse(permission_filter.has_perm_bcm_v2(user, 'zemauth.can_view_platform_cost_breakdown', True))
        # this permission doesnot acutally exist for non-bcm-v2
        self.assertTrue(permission_filter.has_perm_bcm_v2(user, 'zemauth.can_view_platform_cost_breakdown', False))

    def test_has_perms_bcm_v2(self):
        user = magic_mixer.blend_user(['can_view_platform_cost_breakdown'])
        self.assertTrue(permission_filter.has_perms_bcm_v2(user, ['zemauth.can_view_platform_cost_breakdown'], True))
        self.assertTrue(permission_filter.has_perms_bcm_v2(user, ['zemauth.can_view_platform_cost_breakdown'], False))

        user = magic_mixer.blend_user(['can_view_actual_costs'])
        self.assertFalse(permission_filter.has_perms_bcm_v2(user, ['zemauth.can_view_platform_cost_breakdown'], True))
        self.assertTrue(permission_filter.has_perms_bcm_v2(user, ['zemauth.can_view_platform_cost_breakdown'], False))
        self.assertFalse(permission_filter.has_perms_bcm_v2(
            user, ['zemauth.can_view_platform_cost_breakdown', 'zemauth.can_view_end_user_cost_breakdown'], False))


class FilterTestCase(TestCase):

    fixtures = ['test_augmenter']

    def setUp(self):
        self.superuser = magic_mixer.blend_user(is_superuser=True)
        self.campaign = models.Campaign.objects.get(pk=1)
        self.conversion_goals = self.campaign.conversiongoal_set.all()
        self.campaign_goal_values = campaign_goals.get_campaign_goal_values(self.campaign)
        self.pixels = self.campaign.account.conversionpixel_set.all()

        self.goals = Goals(
            [x.campaign_goal for x in self.campaign_goal_values],  # campaign goals without values can exist
            self.conversion_goals, self.campaign_goal_values, self.pixels,
            self.campaign_goal_values[0].campaign_goal
        )

        self.public_fields = {
            'id', 'breakdown_id', 'breakdown_name', 'name', 'parent_breakdown_id',
            'account', 'account_id', 'account_status',
            'campaign', 'campaign_has_available_budget', 'campaign_id', 'campaign_status', 'campaign_stop_inactive',
            'ad_group', 'ad_group_id', 'ad_group_status',
            'content_ad', 'content_ad_id', 'content_ad_status', 'call_to_action', 'brand_name', 'description', 'display_url',
            'domain', 'domain_link', 'editable_fields', 'batch_id', 'batch_name', 'image_hash', 'image_url', 'image_urls', 'label', 'redirector_url', 'title', 'tracker_urls', 'upload_time', 'url',
            'publisher', 'publisher_id', 'publisher_status', 'blacklisted', 'blacklisted_level', 'blacklisted_level_description', 'can_blacklist_publisher', 'external_id',
            'source', 'source_id', 'source_name', 'source_slug', 'source_status', 'exchange', 'supply_dash_disabled_message', 'supply_dash_url',
            'age', 'age_gender', 'country', 'day', 'device_type', 'dma', 'gender', 'month', 'placement_type', 'week', 'device_os', 'device_os_version', 'placement_medium',
            'archived', 'maintenance', 'notifications', 'state', 'status', 'status_per_source', 'status_setting',
            'daily_budget', 'bid_cpc', 'current_bid_cpc', 'current_daily_budget', 'max_bid_cpc', 'min_bid_cpc',
            'billing_cost',
            'clicks', 'impressions',
            'cpc', 'cpm', 'ctr',
            'avg_cost_per_minute', 'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview', 'avg_cost_for_new_visitor', 'avg_cost_per_visit',
            'avg_cost_per_pixel_1_168', 'avg_cost_per_pixel_1_2160', 'avg_cost_per_pixel_1_24', 'avg_cost_per_pixel_1_720',
            'pixel_1_168', 'pixel_1_2160', 'pixel_1_24', 'pixel_1_720',
            'roas_pixel_1_168', 'roas_pixel_1_2160', 'roas_pixel_1_24', 'roas_pixel_1_720',
            'video_complete', 'video_cpcv', 'video_cpv', 'video_first_quartile', 'video_midpoint', 'video_playback_method', 'video_progress_3s', 'video_start', 'video_third_quartile',
            'total_fee_projection', 'agency_cost', 'total_fee', 'flat_fee', 'margin',
        }

        self.public_fields_uses_bcm_v2 = self.public_fields - permission_filter.BCM2_DEPRECATED_FIELDS - {
            'roas_pixel_1_168', 'roas_pixel_1_2160', 'roas_pixel_1_24', 'roas_pixel_1_720',
            'avg_cost_per_pixel_1_168', 'avg_cost_per_pixel_1_2160', 'avg_cost_per_pixel_1_24', 'avg_cost_per_pixel_1_720',
            'total_fee_projection', 'agency_cost', 'total_fee', 'flat_fee', 'margin',
        }

        # add public fields in non-bcm-v2 mode
        self.public_fields |= {
            'e_data_cost', 'e_media_cost', 'e_yesterday_cost',
            'et_cost',
            'avg_et_cost_per_visit', 'avg_et_cost_for_new_visitor', 'avg_et_cost_per_minute', 'avg_et_cost_per_non_bounced_visit', 'avg_et_cost_per_pageview',
            'avg_et_cost_per_pixel_1_168', 'avg_et_cost_per_pixel_1_2160', 'avg_et_cost_per_pixel_1_24', 'avg_et_cost_per_pixel_1_720',
            'et_cpc', 'et_cpm',
            'et_roas_pixel_1_168', 'et_roas_pixel_1_2160', 'et_roas_pixel_1_24', 'et_roas_pixel_1_720',
            'license_fee', 'license_fee_projection', 'pacing', 'spend_projection',
            'video_et_cpcv', 'video_et_cpv',
            'yesterday_et_cost',
        }

    def _mock_constraints(self, uses_bcm_v2):
        return {
            'account': magic_mixer.blend(models.Account, uses_bcm_v2=uses_bcm_v2)
        }

    def test_filter_columns_by_permission_no_perm(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(rows[0].keys(), self.public_fields)

    def test_filter_columns_by_permission_no_perm_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user()

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(rows[0].keys(), self.public_fields_uses_bcm_v2)

    def test_filter_columns_by_permission_actual_cost(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_actual_costs'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'data_cost', 'yesterday_cost', 'at_cost', 'media_cost', 'yesterday_at_cost'
        ])

    def test_filter_columns_by_permission_actual_cost_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_actual_costs'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields_uses_bcm_v2, [
            'data_cost', 'at_cost', 'media_cost', 'yesterday_at_cost'
        ])

    def test_filter_columns_by_permission_platform_cost(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_platform_cost_breakdown'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()), self.public_fields)

    def test_filter_columns_by_permission_platform_cost_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_platform_cost_breakdown'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields_uses_bcm_v2, [
            'avg_et_cost_for_new_visitor', 'avg_et_cost_per_minute', 'avg_et_cost_per_non_bounced_visit',
            'avg_et_cost_per_pageview', 'avg_et_cost_per_pixel_1_168', 'avg_et_cost_per_pixel_1_2160',
            'avg_et_cost_per_pixel_1_24', 'avg_et_cost_per_pixel_1_720', 'avg_et_cost_per_visit',
            'e_data_cost', 'e_media_cost', 'et_cost', 'et_cpc', 'et_cpm',
            'et_roas_pixel_1_168', 'et_roas_pixel_1_2160', 'et_roas_pixel_1_24', 'et_roas_pixel_1_720',
            'license_fee', 'license_fee_projection', 'pacing', 'spend_projection', 'video_et_cpcv',
            'video_et_cpv', 'yesterday_et_cost'
        ])

    def test_filter_columns_by_permission_agency_cost(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_agency_cost_breakdown', 'can_view_agency_margin'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'etf_cost',
        ])

    def test_filter_columns_by_permission_agency_cost_bcm_v2(self):
        uses_bcm_v2 = True
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_agency_cost_breakdown', 'can_view_agency_margin'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields_uses_bcm_v2, [
            'etf_cost', 'margin',
        ])

    def test_filter_columns_by_permission_campaign_goal_optimization(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['campaign_goal_optimization'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'avg_cost_per_conversion_goal_2', 'avg_cost_per_conversion_goal_3',
            'avg_cost_per_conversion_goal_4', 'avg_cost_per_conversion_goal_5',
            'avg_et_cost_per_conversion_goal_2', 'avg_et_cost_per_conversion_goal_3',
            'avg_et_cost_per_conversion_goal_4', 'avg_et_cost_per_conversion_goal_5',
        ])

    def test_filter_columns_by_permission_performance(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['campaign_goal_performance'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'performance_campaign_goal_1', 'performance_campaign_goal_2',
            'performance', 'styles',
        ])

    def test_filter_columns_by_permission_conversion_goals(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_see_redshift_postclick_statistics'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5',
        ])

    def test_filter_columns_by_permission_projections(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_see_projections', 'can_view_flat_fees'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'allocated_budgets',
        ])

    def test_filter_columns_by_permission_agency(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_view_account_agency_information'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'agency', 'agency_id'
        ])

    def test_filter_columns_by_permission_managers(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_see_managers_in_accounts_table', 'can_see_managers_in_campaigns_table'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertItemsEqual(set(rows[0].keys()) - self.public_fields, [
            'default_account_manager', 'default_sales_representative', 'campaign_manager',
            'default_cs_representative',
        ])

    def test_filter_columns_by_permission_content_ad_source_status(self):
        uses_bcm_v2 = False
        rows = generate_rows(permission_filter._get_fields_to_keep(self.superuser, self.goals, uses_bcm_v2))
        user = magic_mixer.blend_user(['can_see_media_source_status_on_submission_popover'])

        permission_filter.filter_columns_by_permission(user, rows, self.goals, self._mock_constraints(uses_bcm_v2))

        self.assertEqual(rows[0]['status_per_source'], {
            1: {
                'source_id': 1,
                'source_status': 1,
            },
        })


class BreakdownAllowedTest(TestCase):
    fixtures = ['test_non_superuser']

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
        self.add_permission_and_test(Level.ALL_ACCOUNTS, ['account_id'], ['all_accounts_accounts_view'])
        self.add_permission_and_test(Level.ALL_ACCOUNTS, ['source_id'], ['all_accounts_sources_view'])

        self.add_permission_and_test(Level.ACCOUNTS, ['campaign_id'], ['account_campaigns_view'])
        self.add_permission_and_test(Level.ACCOUNTS, ['source_id'], ['account_sources_view'])

        self.add_permission_and_test(Level.AD_GROUPS, ['publisher_id'], ['can_see_publishers'])

    def test_breakdown_validate_by_delivery_permissions(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['all_accounts_accounts_view'])

        with self.assertRaises(exc.MissingDataError):
            permission_filter.validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ['account_id', 'dma'])

        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['all_accounts_accounts_view', 'can_view_breakdown_by_delivery'])

        permission_filter.validate_breakdown_by_permissions(Level.ALL_ACCOUNTS, user, ['account_id', 'dma'])

    def test_validate_breakdown_structure(self):
        # should succeed, no exception
        permission_filter.validate_breakdown_by_structure(['account_id', 'campaign_id', 'device_type', 'week'])
        permission_filter.validate_breakdown_by_structure(['account_id'])
        permission_filter.validate_breakdown_by_structure([])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Unsupported breakdowns: bla"):
            permission_filter.validate_breakdown_by_structure(['account_id', 'bla', 'device_type'])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
            permission_filter.validate_breakdown_by_structure(['account_id', 'day', 'device_type'])
