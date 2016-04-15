import decimal
from datetime import datetime
import operator
from mock import patch

from django.core import mail
from django import test
from django.http.request import HttpRequest

from automation import budgetdepletion, helpers
from automation import models as automationmodels
from dash import models
from reports import refresh
import automation.settings
import automation.constants
import automation.autopilot_budgets

from zemauth.models import User


class DatetimeMock(datetime):

    @classmethod
    def utcnow(cls):
        return datetime(2014, 6, 5, 9, 58, 25)


class BudgetDepletionTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    def test_get_active_campaigns(self):
        campaigns = helpers.get_active_campaigns()
        self.assertEqual(campaigns.filter(pk=1).count(), 1)

    def test_get_active_campaigns_subset(self):
        campaigns = models.Campaign.objects.all()
        actives = helpers._get_active_campaigns_subset(campaigns)
        self.assertEqual(actives.filter(pk=1).count(), 1)
        self.assertEqual(actives.filter(pk=2).count(), 0)

    @patch("automation.settings.DEPLETING_AVAILABLE_BUDGET_SCALAR", 1.0)
    def test_budget_is_depleting(self):
        self.assertEqual(budgetdepletion.budget_is_depleting(100, 5), False)
        self.assertEqual(budgetdepletion.budget_is_depleting(100, 500), True)
        self.assertEqual(budgetdepletion.budget_is_depleting(-100, 5), True)

    @patch("automation.budgetdepletion._send_depleting_budget_notification_email")
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

    @patch("automation.budgetdepletion._send_depleting_budget_notification_email")
    def test_manager_has_been_notified(self, _):
        camp = models.Campaign.objects.get(pk=1)
        self.assertEqual(budgetdepletion.manager_has_been_notified(camp), False)

        budgetdepletion.notify_campaign_with_depleting_budget(camp, 100, 150)
        self.assertEqual(budgetdepletion.manager_has_been_notified(camp), True)

    def test_send_depleting_budget_notification_email(self):
        budgetdepletion._send_depleting_budget_notification_email(
            'campaign_name',
            'campaign_url',
            'account_name',
            ['test@zemanta.com'],
            1000,
            1500,
            5000
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(
            automation.settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL)
        )
        self.assertEqual(mail.outbox[0].to, ['test@zemanta.com'])

    def test_send_campaign_stopped_notification_email(self):
        budgetdepletion._send_campaign_stopped_notification_email(
            'campaign_name',
            'campaign_url',
            'account_name',
            ['test@zemanta.com']
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(
            automation.settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL)
        )
        self.assertEqual(mail.outbox[0].to, ['test@zemanta.com'])

    def test_get_active_ad_groups(self):
        campaign1 = models.Campaign.objects.get(id=1)
        actives = helpers.get_active_ad_groups(campaign1)
        self.assertEqual(len(actives), 1)

        campaign2 = models.Campaign.objects.get(id=2)
        actives = helpers.get_active_ad_groups(campaign2)
        self.assertEqual(len(actives), 0)

    def test_get_active_ad_group_sources_settings(self):
        adg1 = models.AdGroup.objects.get(id=1)
        actives = helpers.get_active_ad_group_sources_settings(adg1)
        self.assertEqual(len(actives), 1)

        adg2 = models.AdGroup.objects.get(id=2)
        actives2 = helpers.get_active_ad_group_sources_settings(adg2)
        self.assertEqual(len(actives2), 1)

    def test_get_total_daily_budget_amount(self):
        camp1 = models.Campaign.objects.get(id=1)
        self.assertEqual(helpers.get_total_daily_budget_amount(camp1), decimal.Decimal('60'))

        camp2 = models.Campaign.objects.get(id=2)
        self.assertEqual(helpers.get_total_daily_budget_amount(camp2), decimal.Decimal('0'))

    def test_stop_campaign(self):
        camp = models.Campaign.objects.get(id=1)
        self.assertTrue(len(helpers.get_active_ad_groups(camp)) > 0)
        helpers.stop_campaign(camp)
        self.assertEqual(len(helpers.get_active_ad_groups(camp)), 0)


class BCMDepletionTestCase(test.TestCase):

    fixtures = ['test_automation.yaml']

    def setUp(self):
        self.campaigns = models.Campaign.objects.all()
        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=1)
        refresh.refresh_adgroup_stats()

    @patch('datetime.datetime', DatetimeMock)
    def test_get_yesterdays_spends(self):
        self.assertEqual(
            helpers.get_yesterdays_spends(self.campaigns),
            {
                1: decimal.Decimal('0.0'),
                2: decimal.Decimal('0.0'),
                3: decimal.Decimal('55.0'),
                4: decimal.Decimal('77.0')
            },
        )

    @patch('datetime.datetime', DatetimeMock)
    def test_get_available_budgets(self):
        with patch('reports.api.query') as query:
            query.return_value = {'cost': 200.0}
            self.assertEqual(
                helpers.get_available_budgets(self.campaigns),
                {
                    1: decimal.Decimal('0.0'),
                    2: decimal.Decimal('100.0000'),
                    3: decimal.Decimal('49879.0000'),
                    4: decimal.Decimal('49923.0000')
                },
            )


class BetaBanditTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    def test_naiive(self):
        ags = models.AdGroupSource.objects.filter(ad_group=4)
        self.assertEqual(ags.count(), 3)

        bandit = automation.autopilot_budgets.BetaBandit([a for a in ags])

        for i in range(100):
            bandit.add_result(ags[0], True)

        recommendations = {s: 0 for s in ags}
        for i in range(100):
            recommendations[bandit.get_recommendation()] += 1

        most_recommended = max(recommendations.iteritems(), key=operator.itemgetter(1))[0]
        self.assertEqual(most_recommended, ags[0])
