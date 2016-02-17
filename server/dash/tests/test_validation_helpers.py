from mock import patch

from django.test import TestCase

from dash import validation_helpers
from dash.models import AdGroup


@patch('dash.validation_helpers.budget.CampaignBudget.get_total')
@patch('dash.validation_helpers.budget.CampaignBudget.get_spend')
class ValidationHelpersTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_ad_group_has_available_budget(self, mock_get_spend, mock_get_total):
        ad_group = AdGroup.objects.get(pk=1)

        mock_get_total.return_value = 50
        mock_get_spend.return_value = 40
        has_budget = validation_helpers.ad_group_has_available_budget(ad_group)
        self.assertTrue(has_budget)

        mock_get_total.return_value = 30
        mock_get_spend.return_value = 40
        has_budget = validation_helpers.ad_group_has_available_budget(ad_group)
        self.assertFalse(has_budget)

        mock_get_total.return_value = 40
        mock_get_spend.return_value = 40
        has_budget = validation_helpers.ad_group_has_available_budget(ad_group)
        self.assertFalse(has_budget)
