import httplib
import mock
import datetime

import dash.models
import actionlog.models

from django.test import TestCase
from django.conf import settings

from actionlog import sync, constants

from utils.command_helpers import last_n_days


class ActionLogSyncTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_sync.yaml']

    def test_global_latest_success_by_account_ignore_archived(self):
        latest_success_by_account = sync.GlobalSync().get_latest_success_by_account()

        self.assertEqual(
            latest_success_by_account,
            {
                1: datetime.datetime(2014, 6, 10, 9, 58, 21),
                2: None,
                3: datetime.datetime(2014, 6, 10, 9, 58, 21)
            })

    def test_global_latest_success_by_source_ignore_archived(self):
        latest_success_by_source = sync.GlobalSync().get_latest_success_by_source()

        self.assertEqual(
            latest_success_by_source,
            {
                1: None,
                2: None,
                3: None,
                4: datetime.datetime(2014, 6, 10, 9, 58, 21),
                5: datetime.datetime(2014, 6, 10, 9, 58, 21)
            })

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
        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')

        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=5)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

    def test_cached_ad_group_source_latest_success(self):
        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')

        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_success_by_child(recompute=False)

        self.assertEqual(latest_success_dict[1].isoformat(), '2014-06-10T09:58:21')

    def test_ad_group_source_latest_source_success(self):
        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_source_success()

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')

        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=5)
        ).get_latest_source_success()

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

    def test_cached_ad_group_source_latest_source_success(self):
        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_source_success()

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')

        latest_success_dict = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        ).get_latest_source_success(recompute=False)

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-06-10T09:58:21')

    def test_ad_group_latest_success(self):
        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=2)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 3)
        self.assertEqual(latest_success_dict[6], None)
        self.assertEqual(latest_success_dict[7], None)
        self.assertEqual(latest_success_dict[8], None)

    def test_cached_ad_group_latest_success(self):
        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_success_by_child(recompute=False)

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-06-10T09:58:21')

    def test_ad_group_latest_source_success(self):
        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_source_success()

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_source_success()

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

    def test_cached_ad_group_latest_source_success(self):
        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_source_success()

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_source_success(recompute=False)

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-06-10T09:58:21')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-06-10T09:58:21')

    def test_ad_group_latest_success_maintenance(self):
        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 5)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

        # turn off maintenance mode for Source 6
        m_source = dash.models.Source.objects.get(pk=6)
        m_source.maintenance = False
        m_source.save()

        latest_success_dict = sync.AdGroupSync(
            dash.models.AdGroup.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 6)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')
        self.assertEqual(latest_success_dict[2].isoformat(), '2014-07-01T08:08:08')
        self.assertEqual(latest_success_dict[3].isoformat(), '2014-07-01T09:09:09')
        self.assertEqual(latest_success_dict[4].isoformat(), '2014-07-01T10:10:10')
        self.assertEqual(latest_success_dict[5].isoformat(), '2014-07-01T11:11:11')

        # put the maintenance mode back on
        m_source.maintenance = True
        m_source.save()

    def test_campaign_latest_success(self):
        campaign1 = dash.models.Campaign.objects.get(pk=1)
        latest_success_dict = sync.CampaignSync(campaign1).get_latest_success_by_child()
        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')

        campaign2 = dash.models.Campaign.objects.get(pk=2)
        latest_success_dict = sync.CampaignSync(campaign2).get_latest_success_by_child()
        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[2], None)

    def test_cached_campaign_latest_success(self):
        latest_success_dict = sync.CampaignSync(
            dash.models.Campaign.objects.get(pk=1)
        ).get_latest_success_by_child()

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-07-01T07:07:07')

        latest_success_dict = sync.CampaignSync(
            dash.models.Campaign.objects.get(pk=1)
        ).get_latest_success_by_child(recompute=False)

        self.assertEqual(len(latest_success_dict), 1)
        self.assertEqual(latest_success_dict[1].isoformat(), '2014-06-10T09:58:21')

    def test_global_latest_success(self):
        latest_success_dict = sync.GlobalSync().get_latest_success_by_child()
        self.assertEqual(len(latest_success_dict), 2)
        self.assertEqual(latest_success_dict[1], None)
        self.assertEqual(latest_success_dict[2], None)


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
        ags_sync.trigger_reports_for_dates(dates)

        actions = actionlog.models.ActionLog.objects.filter(
            created_dt__isnull=False).order_by('-created_dt')
        actions = list(actions)

        self.assertEqual(len(actions) > 3, True)
        self.assertEqual(actions[0].created_dt.date() == actions[1].created_dt.date() == actions[2].created_dt.date(), True)
        self.assertEqual(actions[3].created_dt.date() < actions[2].created_dt.date(), True)

        for action in actions[:3]:
            self.assertEqual(action.state, constants.ActionState.WAITING)
            self.assertIn(
                action.action,
                (constants.Action.FETCH_REPORTS, )
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_ad_group_source_trigger_content_ad_status(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        self.assertFalse(actionlog.models.ActionLog.objects.filter(
            ad_group_source__ad_group_id=1,
            action=constants.Action.GET_CONTENT_AD_STATUS).exists())

        ags_sync = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=1)
        )

        ags_sync.trigger_content_ad_status()

        action_logs = actionlog.models.ActionLog.objects.filter(
            ad_group_source__ad_group_id=1,
            action=constants.Action.GET_CONTENT_AD_STATUS)

        self.assertEqual(len(action_logs), 1)

        self.assertEqual(action_logs[0].state, constants.ActionState.WAITING)
        self.assertEqual(action_logs[0].action, constants.Action.GET_CONTENT_AD_STATUS)
        self.assertEqual(action_logs[0].action_type, constants.ActionType.AUTOMATIC)

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

    def test_ad_group_source_get_dates_to_sync_reports(self):
        ags_sync = sync.AdGroupSourceSync(
            dash.models.AdGroupSource.objects.get(pk=5)
        )

        dates = ags_sync.get_dates_to_sync_reports()
        dates = list(dates)

        self.assertEqual(dates[0], datetime.datetime.utcnow().date())
        self.assertEqual(dates[-1], datetime.date(2014, 7, 1) - datetime.timedelta(days=settings.LAST_N_DAY_REPORTS - 1))
        self.assertEqual(
            len(dates), 
            (datetime.datetime.utcnow().date() - (
                    datetime.date(2014, 7, 1) - datetime.timedelta(days=settings.LAST_N_DAY_REPORTS - 1)
                )).days + 1
        )


class ActionLogSyncGetComponentsTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_sync.yaml']

    def test_global_sync_get_components(self):
        global_sync = sync.GlobalSync()
        child_syncs = global_sync.get_components()

        self.assertEqual(len(list(child_syncs)), 2)

    def test_account_sync_get_components(self):
        account = dash.models.Account.objects.get(pk=3)

        account_sync = sync.AccountSync(account)
        child_syncs = account_sync.get_components()

        self.assertEqual(len(list(child_syncs)), 1)

    def test_campaign_sync_get_components(self):
        campaign = dash.models.Campaign.objects.get(pk=4)

        campaign_sync = sync.CampaignSync(campaign)
        child_syncs = campaign_sync.get_components()

        self.assertEqual(len(list(child_syncs)), 1)
