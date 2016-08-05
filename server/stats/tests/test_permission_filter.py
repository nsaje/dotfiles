from django.test import TestCase

from utils.test_helper import add_permissions
from zemauth.models import User

from dash import models
from dash import campaign_goals

from stats import permission_filter

from reports import api_helpers


class FilterTestCase(TestCase):

    fixtures = ['test_augmenter', 'test_non_superuser']

    def setUp(self):
        self.campaign = models.Campaign.objects.get(pk=1)

        row = {
            'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
            'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
            'e_yesterday_cost': 1, 'yesterday_cost': 1,
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

        for x in self.conversion_goals:
            row[x.get_view_key(self.conversion_goals)] = 1
            row['avg_cost_per_{}'.format(x.get_view_key(self.conversion_goals))] = 1

        # just check we actually inserted something
        self.assertIn('conversion_goal_1', row)

        self.rows = [row]
        self.default_cleaned_rows = [
            {
                'ad_group_id': 1, 'source_id': 1, 'ad_group_name': 'test adgroup 1', 'clicks': 10, 'age': '18-20',
                'breakdown_id': '1||1', 'breakdown_name': 'test adgroup 1', 'parent_breakdown_id': '1',
                'clicks': 1, 'ctr': 1, 'cpc': 1, 'impressions': 1, 'billing_cost': 1, 'avg_cost_per_visit': 1,
                'avg_cost_per_pageview': 1, 'avg_cost_per_minute': 1, 'avg_cost_per_non_bounced_visit': 1,
                'avg_cost_for_new_visitor': 1,
                'title': 1, 'url': 1,  # these two are in TRAFFIC_FIELDS
            },
        ]

    def test_user_not_superuser(self):
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_superuser)

    def test_filter_columns_by_permission_no_perm(self):
        user = User.objects.get(pk=1)

        permission_filter.filter_columns_by_permission(user, self.rows, self.campaign_goal_values, self.conversion_goals)

        # only default field should be left
        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_effective_cost(self):
        user = User.objects.get(pk=1)
        add_permissions(user, ['can_view_platform_cost_breakdown'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.campaign_goal_values, self.conversion_goals)

        self.default_cleaned_rows[0].update({
            'license_fee': 1, 'e_media_cost': 1,
            'e_data_cost': 1, 'e_yesterday_cost': 1,
        })

        self.maxDiff = None
        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_campaign_goal_optimization(self):
        user = User.objects.get(pk=1)
        add_permissions(user, ['campaign_goal_optimization'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.campaign_goal_values, self.conversion_goals)

        self.maxDiff = None
        self.default_cleaned_rows[0].update({
            'avg_cost_per_conversion_goal_1': 1, 'avg_cost_per_conversion_goal_2': 1,
            'avg_cost_per_conversion_goal_4': 1, 'avg_cost_per_conversion_goal_5': 1,
            'avg_cost_per_conversion_goal_3': 1,
        })

        self.assertItemsEqual(self.rows, self.default_cleaned_rows)

    def test_filter_columns_by_permission_conversion_goals(self):
        user = User.objects.get(pk=1)
        add_permissions(user, ['can_see_redshift_postclick_statistics'])

        permission_filter.filter_columns_by_permission(user, self.rows, self.campaign_goal_values, self.conversion_goals)

        self.default_cleaned_rows[0].update({
            'conversion_goal_1': 1, 'conversion_goal_2': 1,
            'conversion_goal_4': 1, 'conversion_goal_5': 1,
            'conversion_goal_3': 1,
        })

        self.assertItemsEqual(self.rows, self.default_cleaned_rows)
