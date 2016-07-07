# -*- coding: utf-8 -*-
import json
import datetime
import pytz
import httplib

from mock import patch, ANY, Mock, call
from decimal import Decimal

from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.core import mail
from django.conf import settings
from django.test import Client
from requests import Response

from zemauth.models import User
from dash import models
from dash import constants
from dash.views import agency
from dash import forms
from dash import history_helpers

from utils import exc
from utils.test_helper import add_permissions, fake_request


class AdGroupSettingsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.settings_dict = {
            'settings': {
                'start_date': '2015-05-01',
                'end_date': str(datetime.date.today()),
                'cpc_cc': '0.3000',
                'daily_budget_cc': '200.0000',
                'target_devices': ['desktop'],
                'target_regions': ['693', 'GB'],
                'name': 'Test ad group name',
                'id': 1,
                'autopilot_state': 2,
                'autopilot_daily_budget': '150.0000',
                'retargeting_ad_groups': [2],
                'enable_ga_tracking': False,
                'enable_adobe_tracking': False,
                'ga_tracking_type': 2,
                'ga_property_id': 'UA-0123456789-1',
                'adobe_tracking_param': 'cid',
                'tracking_code': 'def=123',
                'autopilot_min_budget': '0'
            }
        }

        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        for account in models.Account.objects.all():
            account.users.add(self.user)

        self.client.login(username=self.user.email, password='secret')

    def test_permissions(self):
        url = reverse('ad_group_settings', kwargs={'ad_group_id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['settings_view', 'can_view_retargeting_settings'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )
        json_blob = json.loads(response.content)
        self.assertDictEqual(json_blob, {
            'data': {
                'can_archive': True,
                'can_restore': True,
                'action_is_waiting': False,
                'default_settings': {
                    'target_devices': ['mobile'],
                    'target_regions': ['NC', '501'],
                },
                'retargetable_adgroups': [
                    {
                        "campaign_name": "test campaign 1",
                        "archived": False,
                        "id": 1, "name": "test adgroup 1",
                    },
                    {
                        "campaign_name": "test campaign 2",
                        "archived": False,
                        "id": 2, "name": "test adgroup 2",
                    },
                    {
                        "campaign_name": "test campaign 1",
                        "archived": False,
                        "id": 9,
                        "name": "test adgroup 9",
                    },
                    {
                        "campaign_name": "test campaign 1",
                        "archived": False,
                        "id": 10, "name": "test adgroup 10",
                    },
                ],
                'settings': {
                    'adobe_tracking_param': '',
                    'cpc_cc': '',
                    'daily_budget_cc': '100.00',
                    'end_date': '2015-04-02',
                    'id': '1',
                    'name': 'test adgroup 1',
                    'start_date': '2015-03-02',
                    'state': 2,
                    'target_devices': ['desktop', 'mobile'],
                    'target_regions': ['GB', 'US', 'CA'],
                    'tracking_code': 'param1=foo&param2=bar',
                    'autopilot_state': 1,
                    'autopilot_daily_budget': '50.00',
                    'retargeting_ad_groups': [3],
                    'enable_ga_tracking': True,
                    'ga_property_id': 'UA-123456789-1',
                    'ga_tracking_type': 1,
                    'enable_adobe_tracking': True,
                    'adobe_tracking_param': 'pid',
                    'tracking_code': 'param1=foo&param2=bar',
                    'autopilot_min_budget': '0',
                    'autopilot_optimization_goal': None
                },
                'warnings': {}
            },
            'success': True
        })

    def test_get_not_retargetable(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        for source in models.Source.objects.all():
            source.supports_retargeting = False
            source.save()

        req = RequestFactory().get('/')
        req.user = User(id=1)

        for source_settings in models.AdGroupSourceSettings.objects.all():
            new_source_settings = source_settings.copy_settings()
            new_source_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_source_settings.save(req)

        add_permissions(self.user, ['settings_view'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )

        self.assertDictEqual(
            json.loads(response.content)['data']['warnings'], {
                'retargeting': {
                    'sources': [
                        'AdsNative',
                        'Gravity',
                        'Yahoo',
                    ],
                }
            }
        )

    def test_get_landing(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        req = RequestFactory().get('/')
        req.user = User(id=1)

        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.landing_mode = True
        new_settings.save(req)

        add_permissions(self.user, ['settings_view'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )

        self.assertDictEqual(
            json.loads(response.content)['data']['warnings'], {
                'end_date': {
                    'campaign_id': 1,
                }
            }
        )

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('utils.k1_helper.update_ad_group')
    def test_put(self, mock_k1_ping, mock_log_useraction, mock_actionlog_api,
                 mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            # we need this to track call order across multiple mocks
            mock_manager = Mock()
            mock_manager.attach_mock(mock_actionlog_api, 'mock_actionlog_api')
            mock_manager.attach_mock(mock_order_ad_group_settings_update, 'mock_order_ad_group_settings_update')

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            add_permissions(self.user, [
                'settings_view',
                'can_set_ad_group_max_cpc',
                'can_set_adgroup_to_auto_pilot',
                'can_view_retargeting_settings'
            ])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )
            mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')

            self.assertEqual(json.loads(response.content), {
                'data': {
                    'action_is_waiting': False,
                    'default_settings': {
                        'target_devices': ['mobile'],
                        'target_regions': ['NC', '501'],
                    },
                    'settings': {
                        'cpc_cc': '0.300',
                        'daily_budget_cc': '200.00',
                        'end_date': str(datetime.date.today()),
                        'id': '1',
                        'name': 'Test ad group name',
                        'start_date': '2015-05-01',
                        'state': 2,
                        'target_devices': ['desktop'],
                        'target_regions': ['693', 'GB'],
                        'tracking_code': '',
                        'adobe_tracking_param': '',
                        'autopilot_state': 2,
                        'autopilot_daily_budget': '50.00',
                        'retargeting_ad_groups': [2],
                        'enable_ga_tracking': False,
                        'ga_property_id': 'UA-123456789-1',
                        'ga_tracking_type': 1,
                        'enable_adobe_tracking': False,
                        'adobe_tracking_param': 'cid',
                        'tracking_code': 'def=123',
                        'autopilot_min_budget': '0',
                        'autopilot_optimization_goal': None
                    }
                },
                'success': True
            })

            new_settings = ad_group.get_current_settings()

            self.assertEqual(new_settings.display_url, 'example.com')
            self.assertEqual(new_settings.brand_name, 'Example')
            self.assertEqual(new_settings.description, 'Example description')
            self.assertEqual(new_settings.call_to_action, 'Call to action')

            mock_manager.assert_has_calls([
                call.mock_order_ad_group_settings_update(
                    ad_group, old_settings, new_settings, ANY, send=False),
                ANY, ANY,  # this is necessary because calls to __iter__ and __len__ happen
            ])
            mock_log_useraction.assert_called_with(
                response.wsgi_request, constants.UserActionType.SET_AD_GROUP_SETTINGS, ad_group=ad_group)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('utils.k1_helper.update_ad_group')
    def test_put_low_cpc(self, mock_k1_ping, mock_log_useraction, mock_actionlog_api,
                         mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            # we need this to track call order across multiple mocks
            mock_manager = Mock()
            mock_manager.attach_mock(mock_actionlog_api, 'mock_actionlog_api')
            mock_manager.attach_mock(mock_order_ad_group_settings_update, 'mock_order_ad_group_settings_update')

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            add_permissions(self.user, [
                'settings_view',
                'can_set_ad_group_max_cpc',
                'can_set_adgroup_to_auto_pilot',
                'can_view_retargeting_settings'
            ])
            new_settings = {}
            new_settings.update(self.settings_dict)
            new_settings['settings']['cpc_cc'] = '0.04'

            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(new_settings),
                follow=True
            )
            print response
            mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')

            self.assertEqual(json.loads(response.content), {
                'data': {
                    'action_is_waiting': False,
                    'default_settings': {
                        'target_devices': ['mobile'],
                        'target_regions': ['NC', '501'],
                    },
                    'settings': {
                        'cpc_cc': '0.040',
                        'daily_budget_cc': '200.00',
                        'end_date': str(datetime.date.today()),
                        'id': '1',
                        'name': 'Test ad group name',
                        'start_date': '2015-05-01',
                        'state': 2,
                        'target_devices': ['desktop'],
                        'target_regions': ['693', 'GB'],
                        'tracking_code': '',
                        'adobe_tracking_param': '',
                        'autopilot_state': 2,
                        'autopilot_daily_budget': '50.00',
                        'retargeting_ad_groups': [2],
                        'enable_ga_tracking': False,
                        'ga_property_id': 'UA-123456789-1',
                        'ga_tracking_type': 1,
                        'enable_adobe_tracking': False,
                        'adobe_tracking_param': 'cid',
                        'tracking_code': 'def=123',
                        'autopilot_min_budget': '0',
                        'autopilot_optimization_goal': None
                    }
                },
                'success': True
            })

            new_settings = ad_group.get_current_settings()

            self.assertEqual(new_settings.display_url, 'example.com')
            self.assertEqual(new_settings.brand_name, 'Example')
            self.assertEqual(new_settings.description, 'Example description')
            self.assertEqual(new_settings.call_to_action, 'Call to action')

            for ags in ad_group.adgroupsource_set.all():
                cpc = ags.get_current_settings().cpc_cc
                # All cpc are adjusted to be lower or equal to 0.04
                self.assertTrue(cpc <= Decimal('0.04'))

            mock_manager.assert_has_calls([
                call.mock_order_ad_group_settings_update(
                    ad_group, old_settings, new_settings, ANY, send=False),
                ANY, ANY,  # this is necessary because calls to __iter__ and __len__ happen
            ])
            mock_log_useraction.assert_called_with(
                response.wsgi_request, constants.UserActionType.SET_AD_GROUP_SETTINGS, ad_group=ad_group)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('utils.k1_helper.update_ad_group')
    def test_put_add_ga_analytics(self, mock_k1_ping, mock_log_useraction, mock_actionlog_api,
                                  mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            add_permissions(self.user, [
                'settings_view',
                'can_set_ad_group_max_cpc',
                'can_set_adgroup_to_auto_pilot',
                'can_view_retargeting_settings',
                'can_set_ga_api_tracking'
            ])
            self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            new_settings = ad_group.get_current_settings()
            self.assertEquals(models.GAAnalyticsAccount.objects.filter(
                account=ad_group.campaign.account,
                ga_web_property_id=new_settings.ga_property_id).count(), 1)

            # put again - this time no new GAAnalyticsAccount should be created
            self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            new_settings = ad_group.get_current_settings()
            self.assertEquals(models.GAAnalyticsAccount.objects.filter(
                account=ad_group.campaign.account,
                ga_web_property_id=new_settings.ga_property_id).count(), 1)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_put_without_non_propagated_settings(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            mock_actionlog_api.is_waiting_for_set_actions.return_value = True
            old_settings = ad_group.get_current_settings()

            self.assertIsNotNone(old_settings.pk)

            self.settings_dict['settings']['cpc_cc'] = None
            self.settings_dict['settings']['daily_budget_cc'] = None

            add_permissions(self.user, ['settings_view', 'can_set_ad_group_max_cpc'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_settings_dict = json.loads(response.content)['data']['settings']

            self.assertEqual(response_settings_dict['cpc_cc'], '')
            self.assertEqual(response_settings_dict['daily_budget_cc'], '')

            new_settings = ad_group.get_current_settings()
            new_settings_copy = new_settings.copy_settings()

            request = HttpRequest()
            request.user = User(id=1)

            # can it actually be saved to the db
            new_settings_copy.save(request)

            self.assertEqual(new_settings.cpc_cc, None)
            self.assertEqual(new_settings.daily_budget_cc, None)

            mock_order_ad_group_settings_update.assert_called_with(
                ad_group, old_settings, new_settings, ANY, send=False)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    @patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group')
    def test_put_set_budget_autopilot_triggers_budget_reallocation(
            self, mock_actionlog_api, mock_order_ad_group_settings_update, mock_init_autopilot):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            mock_actionlog_api.is_waiting_for_set_actions.return_value = True
            old_settings = ad_group.get_current_settings()
            new_settings = old_settings.copy_settings()
            new_settings.autopilot_state = 2
            new_settings.save(None)
            mock_actionlog_api.is_waiting_for_set_actions.return_value = True
            self.assertIsNotNone(old_settings.pk)
            self.settings_dict['settings']['autopilot_state'] = 1
            self.settings_dict['settings']['autopilot_daily_budget'] = '200.00'

            add_permissions(self.user, ['settings_view', 'can_set_adgroup_to_auto_pilot'])
            self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            new_settings = ad_group.get_current_settings().copy_settings()

            request = HttpRequest()
            request.user = User(id=1)

            # can it actually be saved to the db
            new_settings.save(request)

            self.assertEqual(new_settings.autopilot_state, 1)
            self.assertEqual(new_settings.autopilot_daily_budget, Decimal('200'))

            self.assertEqual(mock_init_autopilot.called, True)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put_firsttime_create_settings(self, mock_log_useraction, mock_actionlog_api,
                                           mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=10)

            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            # this ad group does not have settings
            current_settings = ad_group.get_current_settings()
            self.assertIsNone(current_settings.pk)

            self.settings_dict['settings']['id'] = 10

            add_permissions(self.user, [
                'settings_view',
                'can_set_ad_group_max_cpc',
                'can_set_adgroup_to_auto_pilot',
                'can_view_retargeting_settings'
            ])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            self.assertEqual(json.loads(response.content), {
                'data': {
                    'action_is_waiting': False,
                    'default_settings': {
                        'target_devices': ['mobile'],
                        'target_regions': ['NC', '501'],
                    },
                    'settings': {
                        'cpc_cc': '0.300',
                        'daily_budget_cc': '200.00',
                        'end_date': str(datetime.date.today()),
                        'id': '10',
                        'name': 'Test ad group name',
                        'start_date': '2015-05-01',
                        'state': 2,
                        'target_devices': ['desktop'],
                        'target_regions': ['693', 'GB'],
                        'tracking_code': '',
                        'enable_ga_tracking': True,
                        'adobe_tracking_param': '',
                        'enable_adobe_tracking': False,
                        'autopilot_state': 2,
                        'ga_property_id': '',
                        'ga_tracking_type': 1,
                        'autopilot_daily_budget': '0.00',
                        'retargeting_ad_groups': [2],
                        'enable_ga_tracking': False,
                        'enable_adobe_tracking': False,
                        'adobe_tracking_param': 'cid',
                        'tracking_code': 'def=123',
                        'autopilot_min_budget': '0',
                        'autopilot_optimization_goal': None
                    }
                },
                'success': True
            })

            new_settings = ad_group.get_current_settings()
            self.assertIsNotNone(new_settings.pk)

            # uses 'ANY' instead of 'current_settings' because before settings are created, the
            # 'get_current_settings' returns a new AdGroupSettings instance each time
            mock_order_ad_group_settings_update.assert_called_with(
                ad_group, ANY, new_settings, response.wsgi_request, send=False)

            # when saving settings, previous ad_group.name gets added to previous settings
            # - and the only time it makes a real difference is the first time the settings are
            # saved
            current_settings.ad_group_name = 'test adgroup 10'

            self.assertDictEqual(
                mock_order_ad_group_settings_update.call_args[0][1].get_settings_dict(),
                current_settings.get_settings_dict()
            )

            mock_log_useraction.assert_called_with(
                response.wsgi_request,
                constants.UserActionType.SET_AD_GROUP_SETTINGS,
                ad_group=ad_group)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_put_tracking_codes_with_permission(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            self.settings_dict['settings']['tracking_code'] = 'asd=123'
            self.settings_dict['settings']['enable_ga_tracking'] = False

            add_permissions(self.user, ['settings_view'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_settings_dict = json.loads(response.content)['data']['settings']

            self.assertEqual(response_settings_dict['tracking_code'], 'asd=123')
            self.assertEqual(response_settings_dict['enable_ga_tracking'], False)

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_put_invalid_target_region(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        self.settings_dict['settings']['target_regions'] = ["123"]

        add_permissions(self.user, ['settings_view'])
        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertIn('target_regions', response_dict['data']['errors'])

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_put_us_and_dmas(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        self.settings_dict['settings']['target_regions'] = ['US', '693']

        add_permissions(self.user, ['settings_view'])
        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertIn('target_regions', response_dict['data']['errors'])

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_end_date_in_the_past(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            new_settings = ad_group.get_current_settings().copy_settings()
            new_settings.state = constants.AdGroupSettingsState.ACTIVE
            new_settings.save(None)

            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            self.settings_dict['settings']['end_date'] = '2015-05-02'

            add_permissions(self.user, ['settings_view'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_dict = json.loads(response.content)
            self.assertFalse(response_dict['success'])
            self.assertIn('end_date', response_dict['data']['errors'])

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_put_set_settings_no_permissions(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            add_permissions(self.user, ['settings_view'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_settings_dict = json.loads(response.content)['data']['settings']

            self.assertNotEqual(response_settings_dict['cpc_cc'], '0.3000')
            self.assertNotEqual(response_settings_dict['autopilot_state'], 2)
            self.assertNotEqual(response_settings_dict['autopilot_daily_budget'], '0.00')
            self.assertNotEqual(response_settings_dict['retargeting_ad_groups'], [2])
            self.assertNotEqual(response_settings_dict['ga_tracking_type'], 2)
            self.assertNotEqual(response_settings_dict['ga_property_id'], 'UA-0123456789-1')


class AdGroupSettingsRetargetableAdgroupsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        for account in models.Account.objects.all():
            account.users.add(self.user)

        self.client.login(username=self.user.email, password='secret')

    def _get_retargetable_adgroups(self, ad_group_id):
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group_id}),
            follow=True
        )
        return json.loads(response.content)

    def test_permissions(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['settings_view'])
        response = self._get_retargetable_adgroups(ad_group.id)

        self.assertEqual([], response['data']['retargetable_adgroups'])

    def test_essential(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['settings_view', 'can_view_retargeting_settings'])
        response = self._get_retargetable_adgroups(ad_group.id)

        self.assertTrue(response['success'])

        adgroups = response['data']['retargetable_adgroups']
        self.assertEqual(4, len(adgroups))
        self.assertEqual([1, 2, 9, 10], sorted([adg['id'] for adg in adgroups]))
        self.assertTrue(all([not adgroup['archived'] for adgroup in adgroups]))

        req = RequestFactory().get('/')
        req.user = self.user
        for adgs in models.AdGroup.objects.filter(campaign__account__id=1):
            adgs.archived = True
            adgs.save(req)

        response = self._get_retargetable_adgroups(ad_group.id)
        self.assertTrue(response['success'])

        adgroups = response['data']['retargetable_adgroups']
        self.assertEqual(4, len(adgroups))
        self.assertFalse(any([adgroup['archived'] for adgroup in adgroups]))


class AdGroupSettingsStateTest(TestCase):
    fixtures = ['test_models.yaml', 'test_adgroup_settings_state.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        self.client.login(username=self.user.email, password='secret')

    def test_permissions(self):
        url = reverse('ad_group_settings_state', kwargs={'ad_group_id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.get(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            follow=True,
        )

        self.assertDictEqual(json.loads(response.content), {
            'data': {
                'id': str(ad_group.pk),
                'state': ad_group.get_current_settings().state
            },
            'success': True
        })

    @patch('dash.validation_helpers.ad_group_has_available_budget')
    @patch('actionlog.zwei_actions.send')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate(self, mock_k1_ping, mock_zwei_send, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_budget_check.return_value = True

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create(campaign_id=ad_group.campaign_id)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_zwei_send.called, True)
        self.assertEqual(len(mock_zwei_send.call_args), 2)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.ACTIVE)
        mock_k1_ping.assert_called_with(2, msg='AdGroupSettingsState.post')

    @patch('dash.validation_helpers.ad_group_has_available_budget')
    @patch('actionlog.zwei_actions.send')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate_already_activated(self, mock_k1_ping, mock_zwei_send, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_budget_check.return_value = True

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create(campaign_id=ad_group.campaign_id)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_zwei_send.called, False)
        self.assertFalse(mock_k1_ping.called)

    @patch('actionlog.zwei_actions.send')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate_without_budget(self, mock_k1_ping, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=2)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(mock_zwei_send.called, False)
        self.assertFalse(mock_k1_ping.called)

    @patch('dash.validation_helpers.ad_group_has_available_budget')
    @patch('actionlog.zwei_actions.send')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate_no_goals(self, mock_k1_ping, mock_zwei_send, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_budget_check.return_value = True

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 400)

    @patch('actionlog.zwei_actions.send')
    def test_campaign_in_landing_mode(self, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=2)
        new_campaign_settings = ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(mock_zwei_send.called, False)

    @patch('actionlog.zwei_actions.send')
    @patch('utils.k1_helper.update_ad_group')
    def test_inactivate(self, mock_k1_ping, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 2}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_zwei_send.called, True)
        self.assertEqual(len(mock_zwei_send.call_args[0]), 1)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        mock_k1_ping.assert_called_with(1, msg='AdGroupSettingsState.post')

    @patch('actionlog.zwei_actions.send')
    def test_inactivate_already_inactivated(self, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=2)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 2}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_zwei_send.called, False)


class AccountConversionPixelsTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    @patch('dash.views.agency.redshift.get_pixels_last_verified_dt')
    def test_get(self, redshift_get_mock):
        utcnow = datetime.datetime.utcnow()
        redshift_get_mock.return_value = {(1, 'test'): utcnow}

        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': account.id}),
            follow=True
        )

        decoded_response = json.loads(response.content)
        tz_now = pytz.utc.localize(utcnow).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertEqual([{
            'id': 1,
            'slug': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'status': constants.ConversionPixelStatus.get_text(constants.ConversionPixelStatus.ACTIVE),
            'last_verified_dt': tz_now.isoformat(),
            'archived': False
        }], decoded_response['data']['rows'])

    def test_get_non_existing_account(self):
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': 9876}),
            follow=True
        )

        self.assertEqual(404, response.status_code)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_post(self, mock_log_useraction):
        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'slug'}),
            content_type='application/json',
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertEqual({
            'id': 2,
            'slug': 'slug',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/slug/',
            'status': constants.ConversionPixelStatus.get_text(constants.ConversionPixelStatus.NOT_USED),
            'last_verified_dt': None,
            'archived': False,
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_CREATE,
            hist.action_type)
        self.assertEqual('Added conversion pixel with unique identifier slug.',
                         hist.changes_text)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.CREATE_CONVERSION_PIXEL,
            account=models.Account.objects.get(pk=1))

    def test_post_slug_empty(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': ''}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    def test_post_slug_invalid_chars(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'A'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': '1'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'č'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': '-'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': '_'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    def test_post_slug_too_long(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'a' * (models.ConversionPixel._meta.get_field('slug').max_length + 1)}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)


class ConversionPixelTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction):
        add_permissions(self.user, ['archive_restore_entity'])
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({
            'id': 1,
            'archived': True,
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_ARCHIVE_RESTORE,
            hist.action_type)
        self.assertEqual('Archived conversion pixel with unique identifier test.',
                         hist.changes_text)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.ARCHIVE_RESTORE_CONVERSION_PIXEL,
            account=models.Account.objects.get(pk=1))

    def test_put_archive_no_permissions(self):
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(401, response.status_code)

    def test_put_invalid_pixel(self):
        conversion_pixel = models.ConversionPixel.objects.latest('id')

        add_permissions(self.user, ['archive_restore_entity'])
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': conversion_pixel.id + 1}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual('Conversion pixel does not exist', decoded_response['data']['message'])

    def test_put_invalid_account(self):
        new_conversion_pixel = models.ConversionPixel.objects.create(account_id=2, slug='abcd')

        add_permissions(self.user, ['archive_restore_entity'])
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': new_conversion_pixel.id}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual('Conversion pixel does not exist', decoded_response['data']['message'])

    def test_put_invalid_archived_value(self):
        add_permissions(self.user, ['archive_restore_entity'])
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual('Invalid value', decoded_response['data']['message'])


class CampaignConversionGoalsTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    def test_get(self):
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        expected_goals = [
            {
                'id': 2,
                'type': 2,
                'name': 'test conversion goal 2',
                'conversion_window': None,
                'goal_id': '2',
            }, {
                'id': 1,
                'type': 1,
                'name': 'test conversion goal',
                'conversion_window': 168,
                'goal_id': '1',
                'pixel': {
                    'id': 1,
                    'slug': 'test',
                    'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
                    'archived': False,
                },
            },
            {
                'id': 5,
                'goal_id': '5',
                'name': 'test conversion goal 5',
                'conversion_window': None,
                'type': 3,
            },
            {
                'id': 4,
                'goal_id': '4',
                'name': 'test conversion goal 4',
                'conversion_window': None,
                'type': 3
            },
            {
                'id': 3,
                'goal_id': '3',
                'name': 'test conversion goal 3',
                'conversion_window': None,
                'type': 2
            },
        ]
        expected_available_pixels = [{
            'id': 1,
            'slug': 'test'
        }]

        self.assertItemsEqual(expected_goals, decoded_response['data']['rows'])
        self.assertItemsEqual(expected_available_pixels, decoded_response['data']['available_pixels'])

    def test_get_campaign_no_permissions(self):
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 3}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        models.Account.objects.get(id=2).users.add(User.objects.get(id=1))
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 3}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_get_available_pixels(self):
        new_pixel = models.ConversionPixel.objects.create(
            account_id=1,
            slug='new',
            archived=False,
        )

        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        expected_conversion_goals = [
            {
                'id': 2,
                'type': 2,
                'name': 'test conversion goal 2',
                'conversion_window': None,
                'goal_id': '2',
            },
            {
                'id': 1,
                'type': 1,
                'name': 'test conversion goal',
                'conversion_window': 168,
                'goal_id': '1',
                'pixel': {
                    'id': 1,
                    'slug': 'test',
                    'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
                    'archived': False,
                },
            },
            {
                'id': 5,
                'goal_id': '5',
                'name': 'test conversion goal 5',
                'conversion_window': None,
                'type': 3,
            },
            {
                'id': 4,
                'goal_id': '4',
                'name': 'test conversion goal 4',
                'conversion_window': None,
                'type': 3
            },
            {
                'id': 3,
                'goal_id': '3',
                'name': 'test conversion goal 3',
                'conversion_window': None,
                'type': 2
            },
        ]
        expected_available_pixels = [{
            'id': 1,
            'slug': 'test',
        }, {
            'id': new_pixel.id,
            'slug': 'new',
        }]

        self.assertItemsEqual(expected_conversion_goals, decoded_response['data']['rows'])
        self.assertItemsEqual(expected_available_pixels, decoded_response['data']['available_pixels'])

    def test_get_non_existing_campaign(self):
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 9876}),
            follow=True
        )

        self.assertEqual(404, response.status_code)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_post(self, mock_log_useraction):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 2,
                'goal_id': 'goal',
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({'success': True}, decoded_response)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.CREATE_CONVERSION_GOAL,
            campaign=models.Campaign.objects.get(pk=2)
        )

    def test_post_campaign_no_permission(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 3}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 2,
                'goal_id': 'goal',
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Campaign does not exist', decoded_response['data']['message'])

        models.Account.objects.get(id=2).users.add(User.objects.get(id=1))
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 3}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 2,
                'goal_id': 'goal',
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_post_max_conversion_goals(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 2,
                'goal_id': 'goal',
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Max conversion goals per campaign exceeded', decoded_response['data']['message'])

    def test_post_pixel_no_conversion_window(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 1,
                'goal_id': '98765',
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual(['conversion_window'],  decoded_response['data']['errors'].keys())

    def test_post_not_unique_name(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal',
                'type': 2,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal',
                'type': 2,
                'goal_id': '2'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(400, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({'name': ['This field has to be unique.']}, decoded_response['data']['errors'])

    def test_post_same_name_and_goal_id_different_campaigns(self):
        models.ConversionGoal.objects.all().delete()

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            json.dumps({
                'name': 'conversion goal',
                'type': 2,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal',
                'type': 2,
                'goal_id': '2'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(200, response.status_code)

    def test_post_same_goal_id_different_types(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal',
                'type': 2,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal 2',
                'type': 3,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(200, response.status_code)

    def test_post_not_unique_goal_id(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal',
                'type': 2,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal 2',
                'type': 2,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )

        self.assertEqual(400, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({'goal_id': ['This field has to be unique.']}, decoded_response['data']['errors'])

    def test_post_non_existing_conversion_pixel(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 1,
                'goal_id': '98765',
                'conversion_window': 168,
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion pixel', decoded_response['data']['message'])

    def test_post_archived_conversion_pixel(self):
        data = {
            'name': 'conversion pixel',
            'type': 1,
            'goal_id': '1',
            'conversion_window': 168,
        }

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps(data),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        models.CampaignGoal.objects.latest('created_dt').delete()
        models.ConversionGoal.objects.latest('created_dt').delete()
        models.ConversionPixel.objects.filter(id=1).update(archived=True)

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps(data),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion pixel', decoded_response['data']['message'])

    def test_post_pixel_invalid_account(self):
        models.Account.objects.get(id=2).users.add(User.objects.get(id=1))

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 1,
                'goal_id': '1',
                'conversion_window': 168,
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 3}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 1,
                'goal_id': '1',
                'conversion_window': 168,
            }),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion pixel', decoded_response['data']['message'])


class ConversionGoalTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_delete(self, mock_log_useraction):
        conversion_goal = models.ConversionGoal.objects.get(id=1)

        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': conversion_goal.id}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        with self.assertRaises(models.ConversionGoal.DoesNotExist):
            models.ConversionGoal.objects.get(id=1)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.DELETE_CONVERSION_GOAL,
            campaign=models.Campaign.objects.get(pk=1)
        )

    def test_delete_campaign_no_permissions(self):
        models.Account.objects.get(id=1).users.remove(User.objects.get(id=1))

        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': 1}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        models.Account.objects.get(id=1).users.add(User.objects.get(id=1))
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': 1}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_delete_invalid_conversion_goal(self):
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': 9876}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion goal', decoded_response['data']['message'])

    def test_delete_goal_not_belonging_to_campaign(self):
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 2, 'conversion_goal_id': 1}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion goal', decoded_response['data']['message'])


class UserActivationTest(TestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_permissions(self):
        url = reverse('account_reactivation', kwargs={'account_id': 0, 'user_id': 0})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_send_mail(self):
        request = HttpRequest()
        request.user = User(id=1)

        data = {}

        add_permissions(self.user, ['account_agency_access_permissions'])
        response = self.client.post(
            reverse('account_reactivation', kwargs={'account_id': 1, 'user_id': 1}),
            data,
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertTrue(decoded_response.get('success'))

        self.assertGreater(len(mail.outbox), 0, 'Successfully sent mail.')

        sent_mail = mail.outbox[0]
        self.assertEqual('Welcome to Zemanta!', sent_mail.subject, 'Title must match activation mail')
        self.assertTrue(self.user.email in sent_mail.recipients())

    @patch('utils.email_helper.send_email_to_new_user')  # , mock=Mock(side_effect=User.DoesNotExist))
    def test_send_mail_failure(self, mock):
        request = HttpRequest()
        request.user = User(id=1)

        mock.side_effect = User.DoesNotExist

        data = {}

        add_permissions(self.user, ['account_agency_access_permissions'])
        response = self.client.post(
            reverse('account_reactivation', kwargs={'account_id': 1, 'user_id': 1}),
            data,
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertFalse(decoded_response.get('success'), 'Failed sending message')


class CampaignSettingsTest(TestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_get(self):
        response = self.client.get(
            '/api/campaigns/1/settings/'
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(content['data']['settings']['name'], 'test campaign 1')
        self.assertEqual(content['data']['settings']['campaign_goal'], 3)
        self.assertEqual(content['data']['settings']['goal_quantity'], '0.00')
        self.assertEqual(content['data']['settings']['target_devices'], ['mobile'])
        self.assertEqual(content['data']['settings']['target_regions'], ['NC', '501'])

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    @patch('utils.k1_helper.update_ad_group')
    def test_put(self, mock_k1_ping, mock_send_campaign_notification_email, mock_log_useraction, _):
        add_permissions(self.user, [
            'can_modify_campaign_manager',
            'can_modify_campaign_iab_category',
        ])
        campaign = models.Campaign.objects.get(pk=1)

        settings = campaign.get_current_settings()
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertNotEqual(settings.goal_quantity, 10)
        self.assertNotEqual(settings.campaign_goal, 2)
        self.assertNotEqual(settings.target_devices, ['desktop'])
        self.assertNotEqual(settings.target_regions, ['CA', '502'])

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create(campaign_id=campaign.id)

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'goal_quantity': 10,
                    'target_devices': ['desktop'],
                    'target_regions': ['CA', '502'],
                    'campaign_manager': 1,
                    'iab_category': 'IAB17',
                }
            }),
            content_type='application/json',
        )
        self.assertEqual(mock_k1_ping.call_count, 1)

        content = json.loads(response.content)
        self.assertTrue(content['success'])

        settings = campaign.get_current_settings()

        # Check if all fields were updated
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertEqual(settings.goal_quantity, 10)
        self.assertEqual(settings.campaign_goal, 2)
        self.assertEqual(settings.target_devices, ['desktop'])
        self.assertEqual(settings.target_regions, ['CA', '502'])
        self.assertEqual(settings.campaign_manager_id, 1)
        self.assertEqual(settings.iab_category, 'IAB17')

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request, ANY)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CAMPAIGN_SETTINGS,
            campaign=campaign)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals_added(self, p1, p2, p3):
        add_permissions(self.user, [
            'can_see_campaign_goals'
        ])

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'goal_quantity': 10,
                    'target_devices': ['desktop'],
                    'target_regions': ['CA', '502']
                },
                'goals': {
                    'added': [
                        {'primary': False, 'value': '0.10', 'type': 1, 'conversion_goal': None, 'campaign_id': 1}
                    ],
                    'removed': [],
                    'modified': {},
                    'primary': None
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])

        goals = models.CampaignGoal.objects.filter(campaign_id=1)
        self.assertEqual(goals[0].type, 1)

        values = models.CampaignGoalValue.objects.filter(campaign_goal__campaign_id=1)
        self.assertEqual(values[0].value, Decimal('0.1000'))

        models.ConversionGoal.objects.all().delete()

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'goal_quantity': 10,
                    'target_devices': ['desktop'],
                    'target_regions': ['CA', '502']
                },
                'goals': {
                    'added': [
                        {
                            'primary': False, 'value': '0.10', 'type': 4,
                            'conversion_goal': {'name': 'test', 'goal_id': 'test', 'type': 2},
                            'campaign_id': 2
                        }
                    ],
                    'removed': [],
                    'modified': {},
                    'primary': None
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(models.ConversionGoal.objects.all()[0].name, 'test')

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals_modified(self, p1, p2, p3):
        goal = models.CampaignGoal.objects.create(
            type=1,
            primary=True,
            campaign_id=1,
        )
        models.CampaignGoalValue.objects.create(
            campaign_goal=goal,
            value=Decimal('0.1')
        )

        add_permissions(self.user, [
            'can_see_campaign_goals'
        ])

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'goal_quantity': 10,
                    'target_devices': ['desktop'],
                    'target_regions': ['CA', '502']
                },
                'goals': {
                    'added': [],
                    'removed': [],
                    'modified': {goal.pk: '0.2'},
                    'primary': goal.pk
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertTrue(content['data']['goals'][0]['primary'])

        values = models.CampaignGoalValue.objects.filter(
            campaign_goal__campaign_id=1
        ).order_by('created_dt')
        self.assertEqual(values[0].value, Decimal('0.1000'))
        self.assertEqual(values[1].value, Decimal('0.2000'))

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals_removed(self, p1, p2, p3):

        campaign_id = 1

        # ensure this campaign has more than 1 goal
        models.CampaignGoal.objects.create(campaign_id=campaign_id)

        goal = models.CampaignGoal.objects.create(
            type=1,
            primary=True,
            campaign_id=campaign_id,
        )

        add_permissions(self.user, [
            'can_see_campaign_goals'
        ])

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': campaign_id,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'goal_quantity': 10,
                    'target_devices': ['desktop'],
                    'target_regions': ['CA', '502']
                },
                'goals': {
                    'added': [],
                    'removed': [{'id': goal.pk}],
                    'modified': {},
                    'primary': None
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(1, models.CampaignGoal.objects.all().count())
        self.assertFalse(models.CampaignGoalValue.objects.all())

    def test_validation(self):
        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'target_devices': ['nonexistent'],
                    'target_regions': ['NC', '501']
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertTrue('goal_quantity' in content['data']['errors'])
        self.assertFalse(content['success'])

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 50,
                    'goal_quantity': 10,
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertFalse(content['success'])
        self.assertTrue('campaign_goal' in content['data']['errors'])
        self.assertTrue('target_devices' in content['data']['errors'])

    def test_get_with_conversion_goals(self):

        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['can_see_campaign_goals'])

        convpix = models.ConversionPixel.objects.create(
            account=ad_group.campaign.account,
            slug='janez_slug',
        )
        convg = models.ConversionGoal.objects.create(
            campaign=ad_group.campaign,
            type=constants.ConversionGoalType.PIXEL,
            name='janezjanez',
            pixel=convpix,
            conversion_window=7,
            goal_id='9',
        )

        models.CampaignGoal.objects.create(
            campaign=ad_group.campaign,
            type=constants.CampaignGoalKPI.CPA,
            conversion_goal=convg,
        )

        response = self.client.get(
            '/api/campaigns/1/settings/'
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(1, content['data']['goals'][0]['campaign_id'])
        self.assertDictContainsSubset(
            {
                'name': 'janezjanez',
                'pixel_url': 'https://p1.zemanta.com/p/1/janez_slug/',
            },
            content['data']['goals'][0]['conversion_goal'],
        )


class AccountSettingsTest(TestCase):
    fixtures = ['test_views.yaml', 'test_account_agency.yaml', 'test_agency.yaml', 'test_facebook.yaml']

    @classmethod
    def setUpClass(cls):
        super(AccountSettingsTest, cls).setUpClass()
        user = User.objects.get(pk=1)
        add_permissions(user, ['campaign_settings_sales_rep'])

    def setUp(self):
        account = models.Account.objects.get(pk=1)
        account.allowed_sources.clear()
        account.allowed_sources.add(1, 2)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def _get_form_with_allowed_sources_dict(self, allowed_sources_dict):
        form = forms.AccountSettingsForm()
        form.cleaned_data = {'allowed_sources': allowed_sources_dict}
        return form

    def _put_account_agency(self, client, settings, account_id):
        response = client.put(
            reverse('account_settings', kwargs={'account_id': account_id}),
            json.dumps({
                'settings': settings,
            }),
            content_type='application/json',
        )
        return response, response.json()

    def test_permissions(self):
        url = reverse('account_settings', kwargs={'account_id': 0})
        client = self._get_client_with_permissions([])

        response = client.get(url)
        self.assertEqual(response.status_code, 404)

        response = client.put(url)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
            'can_modify_account_type',
            'can_modify_facebook_page',
        ])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1}),
            follow=True
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertDictEqual(content['data']['settings'], {
            'name': 'test account 1',
            'default_account_manager': '2',
            'account_type': 3,
            'id': '1',
            'archived': False,
            'facebook_status': 'Empty',
        })

    def test_get_as_agency_manager(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
        ])
        user = User.objects.get(pk=2)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()
        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'name': 'Chuck ads',
            'default_account_manager': None,
            'id': '1000',
            'archived': False
        })

        add_permissions(user, ['can_set_account_sales_representative'])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'name': 'Chuck ads',
            'default_account_manager': None,
            'default_sales_representative': None,
            'id': '1000',
            'archived': False,
        })

        add_permissions(user, ['can_modify_allowed_sources'])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'name': 'Chuck ads',
            'default_account_manager': None,
            'default_sales_representative': None,
            'allowed_sources': {u'2': {u'name': u'Source 2', u'released': True},
                                u'100': {u'name': u'AdsNative', u'released': True},
                                u'200': {u'name': u'Facebook', u'released': True}
                                },
            'id': '1000',
            'archived': False,
        })

        add_permissions(user, ['can_modify_account_type'])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'name': 'Chuck ads',
            'default_account_manager': None,
            'default_sales_representative': None,
            'allowed_sources': {u'2': {u'name': u'Source 2', u'released': True},
                                u'100': {u'name': u'AdsNative', u'released': True},
                                u'200': {u'name': u'Facebook', u'released': True}
                                },
            'account_type': constants.AccountType.UNKNOWN,
            'id': '1000',
            'archived': False,
        })

    def test_put_as_agency_manager(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
        ])
        user = User.objects.get(pk=2)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        basic_settings = {
            'id': 1000,
            'name': 'changed name',
            'default_account_manager': '3',
        }

        response, content = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 200)

    def test_put_as_agency_manager_sales_rep(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
        ])
        user = User.objects.get(pk=2)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        basic_settings = {
            'id': 1000,
            'name': 'changed name',
            'default_account_manager': '3',
            'default_sales_representative': '3',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 400, msg='Designated sales rep doesn''t have permission')

        add_permissions(User.objects.get(pk=3), ['campaign_settings_sales_rep'])
        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 401, 'agency manager cannot set sales rep. without permission')

        add_permissions(user, ['can_set_account_sales_representative'])
        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 200)

    def test_put_as_agency_manager_sources(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
        ])
        user = User.objects.get(pk=2)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        basic_settings = {
            'id': 1000,
            'name': 'changed name',
            'default_account_manager': '3',
            'allowed_sources': {
                '1': {'allowed': True},
            },
        }

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 401,
                         msg='Agency manager doesn''t have permission for changing allowed sources')

        add_permissions(user, ['can_modify_allowed_sources'])

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 200)

    def test_get_as_agency_manager_users(self):
        client = self._get_client_with_permissions([
            'can_modify_account_manager'
        ])
        user = User.objects.get(pk=2)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertItemsEqual(response['data']['account_managers'], [
            {
                'id': '2',
                'name': 'user@test.com',
            }
        ])

        johnnie = User.objects.get(pk=1)
        agency_acc = models.Account.objects.get(pk=1000)
        agency_acc.users.add(johnnie)

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertItemsEqual(response['data']['account_managers'], [
            {
                'id': '2',
                'name': 'user@test.com',
            },
            {
                'id': '1',
                'name': 'superuser@test.com',
            }
        ])

    def test_get_no_permission_can_modify_account_type(self):
        client = self._get_client_with_permissions([])
        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'id': '1',
            'archived': False
        })

    @patch('requests.get')
    @patch('requests.post')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction, mock_request, mock_page_id):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
            'can_modify_account_type',
            'can_modify_allowed_sources',
            'can_set_account_sales_representative',
            'can_modify_facebook_page',
        ])
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        response._content = '{"id": "1234"}'
        mock_page_id.return_value = response

        response = client.put(
            reverse('account_settings', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'name': 'changed name',
                    'default_sales_representative': '1',
                    'default_account_manager': '3',
                    'account_type': '4',
                    'id': '1',
                    'allowed_sources': {
                        '1': {'allowed': True}
                    },
                    'facebook_page': 'http://www.facebook.com/dummy_page',
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])

        account = models.Account.objects.get(pk=1)
        account_settings = account.get_current_settings()
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, ])
        )

        self.assertDictEqual(account_settings.get_settings_dict(), {
            'archived': False,
            'default_sales_representative': User.objects.get(pk=1),
            'default_account_manager': User.objects.get(pk=3),
            'account_type': 4,
            'name': 'changed name',
        })
        self.assertEqual(content['data']['settings']['facebook_page'], 'http://www.facebook.com/dummy_page')
        self.assertEqual(content['data']['settings']['facebook_status'], 'Pending')
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_ACCOUNT_AGENCY_SETTINGS,
            account=account
        )

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put_no_permission_can_modify_account_type(self, mock_log_useraction):
        client = self._get_client_with_permissions([
            'can_modify_allowed_sources'
        ])

        response = client.put(
            reverse('account_settings', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'name': 'changed name',
                    'default_sales_representative': '1',
                    'default_account_manager': '3',
                    'account_type': '4',
                    'id': '1',
                    'allowed_sources': {
                        '1': {'allowed': True}
                    },
                    'facebook_page': 'dummy_page',
                }
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put_no_permission_can_modify_allowed_sources(self, mock_log_useraction):
        client = self._get_client_with_permissions([])
        response = client.put(
            reverse('account_settings', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'name': 'changed name',
                    'default_sales_representative': '1',
                    'default_account_manager': '3',
                    'id': '1',
                    'allowed_sources': {},
                    'facebook_page': 'dummy_page',
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertFalse(content['success'])

    def test_get_changes_text_for_media_sources(self):
        view = agency.AccountSettings()

        sources = list(models.Source.objects.all().order_by('id'))
        self.assertEqual(
            view.get_changes_text_for_media_sources(sources[0:1], sources[1:2]),
            'Added allowed media sources (Source 1), Removed allowed media sources (Source 2)'
        )
        self.assertEqual(
            view.get_changes_text_for_media_sources(sources[0:2], sources[2:3]),
            'Added allowed media sources (Source 1, Source 2), Removed allowed media sources (Source 3)'
        )
        self.assertEqual(
            view.get_changes_text_for_media_sources([], []),
            ''
        )
        self.assertEqual(
            view.get_changes_text_for_media_sources(sources[0:1], []),
            'Added allowed media sources (Source 1)'
        )
        self.assertEqual(
            view.get_changes_text_for_media_sources([], sources[1:2]),
            'Removed allowed media sources (Source 2)'
        )

    def test_set_allowed_sources(self):
        account = models.Account.objects.get(pk=1)
        account_settings = account.get_current_settings()
        view = agency.AccountSettings()
        changes_text = view.set_allowed_sources(
            account_settings,
            account,
            True,
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': True},
                2: {'allowed': False},
                3: {'allowed': True}
            })
        )

        self.assertIsNotNone(changes_text)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 3])
        )

    def test_set_allowed_sources_cant_remove_unreleased(self):
        account = models.Account.objects.get(pk=1)
        account.allowed_sources.add(3)  # add an unreleased source
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 2, 3])
        )
        self.assertFalse(models.Source.objects.get(pk=3).released)

        account_settings = account.get_current_settings()
        view = agency.AccountSettings()
        changes_text = view.set_allowed_sources(
            account_settings,
            account,
            False,  # no permission to remove unreleased source 3
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': False},
                2: {'allowed': False},
                3: {'allowed': False}
            }))
        self.assertIsNotNone(changes_text)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([3, ])
        )

    def test_set_allowed_sources_cant_add_unreleased(self):
        account = models.Account.objects.get(pk=1)
        account_settings = account.get_current_settings()
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 2])
        )
        self.assertFalse(models.Source.objects.get(pk=3).released)

        view = agency.AccountSettings()
        changes_text = view.set_allowed_sources(
            account_settings,
            account,
            False,  # no permission to add unreleased source 3
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': False},
                2: {'allowed': True},
                3: {'allowed': True}
            }))
        self.assertIsNotNone(changes_text)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([2, ])
        )

    def test_set_allowed_sources_cant_remove_running_source(self):
        account = models.Account.objects.get(pk=111)
        account_settings = account.get_current_settings()
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([2, 3])
        )
        view = agency.AccountSettings()
        form = self._get_form_with_allowed_sources_dict({
            2: {'allowed': False},
            3: {'allowed': True}
        })

        view.set_allowed_sources(
            account_settings,
            account,
            False,  # no permission to add unreleased source 3
            form
        )

        self.assertEqual(
            dict(form.errors),
            {'allowed_sources': [u'Can\'t save changes because media source Source 2 is still used on this account.']}
        )

    def test_set_allowed_sources_none(self):
        account = models.Account.objects.get(pk=1)
        account_settings = account.get_current_settings()
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 2])
        )
        view = agency.AccountSettings()
        view.set_allowed_sources(account_settings, account, True, self._get_form_with_allowed_sources_dict(None))
        self.assertIsNone(account_settings.changes_text)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 2])
        )

    def test_get_allowed_sources(self):
        client = self._get_client_with_permissions([
            'can_modify_allowed_sources',
            'can_see_all_available_sources'
        ])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1}),
            follow=True
        )
        response = json.loads(response.content)

        self.assertEqual(response['data']['settings']['allowed_sources'], {
            '2': {'name': 'Source 2', 'allowed': True, 'released': True},
            '3': {'name': 'Source 3', 'released': False},
            '100': {'name': 'AdsNative', 'released': True},
            '200': {'name': 'Facebook', 'released': True},
        })

    def test_get_allowed_sources_no_released(self):
        client = self._get_client_with_permissions([
            'can_modify_allowed_sources',
        ])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1}),
            follow=True
        )
        response = json.loads(response.content)

        self.assertEqual(response['data']['settings']['allowed_sources'], {
            '2': {'name': 'Source 2', 'allowed': True, 'released': True},
            '100': {'name': 'AdsNative', 'released': True},
            '200': {'name': 'Facebook', 'released': True},
        })

    def test_add_error_to_account_agency_form(self):
        view = agency.AccountSettings()
        form = self._get_form_with_allowed_sources_dict({})
        view.add_error_to_account_agency_form(form, [1, 2])
        self.assertEqual(
            dict(form.errors),
            {
                'allowed_sources':
                    [u'Can\'t save changes because media sources Source 1, Source 2 are still used on this account.']
            }
        )

    def test_add_error_to_account_agency_single(self):
        view = agency.AccountSettings()
        form = self._get_form_with_allowed_sources_dict({})
        view.add_error_to_account_agency_form(form, [1])
        self.assertEqual(
            dict(form.errors),
            {
                'allowed_sources':
                    [u'Can\'t save changes because media source Source 1 is still used on this account.']
            }
        )

    def test_get_non_removable_sources_empty(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountSettings()
        self.assertEqual(view.get_non_removable_sources(account, []), [])

    def test_get_non_removable_sources_source_not_added(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountSettings()
        self.assertEqual(view.get_non_removable_sources(account, [1]), [])

    def test_get_non_removable_sources_source_not_running(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountSettings()
        self.assertEqual(view.get_non_removable_sources(account, [3]), [])

    def test_get_non_removable_sources_source_running(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountSettings()

        self.assertEqual(view.get_non_removable_sources(account, [2]), [2])

        ad_group_settings = models.AdGroupSettings.objects.get(pk=11122)
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.state = constants.AdGroupSettingsState.INACTIVE
        new_ad_group_settings.save(None)

        self.assertEqual(view.get_non_removable_sources(account, [2]), [])

        new_ad_group_settings = new_ad_group_settings.copy_settings()
        new_ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE
        new_ad_group_settings.save(None)

        self.assertEqual(view.get_non_removable_sources(account, [2]), [2])

    def test_get_non_removable_sources_source_demo(self):
        user = User.objects.get(pk=1)
        mock_request = Mock()
        mock_request.user = user

        view = agency.AccountSettings()
        account = models.Account.objects.get(pk=111)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [2])

        ad_group = models.AdGroup.objects.get(pk=11122)
        ad_group.is_demo = True
        ad_group.save(mock_request)

        self.assertEqual(view.get_non_removable_sources(account, [2]), [])

        ad_group.is_demo = False
        ad_group.save(mock_request)

    def test_get_non_removable_sources_archived_campaign(self):
        view = agency.AccountSettings()
        account = models.Account.objects.get(pk=111)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [2])

        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        campaign_settings = models.CampaignSettings.objects.get(pk=1112)
        new_campaign_settings = campaign_settings.copy_settings()
        new_campaign_settings.archived = True
        new_campaign_settings.save(request)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [])


class AccountUsersTest(TestCase):
    fixtures = ['test_views.yaml', 'test_agency.yaml']

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=1)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_get(self):
        client = self._get_client_with_permissions([
            'account_agency_access_permissions',
        ])
        response = client.get(
            reverse('account_users', kwargs={'account_id': 1}),
        )
        user = User.objects.get(pk=1)

        self.assertIsNone(response.json()['data']['agency_managers'])
        self.assertItemsEqual([
            {
                u'name': u'',
                u'is_active': False,
                u'id': 2,
                u'last_login': u'2014-06-16',
                u'email': u'user@test.com'
            },
            {
                u'name': u'',
                u'is_active': False,
                u'id': 3,
                u'last_login': u'2014-06-16',
                u'email': u'john@test.com'
            },
            {
                u'name': u'',
                u'is_active': True,
                u'id': 1,
                u'last_login': user.last_login.date().isoformat(),
                u'email': u'superuser@test.com'
            }
        ],
            response.json()['data']['users']
        )

    def test_get_agency(self):
        client = self._get_client_with_permissions([
            'account_agency_access_permissions',
        ])

        acc = models.Account.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        acc.agency = agency
        acc.save(fake_request(User.objects.get(pk=1)))

        user = User.objects.get(pk=1)
        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=1)
        response = client.get(
            reverse('account_users', kwargs={'account_id': 1}),
        )

        self.assertItemsEqual([
            {
                u'name': u'',
                u'is_active': True,
                u'id': 1,
                u'last_login': user.last_login.date().isoformat(),
                u'email': u'superuser@test.com'
            }
        ],
            response.json()['data']['agency_managers']
        )

        self.assertItemsEqual([
            {
                u'name': u'',
                u'is_active': False,
                u'id': 2,
                u'last_login': u'2014-06-16',
                u'email': u'user@test.com'
            },
            {
                u'name': u'',
                u'is_active': False,
                u'id': 3,
                u'last_login': u'2014-06-16',
                u'email': u'john@test.com'
            },
            {
                u'name': u'',
                u'is_active': True,
                u'id': 1,
                u'last_login': user.last_login.date().isoformat(),
                u'email': u'superuser@test.com'
            }
        ],
            response.json()['data']['users']
        )


class CampaignContentInsightsTest(TestCase):
    fixtures = ['test_views.yaml']

    def user(self):
        return User.objects.get(pk=2)

    @patch('dash.stats_helper.get_content_ad_stats_with_conversions')
    def test_permission(self, mock_get_stats):
        cis = agency.CampaignContentInsights()
        with self.assertRaises(exc.AuthorizationError):
            cis.get(fake_request(self.user()), 1)

        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(httplib.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [],
                'worst_performer_rows': [],
            },
            'success': True,
        }, json.loads(response.content))

    @patch('dash.stats_helper.get_content_ad_stats_with_conversions')
    def test_basic_archived(self, mock_get_stats):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad = models.ContentAd.objects.create(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1,
            archived=True,
        )

        mock_get_stats.return_value = [
            {
                'content_ad': cad.id,
                'clicks': 1000,
                'impressions': 10000,
            }
        ]
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(httplib.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [],
                'worst_performer_rows': [],
            },
            'success': True,
        }, json.loads(response.content))

    @patch('dash.stats_helper.get_content_ad_stats_with_conversions')
    def test_basic_title_ctr(self, mock_get_stats):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad = models.ContentAd.objects.create(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1
        )

        mock_get_stats.return_value = [
            {
                'content_ad': cad.id,
                'clicks': 1000,
                'impressions': 10000,
            }
        ]
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(httplib.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [
                    {
                        'summary': 'Test Ad',
                        'metric': '10.00%',
                    }
                ],
                'worst_performer_rows': [
                    {
                        'summary': 'Test Ad',
                        'metric': '10.00%',
                    }
                ],
            },
            'success': True,
        }, json.loads(response.content))

    @patch('dash.stats_helper.get_content_ad_stats_with_conversions')
    def test_duplicate_title_ctr(self, mock_get_stats):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad1 = models.ContentAd.objects.create(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1
        )

        cad2 = models.ContentAd.objects.create(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.bidder.com',
            batch_id=1
        )

        mock_get_stats.return_value = [
            {
                'content_ad': cad1.id,
                'clicks': 1000,
                'impressions': 10000,
            },
            {
                'content_ad': cad2.id,
                'clicks': 9000,
                'impressions': 10000,
            }
        ]

        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(httplib.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [
                    {
                        'summary': 'Test Ad',
                        'metric': '50.00%',
                    }
                ],
                'worst_performer_rows': [
                    {
                        'summary': 'Test Ad',
                        'metric': '50.00%',
                    }
                ],
            },
            'success': True,
        }, json.loads(response.content))

    @patch('dash.stats_helper.get_content_ad_stats_with_conversions')
    def test_order_title_ctr(self, mock_get_stats):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad1 = models.ContentAd.objects.create(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1
        )

        cad2 = models.ContentAd.objects.create(
            ad_group=campaign.adgroup_set.first(),
            title='Awesome Ad',
            url='http://www.bidder.com',
            batch_id=1
        )

        mock_get_stats.return_value = [
            {
                'content_ad': cad1.id,
                'clicks': 1,
                'impressions': 1000,
            },
            {
                'content_ad': cad2.id,
                'clicks': 10,
                'impressions': 1000,
            }
        ]

        self.maxDiff = None
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(httplib.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [
                    {
                        'metric': '1.00%',
                        'summary': 'Awesome Ad',
                    },
                    {
                        'metric': '0.10%',
                        'summary': 'Test Ad',
                    }
                ],
                'worst_performer_rows': [
                    {
                        'metric': '1.00%',
                        'summary': 'Awesome Ad',
                    },
                ],
            },
            'success': True,
        }, json.loads(response.content))


class HistoryTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=2)

    def _add_entries(self):
        self.dt = datetime.datetime.utcnow()
        ad_group = models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        account = campaign.account

        models.History.objects.create(
            ad_group=ad_group,
            campaign=campaign,
            account=account,
            type=constants.HistoryType.AD_GROUP,
            level=constants.HistoryLevel.AD_GROUP,
            changes={'name': 'test'},
            changes_text="Name changed to 'test'",
            created_by=self.user,
        )

        models.History.objects.create(
            campaign=campaign,
            account=account,
            type=constants.HistoryType.CAMPAIGN,
            level=constants.HistoryLevel.CAMPAIGN,
            changes={'targeting': ['US']},
            changes_text="Geographic targeting changed to 'US'",
            created_dt=self.dt,
            created_by=self.user,
        )
        models.History.objects.create(
            account=account,
            type=constants.HistoryType.ACCOUNT,
            level=constants.HistoryLevel.ACCOUNT,
            changes={'account_manager': 1},
            changes_text="Account manager changed to 'Janez Novak'",
            created_dt=self.dt,
            created_by=self.user,
        )

    def get_history(self, filters):
        self.client.login(username=self.user.username, password='secret')
        reversed_url = reverse(
            'history',
            kwargs={})
        response = self.client.get(
            reversed_url,
            filters,
            follow=True
        )
        return response.json()

    def test_permission(self):
        response = self.get_history({})
        self.assertFalse(response['success'])

        add_permissions(self.user, ['can_view_new_history_backend'])
        response = self.get_history({})
        self.assertFalse(response['success'])

        response = self.get_history({'campaign': 1})
        self.assertTrue(response['success'])

    def test_get_ad_group_history(self):
        add_permissions(self.user, ['can_view_new_history_backend'])

        history_count = models.History.objects.all().count()
        self.assertEqual(0, history_count)

        self._add_entries()

        response = self.get_history({'ad_group': 1})
        self.assertTrue(response['success'])
        self.assertEqual(1, len(response['data']['history']))

        history = response['data']['history'][0]
        self.assertEqual(self.user.email, history['changed_by'])
        self.assertEqual("Name changed to 'test'", history['changes_text'])

    def test_get_campaign_history(self):
        add_permissions(self.user, ['can_view_new_history_backend'])

        history_count = models.History.objects.all().count()
        self.assertEqual(0, history_count)

        self._add_entries()

        response = self.get_history({'campaign': 1, 'level': constants.HistoryLevel.CAMPAIGN})
        self.assertTrue(response['success'])
        self.assertEqual(1, len(response['data']['history']))

        history = response['data']['history'][0]
        self.assertEqual(self.user.email, history['changed_by'])
        self.assertEqual("Geographic targeting changed to 'US'", history['changes_text'])

        response = self.get_history({'campaign': 1})
        self.assertTrue(response['success'])
        self.assertEqual(2, len(response['data']['history']))

        history = response['data']['history'][0]
        self.assertEqual(self.user.email, history['changed_by'])
        self.assertEqual("Geographic targeting changed to 'US'", history['changes_text'])

        history = response['data']['history'][1]
        self.assertEqual(self.user.email, history['changed_by'])
        self.assertEqual("Name changed to 'test'", history['changes_text'])

    def test_get_account_history(self):
        add_permissions(self.user, ['can_view_new_history_backend'])

        history_count = models.History.objects.all().count()
        self.assertEqual(0, history_count)

        self._add_entries()

        response = self.get_history({'account': 1, 'level': constants.HistoryLevel.ACCOUNT})
        self.assertTrue(response['success'])
        self.assertEqual(1, len(response['data']['history']))

        history = response['data']['history'][0]
        self.assertEqual(self.user.email, history['changed_by'])
        self.assertEqual("Account manager changed to 'Janez Novak'", history['changes_text'])


class AgenciesTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.assertFalse(self.user.is_superuser)

    def get_agencies(self):
        self.client.login(username=self.user.username, password='secret')
        reversed_url = reverse('agencies', kwargs={})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return response.json()

    def test_permission(self):
        response = self.get_agencies()
        self.assertFalse(response['success'])

        add_permissions(self.user, ['can_filter_by_agency'])
        response = self.get_agencies()
        self.assertTrue(response['success'])

    def test_get(self):
        agency = models.Agency(
            name='test'
        )
        agency.save(fake_request(self.user))

        add_permissions(self.user, ['can_filter_by_agency'])
        response = self.get_agencies()
        self.assertTrue(response['success'])
        self.assertEqual({
            'agencies': []
        }, response['data'])

        agency.users.add(self.user)
        agency.save(fake_request(self.user))

        response = self.get_agencies()
        self.assertTrue(response['success'])
        self.assertEqual({
            'agencies': [
                {
                    'id': str(agency.id),
                    'name': 'test',
                }
            ]
        }, response['data'])


class TestHistoryMixin(TestCase):

    class FakeMeta(object):

        def __init__(self, concrete_fields, virtual_fields):
            self.concrete_fields = concrete_fields
            self.virtual_fields = virtual_fields
            self.many_to_many = []

    class HistoryTest(models.HistoryMixin):

        history_fields = ['test_field']

        def __init__(self):
            self._meta = TestHistoryMixin.FakeMeta(
                self.history_fields,
                []
            )
            self.id = None
            self.test_field = ''
            super(TestHistoryMixin.HistoryTest, self).__init__()

        def get_human_prop_name(self, prop):
            return 'Test Field'

        def get_human_value(self, key, value):
            return value

        def get_defaults_dict(self):
            return {}

    def test_snapshot(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual({'test_field': ''}, mix.post_init_state)
        self.assertTrue(mix.post_init_newly_created)

        mix.id = 5
        mix.snapshot(previous=mix)

        self.assertEqual({'test_field': ''}, mix.post_init_state)
        self.assertFalse(mix.post_init_newly_created)

    def test_get_history_dict(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual({'test_field': ''}, mix.get_history_dict())

    def test_get_model_state_changes(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual(
            {},
            mix.get_model_state_changes({'test_field': ''})
        )
        self.assertEqual(
            {'test_field': 'johnny'},
            mix.get_model_state_changes({'test_field': 'johnny'})
        )

    def test_get_history_changes_text(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual(
            'Test Field set to "johnny"',
            mix.get_history_changes_text({'test_field': 'johnny'})
        )

        self.assertEqual(
            '',
            mix.get_history_changes_text({})
        )

    def test_get_changes_text_from_dict(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual(
            'Created settings. Test Field set to "johnny"',
            mix.get_changes_text_from_dict({'test_field': 'johnny'})
        )

        self.assertEqual(
            'Created settings',
            mix.get_changes_text_from_dict({})
        )

    def test_construct_changes(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual(
            ({}, 'Created settings. Settings: 5.'),
            mix.construct_changes('Created settings.', 'Settings: 5.', {})
        )

        self.assertEqual(
            ({'test_field': 'pesa'}, 'Created settings. Settings: 5. Test Field set to "pesa"'),
            mix.construct_changes('Created settings.', 'Settings: 5.', {'test_field': 'pesa'})
        )

        mix.id = 5
        mix.snapshot(previous=mix)

        self.assertEqual(
            ({}, 'Settings: 5.'),
            mix.construct_changes('Created settings.', 'Settings: 5.', {})
        )
        self.assertEqual(
            ({'test_field': 'pesa'}, 'Settings: 5. Test Field set to "pesa"'),
            mix.construct_changes('Created settings.', 'Settings: 5.', {'test_field': 'pesa'})
        )
        self.assertEqual(
            ({}, 'Settings: 5.'),
            mix.construct_changes('Created settings.', 'Settings: 5.', {})
        )


class AdFacebookAccountStatusTest(TestCase):
    fixtures = ['test_views.yaml', 'test_facebook.yaml']

    @patch('dash.facebook_helper.get_all_pages')
    def test_get(self, get_all_pages_mock):
        get_all_pages_mock.return_value = {'123': 'CONFIRMED'}
        client = self._get_client_with_permissions([])
        response = client.get(
            reverse('facebook_account_status', kwargs={'account_id': 100}),
            follow=True
        )
        content = json.loads(response.content)
        self.assertDictEqual(content['data'], {u'status': u'Connected'})
        get_all_pages_mock.assert_called_with('fake_business_id', 'fake_access_token')

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client
