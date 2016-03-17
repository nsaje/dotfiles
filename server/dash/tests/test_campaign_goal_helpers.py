from mock import patch
from django.test import TestCase


class CampaignGoalHelpersTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def test_create_goals(self):
        # campaign, data, cost):
        pass

    def test_create_goal_totals(self):
        # (campaign, data, cost):
        pass

    def test_get_campaign_goal_values(self):
        # campaign):
        pass

    def test_calculate_goal_values(self):
        # row, goal_type, cost):
        pass

    def test_calculate_goal_total_values(self):
        # row, goal_type, cost):
        pass

    def test_get_campaign_goals(self):
        # campaign):
        pass
