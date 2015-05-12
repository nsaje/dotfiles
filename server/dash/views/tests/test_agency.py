import json
import datetime
from mock import patch, ANY

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest

from zemauth.models import User
from dash import models


@patch('dash.views.agency.api.order_ad_group_settings_update')
@patch('dash.views.agency.actionlog_api')
class AdGroupSettingsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def test_put(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        self.maxDiff = None
        user = User.objects.get(pk=1)
        password = 'secret'

        self.client.login(username=user.email, password=password)

        ad_group = models.AdGroup.objects.get(pk=1)

        data = {
            'settings': {
                'state': 1,
                'start_date': '2015-05-01',
                'end_date': '2015-06-30',
                'cpc_cc': '0.3000',
                'daily_budget_cc': '200.0000',
                'target_devices': ['desktop'],
                'target_regions': ['US'],
                'name': 'Test ad group name',
                'id': 1
            }
        }

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        old_settings = ad_group.get_current_settings()

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(data),
            follow=True
        )

        self.assertEqual(json.loads(response.content), {
            'data': {
                'action_is_waiting': True,
                'settings': {
                    'cpc_cc': '0.30',
                    'daily_budget_cc': '200.00',
                    'end_date': '2015-06-30',
                    'id': '1',
                    'name': 'Test ad group name',
                    'start_date': '2015-05-01',
                    'state': 1,
                    'target_devices': ['desktop'],
                    'target_regions': ['US'],
                    'tracking_code': ''
                }
            },
            'success': True
        })

        new_settings = ad_group.get_current_settings()

        self.assertEqual(new_settings.display_url, 'example.com')
        self.assertEqual(new_settings.brand_name, 'Example')
        self.assertEqual(new_settings.description, 'Example description')
        self.assertEqual(new_settings.call_to_action, 'Call to action')

        mock_actionlog_api.init_enable_ad_group.assert_called_with(ad_group, ANY, order=ANY, send=False)
        mock_order_ad_group_settings_update.assert_called_with(
            ad_group, old_settings, new_settings, ANY, send=False)


class AdGroupAgencyTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.maxDiff = None
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)
            self.client.login(username=self.user.email, password=password)

    @patch('dash.views.agency.actionlog_api.is_waiting_for_set_actions')
    def test_get(self, mock_is_waiting):
        mock_is_waiting.return_value = True

        ad_group_id = 1
        tracking_code = 'test tracking code'

        ad_group = models.AdGroup.objects.get(pk=1)

        request = HttpRequest()
        request.user = User(id=1)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 23)

            settings = models.AdGroupSettings(
                ad_group=ad_group,
                cpc_cc='0.4000',
                tracking_code=tracking_code,
            )
            settings.save(request)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 24)

            settings = models.AdGroupSettings(
                ad_group=ad_group,
                cpc_cc='0.3000',
                daily_budget_cc='120.0000',
                tracking_code=tracking_code,
            )
            settings.save(request)

        response = self.client.get(
            reverse('ad_group_agency', kwargs={'ad_group_id': ad_group_id}),
            follow=True
        )

        mock_is_waiting.assert_called_once(ad_group)

        self.assertEqual(json.loads(response.content), {
            'data': {
                'action_is_waiting': True,
                'settings': {
                    'tracking_code': tracking_code,
                    'id': '1'
                },
                'can_archive': True,
                'can_restore': True,
                'history': [{
                    'changed_by': 'superuser@test.com',
                    'changes_text': 'Created settings',
                    'datetime': '2015-06-05T09:22:23',
                    'settings': [
                        {'name': 'State', 'value': 'Paused'},
                        {'name': 'Start date', 'value': None},
                        {'name': 'End date', 'value': 'I\'ll stop it myself'},
                        {'name': 'Max CPC bid', 'value': '$0.40'},
                        {'name': 'Daily budget', 'value': None},
                        {'name': 'Device targeting', 'value': ''},
                        {'name': 'Geographic targeting', 'value': 'worldwide'},
                        {'name': 'Tracking code', 'value': 'test tracking code'},
                        {'name': 'Archived', 'value': 'False'},
                        {'name': 'Display URL', 'value': ''},
                        {'name': 'Brand name', 'value': ''},
                        {'name': 'Description', 'value': ''},
                        {'name': 'Call to action', 'value': ''},
                        {'name': 'AdGroup name', 'value': ''}
                    ],
                    'show_old_settings': False
                },
                {
                    'changed_by': 'superuser@test.com',
                    'changes_text': 'Daily budget set to "$120.00", Max CPC bid set to "$0.30"',
                    'datetime': '2015-06-05T09:22:24',
                    'settings': [
                        {'name': 'State', 'old_value': 'Paused', 'value': 'Paused'},
                        {'name': 'Start date', 'old_value': None, 'value': None},
                        {'name': 'End date', 'old_value': 'I\'ll stop it myself', 'value': 'I\'ll stop it myself'},
                        {'name': 'Max CPC bid', 'old_value': '$0.40', 'value': '$0.30'},
                        {'name': 'Daily budget', 'old_value': None, 'value': '$120.00'},
                        {'name': 'Device targeting', 'old_value': '', 'value': ''},
                        {'name': 'Geographic targeting', 'old_value': 'worldwide', 'value': 'worldwide'},
                        {'name': 'Tracking code', 'old_value': 'test tracking code', 'value': 'test tracking code'},
                        {'name': 'Archived', 'old_value': 'False', 'value': 'False'},
                        {'name': 'Display URL', 'old_value': '', 'value': ''},
                        {'name': 'Brand name', 'old_value': '', 'value': ''},
                        {'name': 'Description', 'old_value': '', 'value': ''},
                        {'name': 'Call to action', 'old_value': '', 'value': ''},
                        {'name': 'AdGroup name', 'old_value': '', 'value': ''}
                    ],
                    'show_old_settings': True
                }]
            },
            'success': True
        })

    @patch('dash.views.agency.actionlog_api.is_waiting_for_set_actions')
    def test_put(self, mock_is_waiting):
        mock_is_waiting.return_value = True

        ad_group_id = 1
        tracking_code = 'code=test'

        ad_group = models.AdGroup.objects.get(pk=1)

        request = HttpRequest()
        request.user = User(id=1)

        data = {
            'settings': {
                'id': '1',
                'tracking_code': tracking_code
            }
        }

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 24)

            response = self.client.put(
                reverse('ad_group_agency', kwargs={'ad_group_id': ad_group_id}),
                json.dumps(data),
                follow=True
            )

        mock_is_waiting.assert_called_once(ad_group)

        self.assertEqual(json.loads(response.content), {
            'data': {
                'action_is_waiting': True,
                'settings': {
                    'tracking_code': tracking_code,
                    'id': '1'
                },
                'can_archive': True,
                'can_restore': True,
                'history': [{
                    'changed_by': 'superuser@test.com',
                    'changes_text': 'Created settings',
                    'datetime': '2015-06-05T09:22:24',
                    'settings': [
                        {'name': 'State', 'value': 'Paused'},
                        {'name': 'Start date', 'value': ANY},
                        {'name': 'End date', 'value': 'I\'ll stop it myself'},
                        {'name': 'Max CPC bid', 'value': '$0.40'},
                        {'name': 'Daily budget', 'value': '$10.00'},
                        {'name': 'Device targeting', 'value': 'Mobile, Desktop'},
                        {'name': 'Geographic targeting', 'value': 'worldwide'},
                        {'name': 'Tracking code', 'value': tracking_code},
                        {'name': 'Archived', 'value': 'False'},
                        {'name': 'Display URL', 'value': ''},
                        {'name': 'Brand name', 'value': ''},
                        {'name': 'Description', 'value': ''},
                        {'name': 'Call to action', 'value': ''},
                        {'name': 'AdGroup name', 'value': ''}
                    ],
                    'show_old_settings': False
                }]
            },
            'success': True
        })
