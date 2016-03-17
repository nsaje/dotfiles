from django.test import TestCase
from decimal import Decimal

import dash.constants
import dash.models
import zemauth.models
import dash.campaign_goal_helpers


class CampaignGoalHelpersTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        # make up some goals
        self.campaign = dash.models.Campaign.objects.get(pk=1)
        self.user = zemauth.models.User.objects.get(pk=1)

        all_goal_types = dash.constants.CampaignGoalKPI.get_all()
        for goal_type in all_goal_types:
            dash.models.CampaignGoal.objects.create(
                campaign=self.campaign,
                type=goal_type,
                created_by=self.user,
            )

    def _goal(self, goal_type):
        return dash.models.CampaignGoal.objects.filter(
            type=goal_type
        ).first()

    def _add_value(self, goal_type, value):
        goal = self._goal(goal_type)
        dash.models.CampaignGoalValue.objects.create(
            campaign_goal=goal,
            value=Decimal(value),
            created_by=self.user
        )

    def test_create_goals(self):
        # campaign, data, cost):
        pass

    def test_create_goal_totals(self):
        # (campaign, data, cost):
        pass

    def test_get_campaign_goal_values(self):
        self._add_value(dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.1)
        self._add_value(dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.5)
        self._add_value(dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.75)

        values = dash.campaign_goal_helpers.get_campaign_goal_values(self.campaign)
        self.assertEqual(0.75, values[0].value)

        self._add_value(dash.constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(dash.constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        values = dash.campaign_goal_helpers.get_campaign_goal_values(
            self.campaign
        ).values_list('value', flat=True)
        self.assertItemsEqual([0.75, 5, 60], values)

    def test_calculate_goal_values(self):
        # row, goal_type, cost):
        pass

    def test_calculate_goal_total_values(self):
        # row, goal_type, cost):
        pass

    def test_get_campaign_goals(self):
        self._add_value(dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.75)
        self._add_value(dash.constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(dash.constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        campaign_goals = dash.campaign_goal_helpers.get_campaign_goals(self.campaign)

        result = [
            {
                'name': 'time on site in seconds',
                'value': 60,
                'fields': {'total_seconds': True, 'avg_cost_per_second': True},
            },
            {
                'name': 'pages per session',
                'value': 5,
                'fields': {'total_pageviews': True, 'avg_cost_per_pageview': True},
            },
            {
                'name': 'max bounce rate %',
                'value': 0.75,
                'fields': {'unbounced_visits': True, 'avg_cost_per_non_bounced_visitor': True},
            }
        ]

        self.assertItemsEqual(result, campaign_goals)
