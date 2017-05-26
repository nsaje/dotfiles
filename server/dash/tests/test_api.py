import decimal
import datetime
import mock

from django.db import connection
from django.test import TestCase
from django.http.request import HttpRequest

from dash import models
from dash import api
from dash import constants

from zemauth.models import User


class SetAdGroupSourceSettingsTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)
        self.ad_group_settings = \
            models.AdGroupSettings.objects \
                                  .filter(ad_group=self.ad_group_source.ad_group) \
                                  .latest('created_dt')
        assert self.ad_group_settings.state == 2

        patcher = mock.patch('dash.api.k1_helper')
        self.k1_helper_mock = patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_no_settings_yet(self, mock_send_mail):
        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        # delete all ad_group_source_settings - use raw sql to bypass model restrictions
        q = 'DELETE FROM dash_adgroupsourcesettings'
        connection.cursor().execute(q, [])

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'state': 1},
            request
        )

        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )

        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.state, 1)
        self.assertTrue(latest_settings.cpc_cc is None)
        self.assertTrue(latest_settings.daily_budget_cc is None)

        mock_send_mail.assert_called_with(
            self.ad_group_source.ad_group, request, 'AdsNative State set to Enabled')

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_changed(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'cpc_cc': decimal.Decimal(2)},
            request
        )

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)

        self.assertEqual(request.user, new_latest_settings.created_by)
        self.assertIsNone(new_latest_settings.system_user)

        mock_send_mail.assert_called_with(
            self.ad_group_source.ad_group, request, 'AdsNative Max CPC bid set from $0.120 to $2.000')

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_request_none(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = None

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'cpc_cc': decimal.Decimal(0.1)},
            request,
            system_user=constants.SystemUserType.AUTOPILOT
        )

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertIsNone(new_latest_settings.created_by)
        self.assertEqual(constants.SystemUserType.AUTOPILOT, new_latest_settings.system_user)

        self.assertFalse(mock_send_mail.called)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_changed_no_action(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'cpc_cc': decimal.Decimal(2)},
            request
        )

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)

        mock_send_mail.assert_called_with(self.ad_group_source.ad_group, request,
                                          'AdsNative Max CPC bid set from $0.120 to $2.000')

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_not_write_if_unchanged(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'daily_budget_cc': decimal.Decimal(50)},
            request)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.id, new_latest_settings.id)
        self.assertEqual(latest_settings.state, new_latest_settings.state)
        self.assertEqual(latest_settings.cpc_cc, new_latest_settings.cpc_cc)
        self.assertEqual(latest_settings.daily_budget_cc, new_latest_settings.daily_budget_cc)

        self.assertFalse(mock_send_mail.called)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_set_system_user_valid(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        api.set_ad_group_source_settings(
            self.ad_group_source, {'cpc_cc': decimal.Decimal(2)}, None, landing_mode=True)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertTrue(True, new_latest_settings.landing_mode)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_set_system_user_not_valid(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        api.set_ad_group_source_settings(
            self.ad_group_source, {'cpc_cc': decimal.Decimal(2)}, None, 1028)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertEqual(new_latest_settings.landing_mode, latest_settings.landing_mode)


class AdGroupSettingsOrderTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_settings_changes(self):

        set1 = models.AdGroupSettings(
            created_dt=datetime.date.today(),

            state=1,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.1'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        set2 = models.AdGroupSettings(
            created_dt=datetime.date.today() - datetime.timedelta(days=1),

            state=2,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.2'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        self.assertEqual(set1.get_setting_changes(set1), {})

        self.assertEqual(
            set1.get_setting_changes(set2),
            {'state': 2, 'cpc_cc': decimal.Decimal('0.2')},
        )
