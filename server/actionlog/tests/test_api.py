import datetime
import httplib
import urlparse
import urllib2

from mock import patch, Mock
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from actionlog import api, constants, models
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
        ad_group_network = dashmodels.AdGroupNetwork.objects.get(id=1)

        api.fetch_ad_group_status(ad_group_network.ad_group, ad_group_network.network)
        action = models.ActionLog.objects.latest('created_dt')

        self.assertEqual(action.ad_group_network, ad_group_network)
        self.assertEqual(action.action, constants.Action.FETCH_CAMPAIGN_STATUS)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        self.assertEqual(
            action.payload['credentials'],
            ad_group_network.network_credentials.credentials
        )

    @patch('utils.request_signer._secure_opener.open')
    def test_log_encrypted_credentials_on_conneciton_fail(self, mock_urlopen):
        exception = urllib2.HTTPError(settings.ZWEI_API_URL, 500, "Server is down.", None, None)
        _prepare_mock_urlopen(mock_urlopen, exception=exception)
        ad_group_network = dashmodels.AdGroupNetwork.objects.get(id=1)

        api.fetch_ad_group_status(ad_group_network.ad_group, ad_group_network.network)
        action = models.ActionLog.objects.latest('created_dt')

        self.assertEqual(action.ad_group_network, ad_group_network)
        self.assertEqual(action.action, constants.Action.FETCH_CAMPAIGN_STATUS)
        self.assertEqual(action.state, constants.ActionState.FAILED)

        self.assertEqual(
            action.payload['credentials'],
            ad_group_network.network_credentials.credentials
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

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @patch('actionlog.models.datetime', MockDateTime)
    def test_stop_ad_group(self):

        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_networks = dashmodels.AdGroupNetwork.objects.filter(ad_group=ad_group)
        api.stop_ad_group(ad_group)

        for ad_group_network in ad_group_networks.all():
            action = models.ActionLog.objects.get(
                ad_group_network=ad_group_network,
            )

            self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S')
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': ad_group_network.network.type,
                'action': constants.Action.SET_CAMPAIGN_STATE,
                'expiration_dt': expiration_dt,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                    'state': dashconstants.AdGroupNetworkSettingsState.INACTIVE,
                },
                'callback_url': callback,
            }
            self.assertEqual(action.payload, payload)

    @patch('actionlog.models.datetime', MockDateTime)
    def test_fetch_ad_group_status(self):

        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_networks = dashmodels.AdGroupNetwork.objects.filter(ad_group=ad_group)
        api.fetch_ad_group_status(ad_group)

        for ad_group_network in ad_group_networks.all():
            action = models.ActionLog.objects.get(
                ad_group_network=ad_group_network,
            )

            self.assertEqual(
                action.action,
                constants.Action.FETCH_CAMPAIGN_STATUS
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S')
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': ad_group_network.network.type,
                'action': constants.Action.FETCH_CAMPAIGN_STATUS,
                'expiration_dt': expiration_dt,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                },
                'callback_url': callback,
            }

            self.assertEqual(action.payload, payload)

    @patch('actionlog.models.datetime', MockDateTime)
    def test_fetch_ad_group_reports(self):

        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_networks = dashmodels.AdGroupNetwork.objects.filter(ad_group=ad_group)
        date = datetime.date(2014, 6, 1)
        api.fetch_ad_group_reports(ad_group, date=date)

        for ad_group_network in ad_group_networks.all():
            action = models.ActionLog.objects.get(
                ad_group_network=ad_group_network,
            )

            self.assertEqual(action.action, constants.Action.FETCH_REPORTS)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime('%Y-%m-%dT%H:%M:%S')
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': ad_group_network.network.type,
                'action': constants.Action.FETCH_REPORTS,
                'expiration_dt': expiration_dt,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_ids': [ad_group_network.network_campaign_key],
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback
            }
            self.assertEqual(action.payload, payload)

    def test_set_ad_group_property(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_networks = dashmodels.AdGroupNetwork.objects.filter(ad_group=ad_group)

        prop = 'fake_property'
        value = 'fake_value'

        api.set_ad_group_property(ad_group, prop=prop, value=value)

        for ad_group_network in ad_group_networks.all():
            action = models.ActionLog.objects.get(
                ad_group_network=ad_group_network,
            )

            self.assertEqual(action.action, constants.Action.SET_PROPERTY)
            self.assertEqual(action.action_type, constants.ActionType.MANUAL)

            payload = {
                'property': prop,
                'value': value
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
        self.assertSequenceEqual(
            [action.id for action in waiting_actionlogs_before],
            [action.id for action in waiting_actionlogs_after]
        )

        api.datetime.utcnow = classmethod(lambda cls: datetime.datetime(2014, 7, 3, 18, 45, 0))
        api.cancel_expired_actionlogs()
        failed_actionlogs = models.ActionLog.objects.filter(
            state=constants.ActionState.FAILED
        )
        self.assertEqual(len(failed_actionlogs), 10)
        self.assertEqual(
            [action.id for action in failed_actionlogs],
            [action.id for action in waiting_actionlogs_after]
        )


class SetCampaignPropertyTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def test_actionlog_added(self):
        ad_group_network = dashmodels.AdGroupNetwork.objects.get(pk=1)
        now = datetime.datetime.now()
        api._init_set_campaign_property(ad_group_network, 'test_property', 'test_value', None)
        # check if a new action log object was added
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL,
            ad_group_network=ad_group_network,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value')
        for alog in alogs: 
            alog.delete()

    def test_abort_waiting_actionlog(self):
        ad_group_network = dashmodels.AdGroupNetwork.objects.get(pk=1)
        now = datetime.datetime.now()
        api._init_set_campaign_property(ad_group_network, 'test_property', 'test_value_1', None)
        # insert a new action
        # if the ad_group_network and property are the same
        # the old one should be set to aborted and the new one should be set to waiting
        api._init_set_campaign_property(ad_group_network, 'test_property', 'test_value_2', None)
        # old action is aborted
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.ABORTED,
            action_type=constants.ActionType.MANUAL,
            ad_group_network=ad_group_network,
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
            ad_group_network=ad_group_network,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value_2')
        for alog in alogs:
            alog.delete()
