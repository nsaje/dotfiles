import datetime
from decimal import Decimal
from mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.core import mail
from django.conf import settings

from zemauth.models import User
from dash import models as dash_models
import dash.constants
from utils import email_helper


@override_settings(
    SEND_NOTIFICATION_MAIL=True
)
class EmailHelperTestCase(TestCase):

    def setUp(self):
        request_factory = RequestFactory()
        self.user = User.objects.create_user('test@user.com')
        self.request = request_factory.get('/test')
        self.request.user = self.user

    def test_generate_password_reset_url(self):
        reset_url = email_helper._generate_password_reset_url(self.user, self.request)
        self.assertRegexpMatches(
            reset_url,
            r'https://testserver/set_password/[a-zA-Z0-9]+-[a-zA-Z0-9]+-[0-9a-zA-Z]{20}/')

    def test_send_email_to_user(self):
        subject = 'This is subject'
        body = 'This is body text'

        email_helper._send_email_to_user(self.user, self.request, subject, body)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    @override_settings(
        HOSTNAME='testhost',
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL='http://pagerduty.example.com',
        PAGER_DUTY_ADOPS_SERVICE_KEY='123abc'
    )
    @patch('utils.email_helper.pagerduty_helper.trigger')
    @patch('utils.email_helper.send_mail')
    def test_send_email_to_user_failed(self, mock_send_mail, mock_trigger_event):
        self.user.email = None
        mock_send_mail.side_effect = Exception
        email_helper._send_email_to_user(self.user, self.request, None, None)

        self.assertTrue(mock_trigger_event.called)

    @override_settings(
        HOSTNAME='testhost',
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL='http://pagerduty.example.com',
        PAGER_DUTY_ADOPS_SERVICE_KEY='123abc'
    )
    @patch('utils.email_helper.pagerduty_helper.trigger')
    def test_send_email_to_user_failed_user_none(self, mock_trigger_event):
        email_helper._send_email_to_user(None, self.request, None, None)
        self.assertTrue(mock_trigger_event.called)

    def test_send_ad_group_notification_email(self):
        campaign_manager = User.objects.create_user('manager@user.com')
        account_manager = User.objects.create_user('accountmanager@user.com')

        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account)
        campaign.save(self.request)

        campaign_settings = dash_models.CampaignSettings(campaign=campaign, campaign_manager=campaign_manager)
        campaign_settings.save(self.request)

        account_settings = dash_models.AccountSettings(
            account=campaign.account,
            default_account_manager=account_manager
        )
        account_settings.save(self.request)

        ad_group = dash_models.AdGroup(id=8, campaign=campaign)
        ad_group.save(self.request)

        email_helper.send_ad_group_notification_email(ad_group, self.request, 'Something changed, yo')

        subject = 'Settings change - ad group , campaign , account '
        body = 'Hi account manager of ad group \n\nWe\'d like to notify you that test@user.com has made the following change in the settings of the ad group , campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/ad_groups/8/history for further details.\n\nYours truly,\nZemanta\n    '

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [account_manager.email, campaign_manager.email])

        self.request.user = campaign_manager
        email_helper.send_ad_group_notification_email(ad_group, self.request, 'Test')

        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        HOSTNAME='testhost',
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL='http://pagerduty.example.com',
        PAGER_DUTY_ADOPS_SERVICE_KEY='123abc',
    )
    @patch('utils.email_helper.pagerduty_helper.trigger')
    def test_send_ad_group_notification_email_failed(self, mock_trigger_event):
        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account)
        campaign.save(self.request)

        ad_group = dash_models.AdGroup(campaign=campaign)
        ad_group.save(self.request)

        campaign.get_current_settings().save(self.request)

        email_helper.send_ad_group_notification_email(ad_group, self.request, 'Test')

        self.assertTrue(mock_trigger_event.called)

    def test_send_campaign_notification_email(self):
        campaign_manager = User.objects.create_user('manager@user.com')
        account_manager = User.objects.create_user('accountmanager@user.com')

        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account, id=48)
        campaign.save(self.request)

        campaign_settings = dash_models.CampaignSettings(
            campaign=campaign,
            campaign_manager=campaign_manager
        )
        campaign_settings.save(self.request)

        account_settings = dash_models.AccountSettings(
            account=campaign.account,
            default_account_manager=account_manager
        )
        account_settings.save(self.request)

        email_helper.send_campaign_notification_email(campaign, self.request, 'Something changed, yo')

        subject = 'Settings change - campaign , account '
        body = 'Hi account manager of campaign \n\nWe\'d like to notify you that test@user.com has made the following change in the settings of campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/campaigns/48/history for further details.\n\nYours truly,\nZemanta\n    '

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [account_manager.email, campaign_manager.email])

        self.request.user = campaign_manager
        email_helper.send_campaign_notification_email(campaign, self.request, 'Test')

        self.assertEqual(len(mail.outbox), 1)

    def test_send_async_report_email(self):
        user = User.objects.create_user('manager@user.com')

        account = dash_models.Account(name='Account 1')
        account.save(self.request)

        campaign = dash_models.Campaign(account=account, name='Campaign 1')
        campaign.save(self.request)

        ad_group = dash_models.AdGroup(campaign=campaign, name='Ad Group 1')
        ad_group.save(self.request)

        email_helper.send_async_report(user, ['asd@gmail.com'], 'bla.com/test.csv',
                                       datetime.date(2016, 1, 1), datetime.date(2016, 5, 5), datetime.date(2016, 1, 4),
                                       [], False, dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE, ['Publisher', 'Day'],
                                       ['Clicks'], False, ad_group)
        subject = 'Report results'
        body = """Hi,

You requested a report with the following settings:

Account: Account 1
Campaign: Campaign 1
Ad Group: Ad Group 1

Date range: 1/1/2016 - 5/5/2016
View: Publisher
Breakdowns: Day
Columns: Clicks
Filters: Show active publishers only
Totals included: No

You can download the report here: bla.com/test.csv.
Report will be available for download until 1/4/2016.

Yours truly,
Zemanta
    """
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, ['manager@user.com', 'asd@gmail.com'])

    @override_settings(
        HOSTNAME='testhost',
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL='http://pagerduty.example.com',
        PAGER_DUTY_ADOPS_SERVICE_KEY='123abc'
    )
    @patch('utils.email_helper.pagerduty_helper.trigger')
    def test_send_campaign_notification_email_failed(self, mock_trigger_event):
        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account)
        campaign.save(self.request)

        ad_group = dash_models.AdGroup(campaign=campaign)
        ad_group.save(self.request)

        campaign.get_current_settings().save(self.request)

        email_helper.send_campaign_notification_email(campaign, self.request, 'Test')

        self.assertTrue(mock_trigger_event.called)

    def test_send_livestream_email(self):
        email_helper.send_livestream_email(self.user, 'http://www.google.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Livestream session started')
        self.assertEqual(
            mail.outbox[0].body,
            'User test@user.com started a new livestream session, accesssible on: http://www.google.com')
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [u'operations@zemanta.com',
                                             u'ziga.stopinsek@zemanta.com'])

    def test_send_pacing_email_low(self):
        account = dash_models.Account(name='Test account')
        account.save(self.request)

        campaign = dash_models.Campaign(name='Test campaign', account=account, id=55)
        campaign.save(self.request)

        email_helper.send_pacing_notification_email(
            campaign,
            ['prodops@zemanta.com'],
            Decimal('15.123456'),
            'low'
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your campaign is underpacing')
        self.assertEqual(
            mail.outbox[0].body,
            '''Hi, campaign manager,

your campaign Test campaign (Test account) is underpacing with a rate of 15.12%.

Please consider adjusting daily spend caps on ad group source settings. Visit https://one.zemanta.com/campaigns/55/ad_groups to get a list of all active ad groups.

Yours truly,
Zemanta''')
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [u'prodops@zemanta.com'])

    def test_send_pacing_email_high(self):
        account = dash_models.Account(name='Test account')
        account.save(self.request)

        campaign = dash_models.Campaign(name='Test campaign', account=account, id=55)
        campaign.save(self.request)

        email_helper.send_pacing_notification_email(
            campaign,
            ['prodops@zemanta.com'],
            Decimal('155.123456'),
            'high'
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your campaign is overpacing')
        self.assertEqual(
            mail.outbox[0].body,
            '''Hi, campaign manager,

your campaign Test campaign (Test account) is overpacing with a rate of 155.12%.

Please consider adjusting daily spend caps on ad group source settings. Visit https://one.zemanta.com/campaigns/55/ad_groups to get a list of all active ad groups.

Yours truly,
Zemanta''')
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [u'prodops@zemanta.com'])

    def test_send_budget_notification_email(self):
        campaign_manager = User.objects.create_user('manager@user.com')
        account_manager = User.objects.create_user('accountmanager@user.com')

        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account, id=48)
        campaign.save(self.request)

        campaign_settings = dash_models.CampaignSettings(campaign=campaign, campaign_manager=campaign_manager)
        campaign_settings.save(self.request)

        account_settings = dash_models.AccountSettings(
            account=campaign.account,
            default_account_manager=account_manager
        )
        account_settings.save(self.request)

        email_helper.send_budget_notification_email(campaign, self.request, 'Something changed, yo')

        subject = 'Settings change - campaign , account '
        body = 'Hi account manager of campaign \n\nWe\'d like to notify you that test@user.com has made the following change in the budget of campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/campaigns/48/history for further details.\n\nYours truly,\nZemanta\n    '

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [account_manager.email, campaign_manager.email])

        self.request.user = campaign_manager
        email_helper.send_budget_notification_email(campaign, self.request, 'Test')

        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        HOSTNAME='testhost',
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL='http://pagerduty.example.com',
        PAGER_DUTY_ADOPS_SERVICE_KEY='123abc'
    )
    @patch('utils.email_helper.pagerduty_helper.trigger')
    def test_send_budget_notification_email_failed(self, mock_trigger_event):
        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account)
        campaign.save(self.request)

        ad_group = dash_models.AdGroup(campaign=campaign)
        ad_group.save(self.request)

        campaign.get_current_settings().save(self.request)

        email_helper.send_budget_notification_email(campaign, self.request, 'Test')

        self.assertTrue(mock_trigger_event.called)

    def test_send_depleting_credits_email(self):
        mock = MagicMock()
        email_helper.send_depleting_credits_email(
            mock,
            [dash_models.Account(id=1, name='Test 1'), dash_models.Account(id=2, name='Test 2')]
        )
        mock.email_user.assert_called_with(
            'Depleting credit line items',
            '''Dear sales representative,

Following accounts have depleting credit line items:
 - Account Test 1 https://one.zemanta.com/accounts/1/credit
 - Account Test 2 https://one.zemanta.com/accounts/2/credit


Yours truly,
Zemanta
    ''')


class FormatChangesTextTest(TestCase):

    def test_single_line(self):
        self.assertEqual(email_helper._format_changes_text('Some change.'), '- Some change.')

    def test_multiple_lines_(self):
        self.assertEqual(
            email_helper._format_changes_text('Some change.\nAnother change.'), '- Some change,\n- Another change.')
