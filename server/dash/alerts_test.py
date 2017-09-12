import mock

from django.http.request import HttpRequest
from django.test import TestCase, override_settings

import dash.alerts
from dash import models
from dash import constants
from zemauth.models import User


@override_settings(ALLOWED_HOSTS=['testname'])
class AccountLandingModeAlertsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        normal_user = User.objects.get(id=2)
        self.request = HttpRequest()
        self.request.META['SERVER_NAME'] = 'testname'
        self.request.META['SERVER_PORT'] = 1234
        self.request.user = normal_user

        superuser = User.objects.get(id=1)
        self.superuser_request = HttpRequest()
        self.superuser_request.META['SERVER_NAME'] = 'testname'
        self.superuser_request.META['SERVER_PORT'] = 1234
        self.superuser_request.user = superuser

        self.account = models.Account.objects.get(id=1)
        self.campaign = self.account.campaign_set.get(id=1)

    @mock.patch('automation.campaign_stop.is_campaign_running_out_of_budget')
    def test_landing_campaign(self, mock_out_of_budget):
        mock_out_of_budget.return_value = False
        new_campaign_settings = self.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        alerts = dash.alerts.get_account_landing_mode_alerts(self.request, self.account)
        self.assertEqual(0, len(alerts))

        alerts = dash.alerts.get_account_landing_mode_alerts(self.superuser_request, self.account)
        self.assertEqual(1, len(alerts))
        self.assertEqual(constants.AlertType.INFO, alerts[0]['type'])
        self.assertTrue(self.campaign.name in alerts[0]['message'])

    @mock.patch('automation.campaign_stop.is_campaign_running_out_of_budget')
    def test_depleting_budget_campaigns(self, mock_out_of_budget):
        def _mock_out_of_budget(campaign, campaign_settings):
            if campaign.id == self.campaign.id:
                return True
            return False

        mock_out_of_budget.side_effect = _mock_out_of_budget

        alerts = dash.alerts.get_account_landing_mode_alerts(self.request, self.account)
        self.assertEqual(0, len(alerts))

        alerts = dash.alerts.get_account_landing_mode_alerts(self.superuser_request, self.account)
        self.assertEqual(1, len(alerts))
        self.assertEqual(constants.AlertType.WARNING, alerts[0]['type'])
        self.assertTrue(self.campaign.name in alerts[0]['message'])


@override_settings(ALLOWED_HOSTS=['testname'])
class CampaignLandingModeAlertsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        normal_user = User.objects.get(id=2)
        self.request = HttpRequest()
        self.request.META['SERVER_NAME'] = 'testname'
        self.request.META['SERVER_PORT'] = 1234
        self.request.user = normal_user

        superuser = User.objects.get(id=1)
        self.superuser_request = HttpRequest()
        self.superuser_request.META['SERVER_NAME'] = 'testname'
        self.superuser_request.META['SERVER_PORT'] = 1234
        self.superuser_request.user = superuser

        self.campaign = models.Campaign.objects.get(id=1)

    @mock.patch('automation.campaign_stop.is_campaign_running_out_of_budget')
    def test_landing_campaign(self, mock_out_of_budget):
        mock_out_of_budget.return_value = False
        new_campaign_settings = self.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        alerts = dash.alerts.get_campaign_landing_mode_alerts(self.request, self.campaign)
        self.assertEqual(0, len(alerts))

        alerts = dash.alerts.get_campaign_landing_mode_alerts(self.superuser_request, self.campaign)
        self.assertEqual(1, len(alerts))
        self.assertEqual(constants.AlertType.INFO, alerts[0]['type'])

    @mock.patch('automation.campaign_stop.is_campaign_running_out_of_budget')
    def test_depleting_budget_campaigns(self, mock_out_of_budget):
        def _mock_out_of_budget(campaign, campaign_settings):
            if campaign.id == self.campaign.id:
                return True
            return False

        mock_out_of_budget.side_effect = _mock_out_of_budget

        alerts = dash.alerts.get_campaign_landing_mode_alerts(self.request, self.campaign)
        self.assertEqual(0, len(alerts))

        alerts = dash.alerts.get_campaign_landing_mode_alerts(self.superuser_request, self.campaign)
        self.assertEqual(1, len(alerts))
        self.assertEqual(constants.AlertType.WARNING, alerts[0]['type'])
