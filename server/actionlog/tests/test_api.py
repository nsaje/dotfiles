# coding: utf-8

import datetime
import httplib
import urlparse
import urllib
import urllib2

from mock import patch, Mock
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from actionlog import api, constants, models, sync
from dash import models as dashmodels
from dash import constants as dashconstants
from utils.test_helper import MockDateTime


def _prepare_mock_urlopen(mock_urlopen, exception=None):
    if exception:
        mock_urlopen.side_effect = exception
        return

    mock_request = Mock()
    mock_request.status_code = httplib.OK
    mock_urlopen.return_value = mock_request


class ZweiActionsTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @patch('utils.request_signer._secure_opener.open')
    def test_log_encrypted_credentials_on_conneciton_success(self, mock_urlopen):
        _prepare_mock_urlopen(mock_urlopen)
        ad_group_source = dashmodels.AdGroupSource.objects.get(id=1)

        sync.AdGroupSourceSync(ad_group_source).trigger_status()
        action = models.ActionLog.objects.latest('created_dt')

        self.assertEqual(action.ad_group_source, ad_group_source)
        self.assertEqual(action.action, constants.Action.FETCH_CAMPAIGN_STATUS)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        self.assertEqual(
            action.payload['credentials'],
            ad_group_source.source_credentials.credentials
        )

    @patch('utils.request_signer._secure_opener.open')
    def test_log_encrypted_credentials_on_conneciton_fail(self, mock_urlopen):
        exception = urllib2.HTTPError(settings.ZWEI_API_URL, 500, "Server is down.", None, None)
        _prepare_mock_urlopen(mock_urlopen, exception=exception)
        ad_group_source = dashmodels.AdGroupSource.objects.get(id=1)

        sync.AdGroupSourceSync(ad_group_source).trigger_status()
        action = models.ActionLog.objects.latest('created_dt')

        self.assertEqual(action.ad_group_source, ad_group_source)
        self.assertEqual(action.action, constants.Action.FETCH_CAMPAIGN_STATUS)
        self.assertEqual(action.state, constants.ActionState.FAILED)

        self.assertEqual(
            action.payload['credentials'],
            ad_group_source.source_credentials.credentials
        )


class ActionLogApiTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        patcher_urlopen = patch('utils.request_signer._secure_opener.open')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        _prepare_mock_urlopen(mock_urlopen)

        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

        self.maxDiff = None

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key


    @patch('actionlog.models.datetime', MockDateTime)
    def test_set_ad_group_source_settings_non_maintenance(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        changes = {
            'state': dashconstants.AdGroupSourceSettingsState.ACTIVE,
            'cpc_cc': 0.33,
            'daily_budget_cc': 100,
        }

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=False)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save()

        api.set_ad_group_source_settings(changes, source_settings.ad_group_source)

        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source
        )

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime(
            '%Y-%m-%dT%H:%M:%S.%f')[:-3]

        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse(
                'api.zwei_callback',
                kwargs={'action_id': action.id})
        )

        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.SET_CAMPAIGN_STATE,
            'expiration_dt': expiration_dt,
            'credentials': ad_group_source.source_credentials.credentials,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'conf': {
                    'cpc_cc': 3300,
                    'daily_budget_cc': 1000000,
                    'state': dashconstants.AdGroupSourceSettingsState.ACTIVE,
                }
            },
            'callback_url': callback,
        }
        self.assertEqual(action.payload, payload)


    @patch('actionlog.models.datetime', MockDateTime)
    def test_set_ad_group_source_settings_maintenance(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        changes = {
            'state': dashconstants.AdGroupSourceSettingsState.ACTIVE,
            'cpc_cc': 0.33,
            'daily_budget_cc': 100,
        }

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=True)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save()

        api.set_ad_group_source_settings(changes, source_settings.ad_group_source)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload, {'args': { 'conf': changes}})


    @patch('actionlog.models.datetime', MockDateTime)
    def test_init_enable_ad_group_non_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=False)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save()

        api.init_enable_ad_group(ad_group)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.ACTIVE})

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save()

        api.init_enable_ad_group(ad_group)

        # Nothing changed, since the source is inactive
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ad_group_source).latest('created_dt'),
                         action)


    @patch('actionlog.models.datetime', MockDateTime)
    def test_init_enable_ad_group_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=True)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save()

        api.init_enable_ad_group(ad_group)

        # No manual action is created
        self.assertEqual(list(models.ActionLog.objects.filter(ad_group_source=ad_group_source)), [])

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save()

        api.init_enable_ad_group(ad_group)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.ACTIVE})


    @patch('actionlog.models.datetime', MockDateTime)
    def test_init_pause_ad_group_non_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=False)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save()

        api.init_pause_ad_group(ad_group)

        action1 = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action1.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action1.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action1.state, constants.ActionState.WAITING)
        self.assertEqual(action1.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.INACTIVE})

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save()

        api.init_pause_ad_group(ad_group)

        action2 = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        # Check if action is sent even ad group source is already paused
        self.assertNotEqual(action1.pk, action2.pk)
        self.assertEqual(action2.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action2.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action2.state, constants.ActionState.WAITING)
        self.assertEqual(action2.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.INACTIVE})

    @patch('actionlog.models.datetime', MockDateTime)
    def test_init_pause_ad_group_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=True)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save()

        api.init_pause_ad_group(ad_group)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.INACTIVE})

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save()

        api.init_pause_ad_group(ad_group)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.INACTIVE})


    @patch('actionlog.models.datetime', MockDateTime)
    def test_fetch_ad_group_status(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_sources = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=False)
        sync.AdGroupSync(ad_group).trigger_status()

        for ad_group_source in ad_group_sources.all():

            action = models.ActionLog.objects.get(
                ad_group_source=ad_group_source,
            )

            self.assertEqual(
                action.action,
                constants.Action.FETCH_CAMPAIGN_STATUS
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'source': ad_group_source.source.source_type.type,
                'action': constants.Action.FETCH_CAMPAIGN_STATUS,
                'expiration_dt': expiration_dt,
                'credentials': ad_group_source.source_credentials.credentials,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                },
                'callback_url': callback,
            }

            self.assertEqual(action.payload, payload)

    @patch('actionlog.models.datetime', MockDateTime)
    def test_fetch_ad_group_reports(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_sources = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=False)
        date = datetime.date(2014, 6, 1)

        ad_group_sync = sync.AdGroupSync(ad_group)
        for ad_group_source_sync in ad_group_sync.get_components():
            ad_group_source_sync.trigger_reports_for_dates([date])

        for ad_group_source in ad_group_sources.all():
            action = models.ActionLog.objects.get(
                ad_group_source=ad_group_source,
            )

            self.assertEqual(action.action, constants.Action.FETCH_REPORTS)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'source': ad_group_source.source.source_type.type,
                'action': constants.Action.FETCH_REPORTS,
                'expiration_dt': expiration_dt,
                'credentials': ad_group_source.source_credentials.credentials,
                'args': {
                    'source_campaign_keys': [ad_group_source.source_campaign_key],
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback
            }
            self.assertEqual(action.payload, payload)

    def test_set_ad_group_property(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_sources = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group)

        prop = 'fake_property'
        value = 'fake_value'

        api.set_ad_group_property(ad_group, prop=prop, value=value)

        for ad_group_source in ad_group_sources.all():
            action = models.ActionLog.objects.get(
                ad_group_source=ad_group_source,
            )

            self.assertEqual(action.action, constants.Action.SET_PROPERTY)
            self.assertEqual(action.action_type, constants.ActionType.MANUAL)

            payload = {
                'property': prop,
                'value': value
            }
            self.assertEqual(action.payload, payload)

    @patch('actionlog.models.datetime', MockDateTime)
    def test_create_campaign(self):

        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group_source_failing = dashmodels.AdGroupSource.objects.get(id=1)

        name = 'Test'

        api.create_campaign(ad_group_source_failing, name)
        self.assertFalse(models.ActionLog.objects.filter(
            ad_group_source=ad_group_source_failing,
            action=constants.Action.CREATE_CAMPAIGN
        ).exists())

        ad_group_source = dashmodels.AdGroupSource.objects.get(id=5)

        api.create_campaign(ad_group_source, name)
        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source,
            action=constants.Action.CREATE_CAMPAIGN
        )

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.CREATE_CAMPAIGN,
            'expiration_dt': expiration_dt,
            'credentials': ad_group_source.source_credentials.credentials,
            'args': {
                'name': name,
                'extra': {
                    'tracking_code': urllib.urlencode(ad_group_source.get_tracking_ids()),
                    'target_regions': [],
                    'target_devices': []
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)

        ad_group_source_extra = dashmodels.AdGroupSource.objects.get(id=8)

        api.create_campaign(ad_group_source_extra, name)
        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source_extra,
            action=constants.Action.CREATE_CAMPAIGN
        )

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        payload = {
            'source': ad_group_source_extra.source.source_type.type,
            'action': constants.Action.CREATE_CAMPAIGN,
            'expiration_dt': expiration_dt,
            'credentials': ad_group_source_extra.source_credentials.credentials,
            'args': {
                'name': name,
                'extra': {
                    'iab_category': 'IAB24',
                    'exclusive_blog_ids': [123456],
                    'tracking_code': urllib.urlencode(ad_group_source_extra.get_tracking_ids()),
                    'target_devices': ['desktop', 'mobile'],
                    'target_regions': ['UK', 'US', 'CA']
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)


class ActionLogApiCancelExpiredTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_actionlog.yaml']

    @patch('actionlog.api.datetime', MockDateTime)
    def test_cancel_expired_actionlogs(self):

        waiting_actionlogs_before = models.ActionLog.objects.filter(
            state=constants.ActionState.WAITING
        )
        self.assertEqual(len(waiting_actionlogs_before), 10)

        api.datetime.utcnow = classmethod(lambda cls: datetime.datetime(2014, 7, 3, 18, 15, 0))
        api.cancel_expired_actionlogs()
        waiting_actionlogs_after = models.ActionLog.objects.filter(
            state=constants.ActionState.WAITING
        )
        self.assertEqual(len(waiting_actionlogs_after), 10)
        self.assertEqual(
            {action.id for action in waiting_actionlogs_before},
            {action.id for action in waiting_actionlogs_after}
        )

        api.datetime.utcnow = classmethod(lambda cls: datetime.datetime(2014, 7, 3, 18, 45, 0))
        api.cancel_expired_actionlogs()
        failed_actionlogs = models.ActionLog.objects.filter(
            state=constants.ActionState.FAILED
        )
        self.assertEqual(len(failed_actionlogs), 10)
        self.assertEqual(
            {action.id for action in failed_actionlogs},
            {action.id for action in waiting_actionlogs_after}
        )


class SetCampaignPropertyTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def test_actionlog_added(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)
        now = datetime.datetime.now()
        api._init_set_campaign_property(ad_group_source, 'test_property', 'test_value', None)
        # check if a new action log object was added
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL,
            ad_group_source=ad_group_source,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value')
        for alog in alogs: 
            alog.delete()

    def test_abort_waiting_actionlog(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)
        now = datetime.datetime.now()
        api._init_set_campaign_property(ad_group_source, 'test_property', 'test_value_1', None)
        # insert a new action
        # if the ad_group_source and property are the same
        # the old one should be set to aborted and the new one should be set to waiting
        api._init_set_campaign_property(ad_group_source, 'test_property', 'test_value_2', None)
        # old action is aborted
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.ABORTED,
            action_type=constants.ActionType.MANUAL,
            ad_group_source=ad_group_source,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value_1')
        for alog in alogs:
            alog.delete()
        #new action is waiting
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL,
            ad_group_source=ad_group_source,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value_2')
        for alog in alogs:
            alog.delete()


class SyncInProgressTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def test_ad_groups_sync_in_progress(self):
        ad_group = dashmodels.AdGroup.objects.get(pk=1)

        self.assertEqual(models.ActionLog.objects.filter(ad_group_source__ad_group=ad_group).count(), 0)

        self.assertEqual(api.is_sync_in_progress([ad_group]), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        self.assertEqual(api.is_sync_in_progress([ad_group]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress([ad_group]), False)

    def test_multiple_ad_groups_sync_in_progress(self):
        ad_group = dashmodels.AdGroup.objects.get(pk=1)
        ad_group2 = dashmodels.AdGroup.objects.get(pk=2)

        self.assertEqual(models.ActionLog.objects.filter(ad_group_source__ad_group__in=[ad_group, ad_group2]).count(), 0)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        alog2 = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=7),
        )
        alog2.save()

        self.assertEqual(api.is_sync_in_progress([ad_group, ad_group2]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()
        self.assertEqual(api.is_sync_in_progress([ad_group, ad_group2]), True)

        alog2.state = constants.ActionState.SUCCESS
        alog2.save()
        self.assertEqual(api.is_sync_in_progress([ad_group, ad_group2]), False)

    def test_accounts_sync_in_progress(self):
        account = dashmodels.Account.objects.get(pk=1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source__ad_group__campaign__account=account).count(), 0)

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.filter(ad_group__campaign__account=account)[0],
        )
        alog.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), False)

    def test_multiple_accounts_sync_in_progress(self):
        account = dashmodels.Account.objects.get(pk=1)
        account2 = dashmodels.Account.objects.get(pk=2)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source__ad_group__campaign__account__in=[account, account2]).count(), 0)

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.filter(ad_group__campaign__account=account)[0],
        )
        alog.save()

        alog2 = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.filter(ad_group__campaign__account=account2)[0],
        )
        alog2.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account, account2]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account, account2]), True)

        alog2.state = constants.ActionState.SUCCESS
        alog2.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account, account2]), False)

    def test_global_sync_in_progress(self):
        self.assertEqual(models.ActionLog.objects.all().count(), 0)

        self.assertEqual(api.is_sync_in_progress(), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        self.assertEqual(api.is_sync_in_progress(), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress(), False)
