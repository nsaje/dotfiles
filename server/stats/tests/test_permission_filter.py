from django.test import TestCase

from utils import test_helper
from utils import exc
from zemauth.models import User

from dash import models
from dash import campaign_goals
from dash.constants import Level

from stats import permission_filter
from stats.helpers import Goals

from reports import api_helpers


class FilterTestCase(TestCase):

    fixtures = ['test_augmenter', 'test_non_superuser']

    def setUp(self):
        self.campaign = models.Campaign.objects.get(pk=1)

        # all the fields that can be put into a row
        row = {
            'ad_group_id': 1, 'source_id': 1, 'clicks': 10, 'age': '18-20',
            'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
            'name': 'test adgroup 1', 'e_yesterday_cost': 1, 'yesterday_cost': 1, 'cpm': 1,
            'min_bid_cpc': 1, 'max_bid_cpc': 1, 'daily_budget': 1,
            'campaign_stop_inactive': 1, 'campaign_has_available_budget': 1,
            'pacing': 1, 'allocated_budgets': 1, 'spend_projection': 1, 'license_fee_projection': 1,
            'flat_fee': 1, 'total_fee': 1, 'total_fee_projection': 1,
            'agency': 1, 'default_account_manager': 1, 'default_sales_representative': 1, 'campaign_manager': 1,
        }

        # add all possible fields
        row.update({x: 1 for x in api_helpers.TRAFFIC_FIELDS})
        row.update({x: 1 for x in api_helpers.POSTCLICK_ACQUISITION_FIELDS})
        row.update({x: 1 for x in api_helpers.POSTCLICK_ENGAGEMENT_FIELDS})
        row.update({x: 1 for x in api_helpers.GOAL_FIELDS})

        for field in api_helpers.FIELD_PERMISSION_MAPPING.keys():
            if field not in row:
                row[field] = 1

        self.conversion_goals = self.campaign.conversiongoal_set.all()
        self.campaign_goal_values = campaign_goals.get_campaign_goal_values(self.campaign)
        self.pixels = self.campaign.account.conversionpixel_set.all()

        for x in self.conversion_goals:
            row[x.get_view_key(self.conversion_goals)] = 1
            row['avg_cost_per_{}'.format(x.get_view_key(self.conversion_goals))] = 1

        for x in self.pixels:
            for window in [24, 168, 720, 2160]:
                row[x.get_view_key(window)] = 1
                row['avg_cost_per_{}'.format(x.get_view_key(window))] = 1

        for x in self.campaign_goal_values:
            row['performance_' + x.campaign_goal.get_view_key()] = 1

        # just check we actually inserted something
        self.assertIn('pixel_1_168', row)
        self.assertIn('conversion_goal_2', row)
        self.assertIn('performance_campaign_goal_1', row)

        self.rows = [row]
        self.default_cleaned_rows = [
            {
                'ad_group_id': 1, 'source_id': 1, 'name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
                'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
                'clicks': 1, 'ctr': 1, 'cpc': 1, 'impressions': 1, 'billing_cost': 1, 'avg_cost_per_visit': 1,
                'avg_cost_per_pageview': 1, 'avg_cost_per_minute': 1, 'avg_cost_per_non_bounced_visit': 1,
                'avg_cost_for_new_visitor': 1, 'cpm': 1,
                'title': 1, 'url': 1,  # these two are in TRAFFIC_FIELDS
                'pixel_1_24': 1, 'pixel_1_168': 1, 'pixel_1_720': 1, 'pixel_1_2160': 1,
                'avg_cost_per_pixel_1_24': 1, 'avg_cost_per_pixel_1_168': 1, 'avg_cost_per_pixel_1_720': 1,
                'avg_cost_per_pixel_1_2160': 1,
                'min_bid_cpc': 1, 'max_bid_cpc': 1, 'daily_budget': 1,
                'campaign_stop_inactive': 1, 'campaign_has_available_budget': 1,
                'archived': 1, 'maintenance': 1,
            },
        ]

        self.goals = Goals(
            [x.campaign_goal for x in self.campaign_goal_values],  # campaign goals without values can exist
            self.conversion_goals, self.campaign_goal_values, self.pixels,
            self.campaign_goal_values[0].campaign_goal
        )

    def test_user_not_superuser(self):
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_superuser)

    def test_filter_columns_by_permission_no_perm(self):
        user = User.objects.get(pk=1)

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        # only default field should be left
        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_effective_cost(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['can_view_platform_cost_breakdown'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'license_fee': 1, 'e_media_cost': 1,
            'e_data_cost': 1, 'e_yesterday_cost': 1,
        })

        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_campaign_goal_optimization(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['campaign_goal_optimization'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'avg_cost_per_pixel_1_168': 1, 'avg_cost_per_conversion_goal_2': 1,
            'avg_cost_per_conversion_goal_4': 1, 'avg_cost_per_conversion_goal_5': 1,
            'avg_cost_per_conversion_goal_3': 1,
        })

        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_campaign_goal_performance(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['campaign_goal_performance'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'performance_campaign_goal_1': 1,
            'performance_campaign_goal_2': 1,
            'performance': 1, 'styles': 1,  # TODO legacy fields, not to be inserted at this level
        })

        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_conversion_goals(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['can_see_redshift_postclick_statistics'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'pixel_1_168': 1, 'conversion_goal_2': 1,
            'conversion_goal_4': 1, 'conversion_goal_5': 1,
            'conversion_goal_3': 1,
        })

        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_projections(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(
            user,
            ('can_see_projections', 'can_view_platform_cost_breakdown', 'can_view_flat_fees'))

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'pacing': 1, 'allocated_budgets': 1, 'spend_projection': 1, 'license_fee_projection': 1,
            'flat_fee': 1, 'total_fee': 1, 'total_fee_projection': 1,
            'e_data_cost': 1, 'e_media_cost': 1, 'e_yesterday_cost': 1, 'license_fee': 1,
        })
        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_agency(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['can_view_account_agency_information'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'agency': 1,
        })
        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_managers(self):
        user = User.objects.get(pk=1)
        test_helper.add_permissions(user, ['can_see_managers_in_accounts_table', 'can_see_managers_in_campaigns_table'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.goals)

        self.default_cleaned_rows[0].update({
            'default_account_manager': 1, 'default_sales_representative': 1, 'campaign_manager': 1,
        })
        self.assertItemsEqual(self.rows, self.default_cleaned_rows)


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

        self.add_permission_and_test(Level.AD_GROUPS, ['publisher'], ['can_see_publishers'])

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

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Unsupported breakdowns set(['bla'])"):
            permission_filter.validate_breakdown_by_structure(['account_id', 'bla', 'device_type'])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
            permission_filter.validate_breakdown_by_structure(['account_id', 'day', 'device_type'])
