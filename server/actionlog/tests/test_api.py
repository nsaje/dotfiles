import datetime
import httplib
import urlparse

from mock import patch, Mock
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from actionlog import api, constants, models
from dash import models as dashmodels
from dash import constants as dashconstants


class ActionLogApiTest(TestCase):

    fixtures = ['test_api.yaml']

    def _prepare_mock_urlopen(self, mock_urlopen):
        mock_request = Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

    def setUp(self):
        patcher_urlopen = patch('zweiapi.zwei_actions.urllib2.urlopen')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        self._prepare_mock_urlopen(mock_urlopen)

        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    def test_stop_ad_group(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        api.stop_ad_group(ad_group)

        for network in ad_group.networks.all():
            ad_group_network = dashmodels.AdGroupNetwork.objects.get(
                network=network,
                ad_group=ad_group
            )
            action = models.ActionLog.objects.get(
                ad_group=ad_group,
                network=network
            )

            self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': network.type,
                'action': constants.Action.SET_CAMPAIGN_STATE,
                'credentials': {
                    'username': 'test',
                    'password': 'test'
                },
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                    'state': dashconstants.AdGroupNetworkSettingsState.INACTIVE,
                },
                'callback_url': callback,
            }
            self.assertEqual(action.payload, payload)

    def test_fetch_ad_group_status(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        api.fetch_ad_group_status(ad_group)

        for network in ad_group.networks.all():
            ad_group_network = dashmodels.AdGroupNetwork.objects.get(
                network=network,
                ad_group=ad_group
            )
            action = models.ActionLog.objects.get(
                ad_group=ad_group,
                network=network
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
                'network': network.type,
                'action': constants.Action.FETCH_CAMPAIGN_STATUS,
                'credentials': {
                    'username': 'test',
                    'password': 'test'
                },
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                },
                'callback_url': callback,
            }

            self.assertEqual(action.payload, payload)

    def test_fetch_ad_group_reports(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        date = datetime.date(2014, 6, 1)
        api.fetch_ad_group_reports(ad_group, date=date)

        for network in ad_group.networks.all():
            ad_group_network = dashmodels.AdGroupNetwork.objects.get(
                network=network,
                ad_group=ad_group
            )
            action = models.ActionLog.objects.get(
                ad_group=ad_group,
                network=network
            )

            self.assertEqual(action.action, constants.Action.FETCH_REPORTS)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'network': network.type,
                'action': constants.Action.FETCH_REPORTS,
                'credentials': {
                    'username': 'test',
                    'password': 'test'
                },
                'args': {
                    'partner_campaign_ids': [ad_group_network.network_campaign_key],
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback
            }
            self.assertEqual(action.payload, payload)

    def test_set_ad_group_property(self):
        ad_group = dashmodels.AdGroup.objects.get(id=1)
        prop = {
            'fake_property': 'fake_value',
        }
        api.set_ad_group_property(ad_group, prop=prop)

        for network in ad_group.networks.all():
            action = models.ActionLog.objects.get(
                ad_group=ad_group,
                network=network
            )

            self.assertEqual(action.action, constants.Action.SET_PROPERTY)
            self.assertEqual(action.action_type, constants.ActionType.MANUAL)

            payload = {
                'property': prop
            }
            self.assertEqual(action.payload, payload)
