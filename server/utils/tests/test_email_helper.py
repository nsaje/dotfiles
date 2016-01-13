from mock import patch

from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.core import mail
from django.conf import settings

from zemauth.models import User
from dash import models as dash_models
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
    def test_send_email_to_user_failed(self, mock_trigger_event):
        self.user.email = None
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

        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account)
        campaign.save(self.request)

        campaign_settings = dash_models.CampaignSettings(campaign=campaign, campaign_manager=campaign_manager)
        campaign_settings.save(self.request)

        ad_group = dash_models.AdGroup(id=8, campaign=campaign)
        ad_group.save(self.request)

        email_helper.send_ad_group_notification_email(ad_group, self.request, 'Something changed, yo')

        subject = 'Settings change - ad group , campaign , account '
        body = 'Hi account manager of ad group \n\nWe\'d like to notify you that test@user.com has made the following change in the settings of the ad group , campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/ad_groups/8/agency for further details.\n\nYours truly,\nZemanta\n    '

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [campaign_manager.email])

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

        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account, id=48)
        campaign.save(self.request)

        campaign_settings = dash_models.CampaignSettings(campaign=campaign, campaign_manager=campaign_manager)
        campaign_settings.save(self.request)

        email_helper.send_campaign_notification_email(campaign, self.request, 'Something changed, yo')

        subject = 'Settings change - campaign , account '
        body = 'Hi account manager of campaign \n\nWe\'d like to notify you that test@user.com has made the following change in the settings of campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/campaigns/48/agency for further details.\n\nYours truly,\nZemanta\n    '

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [campaign_manager.email])

        self.request.user = campaign_manager
        email_helper.send_campaign_notification_email(campaign, self.request, 'Test')

        self.assertEqual(len(mail.outbox), 1)

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

    def test_send_budget_notification_email(self):
        campaign_manager = User.objects.create_user('manager@user.com')

        account = dash_models.Account()
        account.save(self.request)

        campaign = dash_models.Campaign(account=account, id=48)
        campaign.save(self.request)

        campaign_settings = dash_models.CampaignSettings(campaign=campaign, campaign_manager=campaign_manager)
        campaign_settings.save(self.request)

        email_helper.send_budget_notification_email(campaign, self.request, 'Something changed, yo')

        subject = 'Settings change - campaign , account '
        body = 'Hi account manager of campaign \n\nWe\'d like to notify you that test@user.com has made the following change in the budget of campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/campaigns/48/agency for further details.\n\nYours truly,\nZemanta\n    '

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, 'Zemanta <{}>'.format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [campaign_manager.email])

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


class FormatChangesTextTest(TestCase):
    def test_single_line(self):
        self.assertEqual(email_helper._format_changes_text('Some change.'), '- Some change.')

    def test_multiple_lines_(self):
        self.assertEqual(
            email_helper._format_changes_text('Some change.\nAnother change.'), '- Some change,\n- Another change.')
