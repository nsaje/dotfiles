import decimal
from datetime import datetime

from django import test
from django.core import mail
from django.http.request import HttpRequest
from mock import patch

from automation import models as automationmodels
from dash import models
from zemauth.models import User

from . import simple


class DatetimeMock(datetime):
    @classmethod
    def utcnow(cls):
        return datetime(2014, 6, 5, 9, 58, 25)


class BudgetDepletionTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    def test_get_active_campaigns(self):
        campaigns = simple._get_active_campaigns()
        self.assertEqual(len([c for c in campaigns if c.pk == 1]), 1)

    def test_get_active_campaigns_subset(self):
        campaigns = models.Campaign.objects.all()
        actives = simple._get_active_campaigns_subset(campaigns)
        self.assertEqual(len([c for c in actives if c.pk == 1]), 1)
        self.assertEqual(len([c for c in actives if c.pk == 2]), 0)

    @patch("automation.campaignstop.service.simple.DEPLETING_AVAILABLE_BUDGET_SCALAR", 1.0)
    def test_budget_is_depleting(self):
        self.assertEqual(simple._budget_is_depleting(100, 5), False)
        self.assertEqual(simple._budget_is_depleting(100, 500), True)
        self.assertEqual(simple._budget_is_depleting(-100, 5), True)

    @patch("automation.campaignstop.service.simple._send_depleting_budget_notification_email")
    def test_notify_campaign_with_depleting_budget(self, mock):
        campaign = models.Campaign.objects.get(pk=1)
        user = User.objects.create_user("accountmanager@test.com")
        campaign.account.settings.update(None, default_account_manager=user)
        simple._notify_campaign_with_depleting_budget(campaign, 100, 150)

        notif = automationmodels.CampaignBudgetDepletionNotification.objects.all().latest("created_dt")
        self.assertEqual(notif.campaign, models.Campaign.objects.get(pk=1))
        self.assertEqual(notif.available_budget, 100)
        self.assertEqual(notif.yesterdays_spend, 150)

        mock.assert_called_with(
            campaign,
            "https://one.zemanta.com/v2/analytics/campaign/1?settings&settingsScrollTo=zemCampaignBudgetsSettings",
            ["accountmanager@test.com", "em@il.com"],
            100,
            150,
            decimal.Decimal("60.0000"),
        )

    @patch("automation.campaignstop.service.simple._send_depleting_budget_notification_email")
    def test_manager_has_been_notified(self, _):
        camp = models.Campaign.objects.get(pk=1)
        self.assertEqual(simple._manager_has_been_notified(camp), False)

        simple._notify_campaign_with_depleting_budget(camp, 100, 150)
        self.assertEqual(simple._manager_has_been_notified(camp), True)

    def test_send_depleting_budget_notification_email(self):
        campaign = models.Campaign.objects.get(pk=1)

        simple._send_depleting_budget_notification_email(
            campaign, "campaign_url", ["test@zemanta.com"], 1000, 1500, 5000
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(simple.DEPLETING_CAMPAIGN_BUDGET_EMAIL))
        self.assertEqual(mail.outbox[0].to, ["test@zemanta.com"])

    def test_send_campaign_stopped_notification_email(self):
        campaign = models.Campaign.objects.get(pk=1)
        simple._send_campaign_stopped_notification_email(campaign, "campaign_url", ["test@zemanta.com"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(simple.DEPLETING_CAMPAIGN_BUDGET_EMAIL))
        self.assertEqual(mail.outbox[0].to, ["test@zemanta.com"])

    def test_get_active_ad_groups(self):
        campaign1 = models.Campaign.objects.get(id=1)
        actives = simple._get_active_ad_groups(campaign1)
        self.assertEqual(len(actives), 1)

        campaign2 = models.Campaign.objects.get(id=2)
        actives = simple._get_active_ad_groups(campaign2)
        self.assertEqual(len(actives), 0)

    def test_get_active_ad_group_sources_settings(self):
        adg1 = models.AdGroup.objects.get(id=1)
        actives = simple._get_active_ad_group_sources_settings(adg1)
        self.assertEqual(len(actives), 1)

        adg2 = models.AdGroup.objects.get(id=2)
        actives2 = simple._get_active_ad_group_sources_settings(adg2)
        self.assertEqual(len(actives2), 1)

    def test_get_total_daily_budget_amount(self):
        camp1 = models.Campaign.objects.get(id=1)
        self.assertEqual(simple._get_total_daily_budget_amount(camp1), decimal.Decimal("60"))

        camp2 = models.Campaign.objects.get(id=2)
        self.assertEqual(simple._get_total_daily_budget_amount(camp2), decimal.Decimal("0"))

    def test_stop_campaign(self):
        camp = models.Campaign.objects.get(id=1)
        self.assertTrue(len(simple._get_active_ad_groups(camp)) > 0)
        simple._stop_campaign(camp)
        self.assertEqual(len(simple._get_active_ad_groups(camp)), 0)


class BCMDepletionTestCase(test.TestCase):

    fixtures = ["test_automation.yaml"]

    def setUp(self):
        self.campaigns = models.Campaign.objects.all()
        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=1)

    @patch("datetime.datetime", DatetimeMock)
    def test_get_yesterdays_spends(self):
        self.assertEqual(
            simple._get_yesterdays_spends(self.campaigns),
            {
                1: decimal.Decimal("0.0"),
                2: decimal.Decimal("0.0"),
                3: decimal.Decimal("55.0"),
                4: decimal.Decimal("77.0"),
            },
        )

    @patch("datetime.datetime", DatetimeMock)
    def test_get_available_budgets(self):
        self.assertEqual(
            simple._get_available_budgets(self.campaigns),
            {
                1: decimal.Decimal("0.0"),
                2: decimal.Decimal("100.0000"),
                3: decimal.Decimal("49879.0000"),
                4: decimal.Decimal("49923.0000"),
            },
        )
