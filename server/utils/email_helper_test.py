import datetime
from decimal import Decimal

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test import override_settings
from django.test.client import RequestFactory
from mock import patch

import dash.constants
from dash import models as dash_models
from utils import email_helper
from utils.magic_mixer import magic_mixer
from zemauth.models import User


class EmailAPITestCase(TestCase):
    def setUp(self):
        request_factory = RequestFactory()
        self.normal_user = User.objects.create_user("test1@user.com")
        self.whitelabel_agency_user = User.objects.create_user("test2@user.com")

        self.request = request_factory.get("/test")
        self.request.user = self.normal_user

        self.agency = dash_models.Agency(name="Agency 1")
        self.agency.save(self.request)
        self.agency.users.add(self.normal_user)
        self.white_label = dash_models.WhiteLabel.objects.create(
            theme="greenpark", dashboard_title="greenpark", favicon_url="http://icon.cm"
        )
        self.whitelabel_agency = dash_models.Agency(name="Agency 2", white_label=self.white_label)
        self.whitelabel_agency.save(self.request)
        self.whitelabel_agency.users.add(self.whitelabel_agency_user)

    @patch("utils.email_helper.render_to_string")
    def test_basic(self, mock_render):
        email_helper.send_official_email(
            recipient_list=["test@test.com"],
            subject="Zemanta Subject",
            body="Zemanta Body",
            additional_recipients=["additional@test.com"],
            tags=["tag1", "tag2"],
            agency_or_user=self.agency,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@test.com"])
        self.assertEqual(mail.outbox[0].subject, "Zemanta Subject")
        self.assertEqual(mail.outbox[0].body, "Zemanta Body")
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].bcc, ["additional@test.com"])
        self.assertEqual(mail.outbox[0].extra_headers, {"X-Mailgun-Tag": ["tag1", "tag2"]})
        mock_render.assert_called_with("email.html", {"content": "<p>Zemanta Body</p>", "subject": "Zemanta Subject"})

    @override_settings(TESTING=False)
    @patch("utils.email_helper.render_to_string")
    def test_basic_development(self, mock_render):
        email_helper.send_official_email(
            recipient_list=["test@test.com"],
            subject="Zemanta Subject",
            body="Zemanta Body",
            additional_recipients=["additional@test.com"],
            tags=["tag1", "tag2"],
            agency_or_user=self.agency,
        )
        self.assertEqual(len(mail.outbox), 0)

    @patch("utils.email_helper.render_to_string")
    def test_whitelabel(self, mock_render):
        email_helper.send_official_email(
            recipient_list=["test@test.com"],
            subject="Zemanta Subject",
            body="Zemanta Body",
            agency_or_user=self.whitelabel_agency,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@test.com"])
        self.assertEqual(mail.outbox[0].subject, "Telescope Subject")
        self.assertEqual(mail.outbox[0].body, "Telescope Body")
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Telescope Body</p>", "subject": "Telescope Subject"}
        )

    def test_from_email(self):
        email_helper.send_official_email(
            recipient_list=["test@test.com"],
            subject="Zemanta Subject",
            body="Zemanta Body",
            from_email="newfrom@zemanta.com",
            agency_or_user=self.agency,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <newfrom@zemanta.com>")

    def test_custom_html(self):
        email_helper.send_internal_email(
            recipient_list=["test@test.com"], subject="Zemanta Subject", body="Zemanta Body", custom_html="<b>hi!</b>"
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].alternatives, [("<b>hi!</b>", "text/html")])

    def test_no_recipients_just_bcc(self):
        email_helper.send_official_email(
            additional_recipients=["test@test.com"],
            subject="Zemanta Subject",
            body="Zemanta Body",
            agency_or_user=self.agency,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].bcc, ["test@test.com"])

    def test_no_tags(self):
        email_helper.send_official_email(
            additional_recipients=["test@test.com"],
            subject="Zemanta Subject",
            body="Zemanta Body",
            agency_or_user=self.agency,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].extra_headers, {"X-Mailgun-Tag": ["unclassified"]})

    def test_params_from_template(self):
        template_type = dash.constants.EmailTemplateType.OUTBRAIN_ACCOUNTS_RUNNING_OUT
        email_template = dash.models.EmailTemplate.objects.get(template_type=template_type)
        email_template.subject = "mysubject"
        email_template.body = "mybody"
        email_template.recipients = "test@test.com, test2@test.com"
        email_template.save()

        params = email_helper.params_from_template(template_type)
        self.assertEqual(
            params,
            {
                "subject": "mysubject",
                "body": "mybody",
                "additional_recipients": ["test@test.com", "test2@test.com"],
                "tags": ["OUTBRAIN_ACCOUNTS_RUNNING_OUT"],
            },
        )

    @patch("dash.constants.EmailTemplateType.get_name", return_value="")
    @patch("dash.models.EmailTemplate.objects.get")
    def test_params_from_template_arguments(self, mock_template, mock_type):
        mock_template.return_value = mock_template
        mock_template.subject = "Testing"
        mock_template.recipients = "test@test.com,"
        mock_template.body = """
Test e-mail from {{ user }}.
{% if campaigns %}
{% for name in campaigns %}
{{ name }}
{% endfor %}
{% else %}
No campaigns to list.
{% endif %}
"""
        params = email_helper.params_from_template(None, user="Admin", campaigns=["C1", "C2", "C3"])
        self.assertEqual(
            params,
            {
                "subject": "Testing",
                "body": "\nTest e-mail from Admin.\n\n\nC1\n\nC2\n\nC3\n\n\n",
                "additional_recipients": ["test@test.com"],
                "tags": [""],
            },
        )

    @patch("dash.constants.EmailTemplateType.get_name", return_value="")
    @patch("dash.models.EmailTemplate.objects.get")
    @patch("utils.email_helper.render_to_string")
    def test_create_email_html_unescape(self, mock_render, mock_template, mock_type):
        account = magic_mixer.blend(dash.models.Account, name="Paul's test (Amnet)")

        mock_template.return_value = mock_template
        mock_template.subject = "Settings change - account {{account.name}}"
        mock_template.recipients = "test@test.com,"
        mock_template.body = "Change were done in the settings of the account {{account.name}}"

        params = email_helper.params_from_template(None, account=account)

        email = email_helper._create_email(**params, recipient_list=["test@test.com"])

        self.assertEqual(email.from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(email.to, ["test@test.com"])
        self.assertEqual(email.subject, "Settings change - account Paul's test (Amnet)")
        self.assertEqual(email.body, "Change were done in the settings of the account Paul's test (Amnet)")
        self.assertEqual(len(email.alternatives), 1)
        self.assertEqual(email.alternatives[0][1], "text/html")
        mock_render.assert_called_with(
            "email.html",
            {
                "content": "<p>Change were done in the settings of the account Paul&#39;s test (Amnet)</p>",
                "subject": "Settings change - account Paul&#39;s test (Amnet)",
            },
        )


@override_settings(SEND_NOTIFICATION_MAIL=True)
class EmailHelperTestCase(TestCase):
    def setUp(self):
        request_factory = RequestFactory()
        self.user = User.objects.create_user("test@user.com")
        self.request = request_factory.get("/test")
        self.request.user = self.user
        self.request.is_api_request = False

    def test_generate_password_reset_url(self):
        reset_url = email_helper._generate_password_reset_url(self.user, self.request)
        self.assertRegex(reset_url, r"https://testserver/set_password/[a-zA-Z0-9]+-[a-zA-Z0-9]+-[0-9a-zA-Z]{20}/")

    def test_send_ad_group_notification_email(self):
        campaign_manager = User.objects.create_user("manager@user.com")
        account_manager = User.objects.create_user("accountmanager@user.com")

        ad_group = magic_mixer.blend(dash_models.AdGroup, id=8, name="", campaign__name="", campaign__account__name="")

        ad_group.campaign.settings.update(None, campaign_manager=campaign_manager)
        ad_group.campaign.account.settings.update(None, default_account_manager=account_manager)

        email_helper.send_ad_group_notification_email(ad_group, self.request, "Something changed, yo")

        subject = "Settings change - ad group , campaign , account "
        body = "Hi account manager of ad group \n\nWe'd like to notify you that test@user.com has made the following change in the settings of the ad group , campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/v2/analytics/adgroup/8?history for further details.\n\nYours truly,\nZemanta\n    "

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(set(mail.outbox[0].to), set([campaign_manager.email]))

        self.request.user = campaign_manager
        email_helper.send_ad_group_notification_email(ad_group, self.request, "Test")

        self.assertEqual(len(mail.outbox), 1)

    def test_send_campaign_notification_email(self):
        campaign_manager = User.objects.create_user("manager@user.com")
        account_manager = User.objects.create_user("accountmanager@user.com")

        campaign = magic_mixer.blend(dash_models.Campaign, id=48, name="", account__name="")

        campaign.settings.update(None, campaign_manager=campaign_manager)
        campaign.account.settings.update(None, default_account_manager=account_manager)

        email_helper.send_campaign_notification_email(campaign, self.request, "Something changed, yo")

        subject = "Settings change - campaign , account "
        body = "Hi account manager of campaign \n\nWe'd like to notify you that test@user.com has made the following change in the settings of campaign , account :\n\n- Something changed, yo.\n\nPlease check https://testserver/v2/analytics/campaign/48?history for further details.\n\nYours truly,\nZemanta\n    "

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(set(mail.outbox[0].to), set([campaign_manager.email]))

        self.request.user = campaign_manager
        email_helper.send_campaign_notification_email(campaign, self.request, "Test")

        self.assertEqual(len(mail.outbox), 1)

    def test_send_account_notification_email(self):
        account = magic_mixer.blend(dash_models.Account, name="")

        account_manager = User.objects.create_user("accountmanager@user.com")
        account.settings.update(None, default_account_manager=account_manager)

        email_helper.send_account_notification_email(account, self.request, "Something changed, yo")

        subject = "Settings change - account "
        body = "Hi account manager of account \n\nWe'd like to notify you that test@user.com has made the following change in the settings of the account :\n\n- Something changed, yo.\n\nPlease check https://testserver/v2/analytics/account/{}?history for further details.\n\nYours truly,\nZemanta\n    ".format(
            account.pk
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, [account_manager.email])

    def test_send_async_report_email(self):
        user = User.objects.create_user("manager@user.com")

        account = magic_mixer.blend(dash_models.Account, name="Account 1")
        campaign = dash_models.Campaign(account=account, name="Campaign 1")
        campaign.save(self.request)

        ad_group = dash_models.AdGroup(campaign=campaign, name="Ad Group 1")
        ad_group.save(self.request)

        email_helper.send_async_report(
            user,
            ["asd@gmail.com"],
            "bla.com/test.csv",
            datetime.date(2016, 1, 1),
            datetime.date(2016, 5, 5),
            datetime.date(2016, 1, 4),
            [],
            False,
            dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE,
            "Publisher",
            ["By Day"],
            ["Clicks"],
            False,
            ad_group.name,
            campaign.name,
            account.name,
        )
        subject = "Report results"
        body = """Hi,

You requested a report with the following settings:

Account: Account 1
Campaign: Campaign 1
Ad Group: Ad Group 1

Date range: 1/1/2016 - 5/5/2016
View: Publisher
Breakdowns: By Day
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
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, ["asd@gmail.com"])

    def test_send_pacing_email_low(self):
        account = magic_mixer.blend(dash_models.Account, name="Test account")

        campaign = dash_models.Campaign(name="Test campaign", account=account, id=55)
        campaign.save(self.request)

        email_helper.send_pacing_notification_email(
            campaign,
            ["prodops@outbrain.com"],
            Decimal("15.123456"),
            "low",
            {"ideal_daily_media_spend": Decimal("123.45678")},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your campaign is underpacing")
        self.assertEqual(
            mail.outbox[0].body,
            """Hi, campaign manager,

your campaign Test campaign (Test account) is underpacing with a rate of 15.12%.

Please consider adjusting daily spend caps on ad group source settings. Visit https://one.zemanta.com/v2/analytics/campaign/55 to get a list of all active ad groups.

Yours truly,
Zemanta""",
        )
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, ["prodops@outbrain.com"])

    def test_send_pacing_email_high(self):
        account = magic_mixer.blend(dash_models.Account, name="Test account")

        campaign = dash_models.Campaign(name="Test campaign", account=account, id=55)
        campaign.save(self.request)

        email_helper.send_pacing_notification_email(
            campaign,
            ["prodops@outbrain.com"],
            Decimal("155.123456"),
            "high",
            {"ideal_daily_media_spend": Decimal("123.45678")},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your campaign is overpacing")
        self.assertEqual(
            mail.outbox[0].body,
            """Hi, campaign manager,

your campaign Test campaign (Test account) is overpacing with a rate of 155.12%.

Please consider adjusting daily spend caps on ad group source settings. Visit https://one.zemanta.com/v2/analytics/campaign/55 to get a list of all active ad groups.

Yours truly,
Zemanta""",
        )
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, ["prodops@outbrain.com"])

    @patch("utils.email_helper.send_account_notification_email")
    def test_send_obj_notification_email_account(self, mock_email):
        account = magic_mixer.blend(dash_models.Account, name="Test account")
        email_helper.send_obj_changes_notification_email(account, self.request, "")
        self.assertTrue(mock_email.called)

    @patch("utils.email_helper.send_campaign_notification_email")
    def test_send_obj_notification_email_campaign(self, mock_email):
        email_helper.send_obj_changes_notification_email(dash_models.Campaign(), self.request, "")
        self.assertTrue(mock_email.called)

    @patch("utils.email_helper.send_ad_group_notification_email")
    def test_send_obj_notification_email_adgroup(self, mock_email):
        email_helper.send_obj_changes_notification_email(dash_models.AdGroup(), self.request, "")
        self.assertTrue(mock_email.called)

    def test_send_supply_report_email(self):
        email_helper.send_supply_report_email("testsupply@test.com", datetime.date(2016, 1, 1), 1000, 5.0)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Zemanta Report for 1/1/2016")
        self.assertEqual(
            mail.outbox[0].body,
            "\nHello,\n\nHere are the impressions and spend for 1/1/2016.\n\nImpressions: 1000\nSpend: 5.0\n\nYours truly,\nZemanta\n\n---\nThe reporting data is an estimate. Final amounts are tallied and should be invoiced per your agreement with Zemanta.\n* All times are in Eastern Standard Time (EST).\n    ",
        )
        self.assertEqual(mail.outbox[0].from_email, "Zemanta <{}>".format(settings.SUPPLY_REPORTS_FROM_EMAIL))
        self.assertEqual(mail.outbox[0].to, ["testsupply@test.com"])

    def test_dont_send_notification_email(self):
        self.request.is_api_request = True
        campaign_manager = User.objects.create_user("manager@user.com")
        account_manager = User.objects.create_user("accountmanager@user.com")

        ad_group = magic_mixer.blend(dash_models.AdGroup, id=8, name="", campaign__name="", campaign__account__name="")

        ad_group.campaign.settings.update(None, campaign_manager=campaign_manager)
        ad_group.campaign.account.settings.update(None, default_account_manager=account_manager)

        email_helper.send_ad_group_notification_email(ad_group, self.request, "Something changed, yo")
        self.assertEqual(len(mail.outbox), 0)


class FormatChangesTextTest(TestCase):
    def test_single_line(self):
        self.assertEqual(email_helper._format_changes_text("Some change."), "- Some change.")

    def test_multiple_lines_(self):
        self.assertEqual(
            email_helper._format_changes_text("Some change.\nAnother change."), "- Some change,\n- Another change."
        )


@patch("utils.email_helper.render_to_string")
class WhitelabelTestCase(TestCase):
    def setUp(self):
        request_factory = RequestFactory()
        self.normal_user = User.objects.create_user("test1@user.com")
        self.whitelabel_agency_user = User.objects.create_user("test2@user.com")

        self.request = request_factory.get("/test")
        self.request.user = self.normal_user

        self.agency = dash_models.Agency(name="Agency 1")
        self.agency.save(self.request)
        self.agency.users.add(self.normal_user)
        self.white_label = dash_models.WhiteLabel.objects.create(
            theme="greenpark", dashboard_title="greenpark", favicon_url="http://icon.cm"
        )
        self.whitelabel_agency = dash_models.Agency(name="Agency 2", white_label=self.white_label)

        self.whitelabel_agency = dash_models.Agency(name="Agency 2", white_label=self.white_label)
        self.whitelabel_agency.save(self.request)
        self.whitelabel_agency.users.add(self.whitelabel_agency_user)

    @staticmethod
    def _create_official_email(subject, body, **kwargs):
        kwargs["recipient_list"] = ["test@test.com"]
        kwargs["subject"] = subject
        kwargs["body"] = body
        email_helper.create_official_email(**kwargs)

    @staticmethod
    def _create_internal_email(subject, body, **kwargs):
        kwargs["recipient_list"] = ["test@test.com"]
        kwargs["subject"] = subject
        kwargs["body"] = body
        email_helper.create_internal_email(**kwargs)

    def test_no_params(self, mock_render):
        self._create_internal_email(subject="Subject", body="Body")
        mock_render.assert_called_with("email.html", {"content": "<p>Body</p>", "subject": "Subject"})

    def test_normal_user(self, mock_render):
        self._create_official_email("Subject", "Body", agency_or_user=self.normal_user)
        mock_render.assert_called_with("email.html", {"content": "<p>Body</p>", "subject": "Subject"})

    def test_whitelabel_agency_user(self, mock_render):
        self._create_official_email("Subject", "Body", agency_or_user=self.whitelabel_agency_user)
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Body</p>", "subject": "Subject"}
        )

    def test_normal_agency(self, mock_render):
        self._create_official_email("Subject", "Body", agency_or_user=self.agency)
        mock_render.assert_called_with("email.html", {"content": "<p>Body</p>", "subject": "Subject"})

    def test_whitelabel_agency(self, mock_render):
        self._create_official_email("Subject", "Body", agency_or_user=self.whitelabel_agency)
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Body</p>", "subject": "Subject"}
        )

    def test_product_name_subject(self, mock_render):
        self._create_official_email("Subject Zemanta", "Body", agency_or_user=self.whitelabel_agency_user)
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Body</p>", "subject": "Subject Telescope"}
        )

    def test_product_name_subject_long(self, mock_render):
        self._create_official_email("Subject Zemanta One", "Body", agency_or_user=self.whitelabel_agency_user)
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Body</p>", "subject": "Subject Telescope"}
        )

    def test_product_name_body(self, mock_render):
        self._create_official_email("Subject", "Body Zemanta, Zemanta", agency_or_user=self.whitelabel_agency_user)
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Body Telescope, Telescope</p>", "subject": "Subject"}
        )

    def test_product_name_body_long(self, mock_render):
        self._create_official_email("Subject", "Body: Zemanta One", agency_or_user=self.whitelabel_agency_user)
        mock_render.assert_called_with(
            "whitelabel/greenpark/email.html", {"content": "<p>Body: Telescope</p>", "subject": "Subject"}
        )
