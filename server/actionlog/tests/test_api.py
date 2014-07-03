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

    @patch('actionlog.zwei_actions.urllib2.urlopen')
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

    @patch('actionlog.zwei_actions.urllib2.urlopen')
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
        patcher_urlopen = patch('actionlog.zwei_actions.urllib2.urlopen')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        _prepare_mock_urlopen(mock_urlopen)

        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    def test_stop_ad_group(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_networks = dashmodels.AdGroupNetwork.objects.filter(ad_group=ad_group)
        api.stop_ad_group(ad_group)

        for ad_group_network in ad_group_networks.all():
            action = models.ActionLog.objects.get(
                ad_group_network=ad_group_network,
            )

            self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': ad_group_network.network.type,
                'action': constants.Action.SET_CAMPAIGN_STATE,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                    'state': dashconstants.AdGroupNetworkSettingsState.INACTIVE,
                },
                'callback_url': callback,
            }
            self.assertEqual(action.payload, payload)

    def test_fetch_ad_group_status(self):
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

            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': ad_group_network.network.type,
                'action': constants.Action.FETCH_CAMPAIGN_STATUS,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                },
                'callback_url': callback,
            }

            self.assertEqual(action.payload, payload)

    def test_fetch_ad_group_reports(self):
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

            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': ad_group_network.network.type,
                'action': constants.Action.FETCH_REPORTS,
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