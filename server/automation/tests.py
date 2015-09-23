import decimal
import dash
import datetime
from mock import patch

from django.core import mail
from django import test

from automation import budgetdepletion, helpers, autopilot
from automation import models as automationmodels
from dash import models
from reports import refresh
import automation.settings


class DatetimeMock(datetime.datetime):
    @classmethod
    def utcnow(cls):
        return datetime.datetime(2014, 06, 05, 9, 58, 25)


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

    def test_get_active_ad_groups(self):
            campaign1 = models.Campaign.objects.get(id=1)
            actives = helpers.get_active_ad_groups(campaign1)
            self.assertEqual(len(actives), 1)

            campaign2 = models.Campaign.objects.get(id=2)
            actives = helpers.get_active_ad_groups(campaign2)
            self.assertEqual(len(actives), 0)

    def test_persist_cpc_change_to_admin_log(self):
        autopilot.persist_cpc_change_to_admin_log(
            models.AdGroupSource.objects.get(id=1),
            20.0,
            0.15,
            0.20,
            30.0,
            5
        )
        log = automationmodels.AutopilotAdGroupSourceBidCpcLog.objects.all().latest('created_dt')
        self.assertEqual(log.campaign, models.Campaign.objects.get(pk=1))
        self.assertEqual(log.ad_group, models.AdGroup.objects.get(pk=1))
        self.assertEqual(log.ad_group_source, models.AdGroupSource.objects.get(pk=1))
        self.assertEqual(log.yesterdays_spend_cc, 20.0)
        self.assertEqual(log.previous_cpc_cc, decimal.Decimal('0.15'))
        self.assertEqual(log.new_cpc_cc, decimal.Decimal('0.20'))
        self.assertEqual(log.current_daily_budget_cc, 30.0)

    @patch('datetime.datetime', DatetimeMock)
    def test_ad_group_sources_daily_budget_was_changed_recently(self):
        self.assertTrue(autopilot.ad_group_sources_daily_budget_was_changed_recently(models.AdGroupSource.objects.get(id=1)))

        self.assertFalse(autopilot.ad_group_sources_daily_budget_was_changed_recently(models.AdGroupSource.objects.get(id=2)))
        settings_writer = dash.api.AdGroupSourceSettingsWriter(models.AdGroupSource.objects.get(id=2))
        resource = dict()
        resource['daily_budget_cc'] = decimal.Decimal(60.00)
        settings_writer.set(resource, None)
        self.assertTrue(autopilot.ad_group_sources_daily_budget_was_changed_recently(models.AdGroupSource.objects.get(id=2)))

    @patch('automation.settings.AUTOPILOT_CPC_CHANGE_TABLE', (
        {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.5, 'bid_cpc_procentual_increase': 0.1},
        {'underspend_upper_limit': -0.5, 'underspend_lower_limit': -0.1, 'bid_cpc_procentual_increase': 0.5},
        {'underspend_upper_limit': -0.1, 'underspend_lower_limit': 0, 'bid_cpc_procentual_increase': -0.5}
        )
    )
    @patch('automation.settings.AUTOPILOT_MIN_CPC', decimal.Decimal('0.1'))
    @patch('automation.settings.AUTOPILOT_MAX_CPC', decimal.Decimal('3'))
    @patch('automation.settings.AUTOPILOT_MIN_LOWERING_CPC_CHANGE', decimal.Decimal('0.2'))
    @patch('automation.settings.AUTOPILOT_MAX_LOWERING_CPC_CHANGE', decimal.Decimal('0.3'))
    def test_calculate_new_autopilot_cpc(self):
        test_cases = {
            #  cpc, daily_budget, yesterday_spend, new_cpc
            ('0', '10', '5', '0'),
            ('0.5', '10', '8', '0.75'),
            ('0.5', '10', '10', '0.25'),
            ('0.5', '10', '2', '0.56'),
            ('0.5', '10', '0', '0.5'),
            ('0.5', '10', '5', '0.56'),
            ('0.5', '0', '5', '0.5'),
            ('0.5', '10', '0', '0.5'),
            ('0.5', '-10', '5', '0.5'),
            ('0.5', '10', '-5', '0.5'),
            ('-0.5', '10', '5', '0'),
            ('0.35', '10', '9.96', '0.15'),
            ('2.8', '10', '9.96', '2.5'),
            ('3.5', '10', '1', '3.5'),
            ('0.05', '10', '1', '0.05')
        }
        for test_case in test_cases:
            self.assertEqual(autopilot.calculate_new_autopilot_cpc(
                decimal.Decimal(test_case[0]),
                decimal.Decimal(test_case[1]),
                decimal.Decimal(test_case[2])),
                decimal.Decimal(test_case[3]))

    def test_send_autopilot_CPC_changes_email(self):
        autopilot.send_autopilot_CPC_changes_email(
            'campaign_name',
            1,
            'account_name',
            ['test@zemanta.com'],
            {(u'Adgroup', 109): [{
                'old_cpc': decimal.Decimal('0.1800'),
                'source_name': u'source',
                'new_cpc': decimal.Decimal('0.21')}
            ]}
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(
            automation.settings.AUTOPILOT_EMAIL)
        )
        self.assertEqual(mail.outbox[0].to, ['test@zemanta.com'])

    def test_get_active_ad_group_sources_settings(self):
            adg1 = models.AdGroup.objects.get(id=1)
            actives = helpers.get_active_ad_group_sources_settings(adg1)
            self.assertEqual(len(actives), 1)

            adg2 = models.AdGroup.objects.get(id=2)
            actives2 = helpers.get_active_ad_group_sources_settings(adg2)
            self.assertEqual(len(actives2), 1)

    def test_get_autopilot_ad_group_sources_settings(self):
            adg1 = models.AdGroup.objects.get(id=1)
            actives = autopilot.get_autopilot_ad_group_sources_settings(adg1)
            self.assertEqual(len(actives), 0)

            adg2 = models.AdGroup.objects.get(id=2)
            actives2 = autopilot.get_autopilot_ad_group_sources_settings(adg2)
            self.assertEqual(len(actives2), 1)

    def test_ad_group_source_is_on_autopilot(self):
            adgs1 = models.AdGroupSource.objects.get(id=1)
            self.assertFalse(autopilot.ad_group_source_is_on_autopilot(adgs1))

            adgs2 = models.AdGroupSource.objects.get(id=2)
            self.assertTrue(autopilot.ad_group_source_is_on_autopilot(adgs2))

    def test_get_total_daily_budget_amount(self):
            camp1 = models.Campaign.objects.get(id=1)
            self.assertEqual(helpers.get_total_daily_budget_amount(camp1), decimal.Decimal('60'))

            camp2 = models.Campaign.objects.get(id=2)
            self.assertEqual(helpers.get_total_daily_budget_amount(camp2), decimal.Decimal('0'))
