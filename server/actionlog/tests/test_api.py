import datetime
import httplib

from mock import patch, Mock
from django.test import TestCase
from django.core.urlresolvers import reverse

from actionlog import api, constants, models
from dash import models as dash_models


class ActionLogApiTest(TestCase):

    fixtures = ['test_api.yaml']

    def _prepare_mock_urlopen(self, mock_urlopen):
        mock_request = Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

    def setUp(self):
        patcher_urlopen = patch('actionlog.zwei_actions.urllib2.urlopen')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        self._prepare_mock_urlopen(mock_urlopen)

    def test_stop_ad_group(self):
        ad_group = dash_models.AdGroup.objects.get(id=1)
        api.stop_ad_group(ad_group)

        for network in ad_group.networks.all():
            ad_group_network = dash_models.AdGroupNetwork.objects.get(
                network=network,
                ad_group=ad_group
            )
            action = models.ActionLog.objects.get(
                ad_group=ad_group,
                network=network
            )

            self.assertEqual(action.action, constants.Action.STOP_CAMPAIGN)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

            payload = {
                'network': network.type,
                'action': constants.Action.STOP_CAMPAIGN,
                'partner_campaign_id': ad_group_network.network_campaign_key,
                'callback': reverse(
                    'actions.zwei_callback',
                    kwargs={'action_id': action.id}
                )
            }
            self.assertEqual(action.payload, payload)

    def test_fetch_ad_group_status(self):
        ad_group = dash_models.AdGroup.objects.get(id=1)
        api.fetch_ad_group_status(ad_group)

        for network in ad_group.networks.all():
            ad_group_network = dash_models.AdGroupNetwork.objects.get(
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

            payload = {
                'network': network.type,
                'action': constants.Action.FETCH_CAMPAIGN_STATUS,
                'partner_campaign_id': ad_group_network.network_campaign_key,
                'callback': reverse(
                    'actions.zwei_callback',
                    kwargs={'action_id': action.id}
                )
            }

            self.assertEqual(action.payload, payload)

    def test_fetch_ad_group_reports(self):
        ad_group = dash_models.AdGroup.objects.get(id=1)
        date = datetime.date(2014, 6, 1)
        api.fetch_ad_group_reports(ad_group, date=date)

        for network in ad_group.networks.all():
            ad_group_network = dash_models.AdGroupNetwork.objects.get(
                network=network,
                ad_group=ad_group
            )
            action = models.ActionLog.objects.get(
                ad_group=ad_group,
                network=network
            )

            self.assertEqual(action.action, constants.Action.FETCH_REPORTS)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

            payload = {
                'network': network.type,
                'action': constants.Action.FETCH_REPORTS,
                'partner_campaign_ids': [ad_group_network.network_campaign_key],
                'date': date.strftime('%Y-%m-%d'),
                'callback': reverse(
                    'actions.zwei_callback',
                    kwargs={'action_id': action.id}
                )
            }
            self.assertEqual(action.payload, payload)

    def test_set_ad_group_property(self):
        ad_group = dash_models.AdGroup.objects.get(id=1)
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
