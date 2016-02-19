import decimal
import dash
import datetime
import operator
from mock import patch

from django.core import mail
from django import test
from django.http.request import HttpRequest

from automation import budgetdepletion, helpers, autopilot
from automation import models as automationmodels
from dash import models
from reports import refresh
import automation.settings
import automation.constants
import automation.autopilot_budgets

from zemauth.models import User


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

    def test_persist_cpc_change_to_admin_log(self):
        autopilot.persist_cpc_change_to_admin_log(
            models.AdGroupSource.objects.get(id=1),
            20.0,
            0.15,
            0.20,
            30.0,
            5,
            []
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
        self.assertTrue(autopilot.ad_group_sources_daily_budget_was_changed_recently(
            models.AdGroupSource.objects.get(id=1)))

        self.assertFalse(autopilot.ad_group_sources_daily_budget_was_changed_recently(
            models.AdGroupSource.objects.get(id=2)))
        settings_writer = dash.api.AdGroupSourceSettingsWriter(models.AdGroupSource.objects.get(id=2))
        resource = dict()
        resource['daily_budget_cc'] = decimal.Decimal(60.00)

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User.objects.create_user('test@example.com')

        settings_writer.set(resource, request)
        self.assertTrue(autopilot.ad_group_sources_daily_budget_was_changed_recently(
            models.AdGroupSource.objects.get(id=2)))

    @patch('automation.settings.AUTOPILOT_CPC_CHANGE_TABLE', (
        {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.5,
            'bid_cpc_procentual_increase': decimal.Decimal('0.1')},
        {'underspend_upper_limit': -0.5, 'underspend_lower_limit': -
            0.1, 'bid_cpc_procentual_increase': decimal.Decimal('0.5')},
        {'underspend_upper_limit': -0.1, 'underspend_lower_limit': 0,
            'bid_cpc_procentual_increase': decimal.Decimal('-0.5')}
    )
    )
    @patch('automation.settings.AUTOPILOT_MIN_CPC', decimal.Decimal('0.1'))
    @patch('automation.settings.AUTOPILOT_MAX_CPC', decimal.Decimal('3'))
    @patch('automation.settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE', decimal.Decimal('0.2'))
    @patch('automation.settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE', decimal.Decimal('0.3'))
    @patch('automation.settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE', decimal.Decimal('0.05'))
    @patch('automation.settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE', decimal.Decimal('0.25'))
    def test_calculate_new_autopilot_cpc(self):
        test_cases = (
            #  cpc, daily_budget, yesterday_spend, new_cpc, comments
            ('0', '10', '5', '0', [automation.constants.CpcChangeComment.CPC_NOT_SET,
                                   automation.constants.CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('0.5', '10', '8', '0.75', []),
            ('2.5', '10', '8', '2.75', []),
            ('0.5', '10', '10', '0.25', []),
            ('0.5', '10', '2', '0.55', []),
            ('0.5', '10', '0', '0.5', [automation.constants.CpcChangeComment.NO_YESTERDAY_SPEND]),
            ('0.5', '10', '5', '0.55', []),
            ('0.5', '0', '5', '0.5', [automation.constants.CpcChangeComment.BUDGET_NOT_SET]),
            ('0.5', '10', '0', '0.5', [automation.constants.CpcChangeComment.NO_YESTERDAY_SPEND]),
            ('0.5', '-10', '5', '0.5', [automation.constants.CpcChangeComment.BUDGET_NOT_SET]),
            ('0.5', '10', '-5', '0.5', [automation.constants.CpcChangeComment.NO_YESTERDAY_SPEND]),
            ('-0.5', '10', '5', '-0.5', [automation.constants.CpcChangeComment.CPC_NOT_SET,
                                         automation.constants.CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('0.35', '10', '9.96', '0.15', []),
            ('2.8', '10', '9.96', '2.5', []),
            ('3.5', '10', '1', '3.5', [automation.constants.CpcChangeComment.CURRENT_CPC_TOO_HIGH]),
            ('0.05', '10', '1', '0.05', [automation.constants.CpcChangeComment.CURRENT_CPC_TOO_LOW])
        )
        for test_case in test_cases:
            self.assertEqual(autopilot.calculate_new_autopilot_cpc(
                decimal.Decimal(test_case[0]),
                decimal.Decimal(test_case[1]),
                decimal.Decimal(test_case[2])),
                (decimal.Decimal(test_case[3]), test_case[4]))

    def test_send_autopilot_CPC_changes_email(self):
        autopilot.send_autopilot_CPC_changes_email(
            u'\u2014campaign_name',
            1,
            u'\u2014account_name',
            ['test@zemanta.com'],
            {(u'Adgroup', 109): [{
                'old_cpc_cc': decimal.Decimal('0.1800'),
                'source_name': u'source',
                'new_cpc_cc': decimal.Decimal('0.21'),
                'comments': []}
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
        models.CampaignBudgetSettings(
            campaign_id=1,
            total=decimal.Decimal('200.0000'),
            created_by_id=1,
        ).save(self.request)
        models.CampaignBudgetSettings(
            campaign_id=2,
            total=decimal.Decimal('300.0000'),
            created_by_id=1,
        ).save(self.request)

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
