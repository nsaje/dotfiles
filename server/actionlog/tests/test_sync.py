import httplib
import mock

import dash.models
import actionlog.models

from django.test import TestCase
from django.conf import settings

from actionlog import sync, constants

from utils.command_helpers import last_n_days


class ActionLogSyncTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_sync.yaml']

    def test_ad_group_source_latest_status_sync(self):
        latest_status_sync_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_status_sync()

        self.assertEqual(latest_status_sync_dt.isoformat(), '2014-07-01T07:07:07')

        latest_status_sync_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=5)
        ).get_latest_status_sync()

        self.assertEqual(latest_status_sync_dt.isoformat(), '2014-07-01T11:11:11')

    def test_ad_group_source_latest_report_sync(self):
        latest_report_sync_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_report_sync()

        self.assertEqual(latest_report_sync_dt.isoformat(), '2014-07-01T12:12:12')

        latest_report_sync_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=2)
        ).get_latest_report_sync()

        self.assertEqual(latest_report_sync_dt.isoformat(), '2014-07-01T18:00:00')

        latest_report_sync_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=5)
        ).get_latest_report_sync()

        self.assertEqual(latest_report_sync_dt.isoformat(), '2014-07-01T13:00:00')

    def test_ad_group_source_latest_success(self):
        latest_success_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_success()

        self.assertEqual(latest_success_dt.isoformat(), '2014-07-01T07:07:07')

        latest_success_dt = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=5)
        ).get_latest_success()

        self.assertEqual(latest_success_dt.isoformat(), '2014-07-01T11:11:11')

    def test_ad_group_latest_success(self):
        latest_success_dt = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_success()

        self.assertEqual(latest_success_dt.isoformat(), '2014-07-01T07:07:07')

        latest_success_dt = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=2)
        ).get_latest_success()

        self.assertEqual(latest_success_dt, None)

    def test_campaign_latest_success(self):
        latest_success_dt = sync.CampaignSync(
            dash.models.Campaign.objects.get(pk=1)
        ).get_latest_success()

        self.assertEqual(latest_success_dt.isoformat(), '2014-07-01T07:07:07')

        latest_success_dt = sync.CampaignSync(
            dash.models.Campaign.objects.get(pk=2)
        ).get_latest_success()

        self.assertEqual(latest_success_dt, None)

    def test_global_latest_success(self):
        latest_success_dt = sync.GlobalSync().get_latest_success()
        self.assertEqual(latest_success_dt, None)


class ActionLogTriggerSyncTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_sync.yaml']

    def setUp(self):
        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_reports(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        dates = last_n_days(3)

        ags_sync = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=6)
        )
        ags_sync.trigger_reports(dates)

        order = actionlog.models.ActionLogOrder.objects.order_by('-created_dt').first()
        self.assertEqual(
            len(order.actionlog_set.filter(action=constants.Action.FETCH_REPORTS)),
            3
        )
        self.assertEqual(
            len(order.actionlog_set.filter(action=constants.Action.FETCH_REPORTS)),
            3
        )

        for action in order.actionlog_set.all():
            self.assertEqual(action.state, constants.ActionState.WAITING)
            self.assertIn(
                action.action,
                (constants.Action.FETCH_REPORTS, )
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_status(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        self.assertEqual(
            len(actionlog.models.ActionLog.objects.filter(ad_group_source=6)),
            0
        )

        ags_sync = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=6)
        )
        ags_sync.trigger_status()

        self.assertEqual(
            len(actionlog.models.ActionLog.objects.filter(ad_group_source=6)),
            1
        )

        alog = actionlog.models.ActionLog.objects.filter(ad_group_source=6)[0]
        self.assertEqual(alog.state, constants.ActionState.WAITING)
        self.assertEqual(alog.action, constants.Action.FETCH_CAMPAIGN_STATUS)
        self.assertEqual(alog.action_type, constants.ActionType.AUTOMATIC)
