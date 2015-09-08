from django.core import mail
from django import test
from mock import patch
from automation import budgetdepletion
from dash import models
from reports import refresh
from django.conf import settings
from automation import models as automationmodels


class BudgetDepletionTestCase(test.TestCase):
    fixtures = ['test_budget_depletion.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    def test_get_active_campaigns(self):
        campaigns = budgetdepletion.get_active_campaigns()
        self.assertEqual(campaigns.filter(pk=1).count(), 1)

    def test_get_active_campaigns_subset(self):
        campaigns = models.Campaign.objects.all()
        actives = budgetdepletion._get_active_campaigns_subset(campaigns)
        self.assertEqual(actives.filter(pk=1).count(), 1)
        self.assertEqual(actives.filter(pk=2).count(), 0)

    @patch("django.conf.settings.DEPLETING_AVAILABLE_BUDGET_SCALAR", 1.0)
    def test_budget_is_depleting(self):
        self.assertEqual(budgetdepletion.budget_is_depleting(100, 5), False)
        self.assertEqual(budgetdepletion.budget_is_depleting(100, 500), True)
        self.assertEqual(budgetdepletion.budget_is_depleting(-100, 5), True)

    @patch("automation.budgetdepletion._send_depleted_budget_notification_email")
    def test_notify_campaign_with_depleting_budget(self, _):
        budgetdepletion.notify_campaign_with_depleting_budget(
            models.Campaign.objects.get(pk=1),
            100,
            150
        )
        notif = automationmodels.CampaignBudgetDepletionNotification.objects.all().latest('created_dt')
        self.assertEqual(notif.campaign, models.Campaign.objects.get(pk=1))
        self.assertEqual(notif.available_budget, 100)
        self.assertEqual(notif.yesterdays_spend, 150)

    @patch("automation.budgetdepletion._send_depleted_budget_notification_email")
    def test_manager_has_been_notified(self, _):
        camp = models.Campaign.objects.get(pk=1)
        self.assertEqual(budgetdepletion.manager_has_been_notified(camp), False)

        budgetdepletion.notify_campaign_with_depleting_budget(camp, 100, 150)
        self.assertEqual(budgetdepletion.manager_has_been_notified(camp), True)

    def test_send_depleted_budget_notification_email(self):
        budgetdepletion._send_depleted_budget_notification_email(
            'campaign_name',
            'campaign_url',
            'account_name',
            ['test@zemanta.com']
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(
            settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL)
        )
        self.assertEqual(mail.outbox[0].to, ['test@zemanta.com'])
