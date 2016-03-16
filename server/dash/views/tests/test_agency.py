# -*- coding: utf-8 -*-
import json
import datetime
import pytz

from mock import patch, ANY, Mock, call
from decimal import Decimal

from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.core import mail
from django.contrib.auth.models import Permission
from django.conf import settings
from django.test import Client

from zemauth.models import User
from dash import models
from dash import constants
from dash.views import agency
from dash import forms


class AgencyViewTestCase(TestCase):

    def add_permissions(self, permissions):
        for permission in permissions:
            self.user.user_permissions.add(Permission.objects.get(codename=permission))


class AdGroupSettingsTest(AgencyViewTestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.settings_dict = {
            'settings': {
                'state': 1,
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
                'adobe_tracking_param': 'cid',
                'tracking_code': 'def=123',
                'autopilot_min_budget': '100'
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

        self.add_permissions(['settings_view', 'can_view_retargeting_settings'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )

        self.assertDictEqual(json.loads(response.content), {
            'data': {
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
                    'enable_adobe_tracking': False,
                    'enable_ga_tracking': True,
                    'end_date': '2015-04-02',
                    'id': '1',
                    'name': 'test adgroup 1',
                    'start_date': '2015-03-02',
                    'state': 2,
                    'target_devices': ['desktop', 'mobile'],
                    'target_regions': ['UK', 'US', 'CA'],
                    'tracking_code': 'param1=foo&param2=bar',
                    'autopilot_state': 1,
                    'autopilot_daily_budget': '50.00',
                    'retargeting_ad_groups': [3],
                    'enable_ga_tracking': True,
                    'enable_adobe_tracking': True,
                    'adobe_tracking_param': 'pid',
                    'tracking_code': 'param1=foo&param2=bar',
                    'autopilot_min_budget': '100'
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

        self.add_permissions(['settings_view'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )

        self.assertDictEqual(
            json.loads(response.content)['data']['warnings'], {
                'retargeting': {
                    'text': "You have some active media sources that"
                            " don't support retargeting. To start using it please disable/pause"
                            " these media sources:",
                    'sources': [
                        'AdsNative',
                        'Gravity',
                        'Yahoo',
                    ],
                }
            }
        )

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction, mock_actionlog_api, mock_order_ad_group_settings_update):
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

            self.add_permissions([
                'settings_view',
                'can_set_ad_group_max_cpc',
                'can_toggle_ga_performance_tracking',
                'can_toggle_adobe_performance_tracking',
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
                    'action_is_waiting': True,
                    'default_settings': {
                        'target_devices': ['mobile'],
                        'target_regions': ['NC', '501'],
                    },
                    'settings': {
                        'cpc_cc': '0.30',
                        'daily_budget_cc': '200.00',
                        'end_date': str(datetime.date.today()),
                        'id': '1',
                        'name': 'Test ad group name',
                        'start_date': '2015-05-01',
                        'state': 1,
                        'target_devices': ['desktop'],
                        'target_regions': ['693', 'GB'],
                        'tracking_code': '',
                        'enable_ga_tracking': True,
                        'enable_adobe_tracking': False,
                        'adobe_tracking_param': '',
                        'autopilot_state': 2,
                        'autopilot_daily_budget': '50.00',
                        'retargeting_ad_groups': [2],
                        'enable_ga_tracking': False,
                        'enable_adobe_tracking': False,
                        'adobe_tracking_param': 'cid',
                        'tracking_code': 'def=123',
                        'autopilot_min_budget': '100'
                    }
                },
                'success': True
            })

            new_settings = ad_group.get_current_settings()

            self.assertEqual(new_settings.display_url, 'example.com')
            self.assertEqual(new_settings.brand_name, 'Example')
            self.assertEqual(new_settings.description, 'Example description')
            self.assertEqual(new_settings.call_to_action, 'Call to action')

            # this checks if updates to other settings happen before
            # changing the state of the campaign. This fixes a bug where
            # setting state to enabled and changing end date from past date
            # to a future date at the same time would cause a failed ActionLog
            # on Yahoo because enabling campaign is not possible when
            # end date is in the past.
            mock_manager.assert_has_calls([
                call.mock_order_ad_group_settings_update(
                    ad_group, old_settings, new_settings, ANY, send=False),
                ANY, ANY,  # this is necessary because calls to __iter__ and __len__ happen
                call.mock_actionlog_api.init_set_ad_group_state(ad_group, constants.AdGroupSettingsState.ACTIVE,
                                                                ANY, send=False)
            ])
            mock_log_useraction.assert_called_with(
                response.wsgi_request, constants.UserActionType.SET_AD_GROUP_SETTINGS, ad_group=ad_group)

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

            self.add_permissions(['settings_view', 'can_set_ad_group_max_cpc'])
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

            self.add_permissions(['settings_view', 'can_set_adgroup_to_auto_pilot'])
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

            self.add_permissions([
                'settings_view',
                'can_set_ad_group_max_cpc',
                'can_toggle_ga_performance_tracking',
                'can_toggle_adobe_performance_tracking',
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
                    'action_is_waiting': True,
                    'default_settings': {
                        'target_devices': ['mobile'],
                        'target_regions': ['NC', '501'],
                    },
                    'settings': {
                        'cpc_cc': '0.30',
                        'daily_budget_cc': '200.00',
                        'end_date': str(datetime.date.today()),
                        'id': '10',
                        'name': 'Test ad group name',
                        'start_date': '2015-05-01',
                        'state': 1,
                        'target_devices': ['desktop'],
                        'target_regions': ['693', 'GB'],
                        'tracking_code': '',
                        'enable_ga_tracking': True,
                        'adobe_tracking_param': '',
                        'enable_adobe_tracking': False,
                        'autopilot_state': 2,
                        'autopilot_daily_budget': '0.00',
                        'retargeting_ad_groups': [2],
                        'enable_ga_tracking': False,
                        'enable_adobe_tracking': False,
                        'adobe_tracking_param': 'cid',
                        'tracking_code': 'def=123',
                        'autopilot_min_budget': '100'
                    }
                },
                'success': True
            })

            new_settings = ad_group.get_current_settings()
            self.assertIsNotNone(new_settings.pk)

            mock_actionlog_api.init_set_ad_group_state.assert_called_with(
                ad_group,
                constants.AdGroupSettingsState.ACTIVE,
                ANY,
                send=False)

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

            self.add_permissions(['settings_view', 'can_toggle_ga_performance_tracking'])
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

        self.add_permissions(['settings_view'])
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

        self.add_permissions(['settings_view'])
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

            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            self.settings_dict['settings']['end_date'] = '2015-05-02'

            self.add_permissions(['settings_view'])
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
    def test_enable_without_budget(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=2)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        self.settings_dict['settings']['id'] = 2

        self.add_permissions(['settings_view'])
        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertIn('state', response_dict['data']['errors'])

    @patch('dash.views.agency.api.order_ad_group_settings_update')
    @patch('dash.views.agency.actionlog_api')
    def test_put_set_settings_no_permissions(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            mock_actionlog_api.is_waiting_for_set_actions.return_value = True

            self.add_permissions(['settings_view'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_settings_dict = json.loads(response.content)['data']['settings']

            self.assertNotEqual(response_settings_dict['cpc_cc'], '0.3000')
            self.assertNotEqual(response_settings_dict['enable_ga_tracking'], False)
            self.assertNotEqual(response_settings_dict['tracking_code'], 'def=123')
            self.assertNotEqual(response_settings_dict['enable_adobe_tracking'], False)
            self.assertNotEqual(response_settings_dict['adobe_tracking_param'], 'cid')
            self.assertNotEqual(response_settings_dict['autopilot_state'], 2)
            self.assertNotEqual(response_settings_dict['autopilot_daily_budget'], '0.00')
            self.assertNotEqual(response_settings_dict['retargeting_ad_groups'], [2])


class AdGroupSettingsRetargetableAdgroupsTest(AgencyViewTestCase):
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

        self.add_permissions(['settings_view'])
        response = self._get_retargetable_adgroups(ad_group.id)

        self.assertEqual([], response['data']['retargetable_adgroups'])

    def test_essential(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        self.add_permissions(['settings_view', 'can_view_retargeting_settings'])
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


class AdGroupSettingsStateTest(AgencyViewTestCase):
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

        self.add_permissions(['can_control_ad_group_state_in_table'])
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
    def test_activate(self, mock_zwei_send, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_budget_check.return_value = True

        self.add_permissions(['can_control_ad_group_state_in_table'])
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

    @patch('dash.validation_helpers.ad_group_has_available_budget')
    @patch('actionlog.zwei_actions.send')
    def test_activate_already_activated(self, mock_zwei_send, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_budget_check.return_value = True

        self.add_permissions(['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_zwei_send.called, False)

    @patch('actionlog.zwei_actions.send')
    def test_activate_without_budget(self, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=2)

        self.add_permissions(['can_control_ad_group_state_in_table'])
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
    def test_campaign_in_landing_mode(self, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=2)
        ad_group.campaign.landing_mode = True
        ad_group.campaign.save(None)

        self.add_permissions(['can_control_ad_group_state_in_table'])
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
    def test_inactivate(self, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=1)

        self.add_permissions(['can_control_ad_group_state_in_table'])
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

    @patch('actionlog.zwei_actions.send')
    def test_inactivate_already_inactivated(self, mock_zwei_send):
        ad_group = models.AdGroup.objects.get(pk=2)

        self.add_permissions(['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 2}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_zwei_send.called, False)


class AdGroupAgencyTest(AgencyViewTestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_permissions(self):
        url = reverse('ad_group_agency', kwargs={'ad_group_id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

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
                cpc_cc='1.0000',
                tracking_code=tracking_code,
            )
            settings.save(request)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 24)

            settings = models.AdGroupSettings(
                ad_group=ad_group,
                cpc_cc='2.0000',
                daily_budget_cc='120.0000',
                tracking_code=tracking_code,
            )
            settings.save(request)

        self.add_permissions([
            'ad_group_agency_tab_view',
            'new_content_ads_tab',
            'can_toggle_adobe_performance_tracking'
        ])
        response = self.client.get(
            reverse('ad_group_agency', kwargs={'ad_group_id': ad_group_id}),
            follow=True
        )

        mock_is_waiting.assert_called_once(ad_group)
        self.assertEqual(json.loads(response.content), {
            u'data': {
                u'can_archive': True,
                u'can_restore': True,
                u'history': [{
                    u'changed_by': u'non_superuser@zemanta.com',
                    u'changes_text': u'Created settings',
                    u'datetime': u'2015-06-05T09:22:23',
                    u'settings': [
                        {u'name': u'State', u'value': u'Paused'},
                        {u'name': u'Start date', u'value': None},
                        {u'name': u'End date', u'value': u'I\'ll stop it myself'},
                        {u'name': u'Max CPC bid', u'value': u'$1.00'},
                        {u'name': u'Daily budget', u'value': None},
                        {u'name': u'Device targeting', u'value': u''},
                        {u'name': u'Locations', u'value': u'worldwide'},
                        {u'name': u'Retargeting ad groups', u'value': u''},
                        {u'name': u'Tracking code', u'value': u'test tracking code'},
                        {u'name': u'Archived', u'value': u'False'},
                        {u'name': u'Display URL', u'value': u''},
                        {u'name': u'Brand name', u'value': u''},
                        {u'name': u'Description', u'value': u''},
                        {u'name': u'Call to action', u'value': u''},
                        {u'name': u'Ad group name', u'value': u''},
                        {u'name': u'Enable GA tracking', u'value': u'True'},
                        {u'name': u'GA tracking type (via API or e-mail).', u'value': u'Email'},
                        {u'name': u'Enable Adobe tracking', u'value': u'False'},
                        {u'name': u'Adobe tracking parameter', u'value': u''},
                        {u'name': u'Auto-Pilot', u'value': u'Disabled'},
                        {u'name': u'Auto-Pilot\'s Daily Budget', u'value': u'$0.00'},
                    ],
                    u'show_old_settings': False
                }, {
                    u'changed_by': u'non_superuser@zemanta.com',
                    u'changes_text': u'Daily budget set to "$120.00", Max CPC bid set to "$2.00"',
                    u'datetime': u'2015-06-05T09:22:24',
                    u'settings': [
                        {u'name': u'State', u'old_value': u'Paused', u'value': u'Paused'},
                        {u'name': u'Start date', u'old_value': None, u'value': None},
                        {u'name': u'End date', u'old_value': u'I\'ll stop it myself', u'value': u'I\'ll stop it myself'},
                        {u'name': u'Max CPC bid', u'old_value': u'$1.00', u'value': u'$2.00'},
                        {u'name': u'Daily budget', u'old_value': None, u'value': u'$120.00'},
                        {u'name': u'Device targeting', u'old_value': u'', u'value': u''},
                        {u'name': u'Locations', u'old_value': u'worldwide', u'value': u'worldwide'},
                        {u'name': u'Retargeting ad groups', u'old_value': u'', u'value': u''},
                        {u'name': u'Tracking code', u'old_value': u'test tracking code', u'value': u'test tracking code'},
                        {u'name': u'Archived', u'old_value': u'False', u'value': u'False'},
                        {u'name': u'Display URL', u'old_value': u'', u'value': u''},
                        {u'name': u'Brand name', u'old_value': u'', u'value': u''},
                        {u'name': u'Description', u'old_value': u'', u'value': u''},
                        {u'name': u'Call to action', u'old_value': u'', u'value': u''},
                        {u'name': u'Ad group name', u'old_value': u'', u'value': u''},
                        {u'name': u'Enable GA tracking', u'old_value': u'True', u'value': u'True'},
                        {u'name': u'GA tracking type (via API or e-mail).', u'old_value': u'Email', u'value': u'Email'},
                        {u'name': u'Enable Adobe tracking', u'old_value': u'False', u'value': u'False'},
                        {u'name': u'Adobe tracking parameter', u'old_value': u'', u'value': u''},
                        {u'name': u'Auto-Pilot', u'old_value': u'Disabled', u'value': u'Disabled'},
                        {u'name': u'Auto-Pilot\'s Daily Budget', u'old_value': u'$0.00', u'value': u'$0.00'},
                    ],
                    u'show_old_settings': True
                }]
            },
            u'success': True
        })


class AccountConversionPixelsTestCase(AgencyViewTestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    def test_permissions(self):
        url = reverse('account_conversion_pixels', kwargs={'account_id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    @patch('dash.views.agency.redshift.get_pixels_last_verified_dt')
    def test_get(self, redshift_get_mock):
        utcnow = datetime.datetime.utcnow()
        redshift_get_mock.return_value = {(1, 'test'): utcnow}

        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        self.add_permissions(['manage_conversion_pixels'])
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
        self.add_permissions(['manage_conversion_pixels'])
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': 9876}),
            follow=True
        )

        self.assertEqual(404, response.status_code)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_post(self, mock_log_useraction):
        self.add_permissions(['manage_conversion_pixels'])
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

        latest_account_settings = models.AccountSettings.objects.latest('created_dt')
        self.assertEqual('Added conversion pixel with unique identifier slug.',
                         latest_account_settings.changes_text)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.CREATE_CONVERSION_PIXEL,
            account=models.Account.objects.get(pk=1))

    def test_post_slug_empty(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        self.add_permissions(['manage_conversion_pixels'])
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

        self.add_permissions(['manage_conversion_pixels'])
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

        self.add_permissions(['manage_conversion_pixels'])
        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'a' * (models.ConversionPixel._meta.get_field('slug').max_length + 1)}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)


class ConversionPixelTestCase(AgencyViewTestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    def test_permissions(self):
        url = reverse('conversion_pixel', kwargs={'conversion_pixel_id': 0})

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction):
        self.add_permissions(['manage_conversion_pixels', 'archive_restore_entity'])
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

        latest_account_settings = models.AccountSettings.objects.latest('created_dt')
        self.assertEqual('Archived conversion pixel with unique identifier test.',
                         latest_account_settings.changes_text)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.ARCHIVE_RESTORE_CONVERSION_PIXEL,
            account=models.Account.objects.get(pk=1))

    def test_put_archive_no_permissions(self):
        self.add_permissions(['manage_conversion_pixels'])
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(401, response.status_code)

    def test_put_invalid_pixel(self):
        conversion_pixel = models.ConversionPixel.objects.latest('id')

        self.add_permissions(['manage_conversion_pixels', 'archive_restore_entity'])
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

        self.add_permissions(['manage_conversion_pixels', 'archive_restore_entity'])
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
        self.add_permissions(['manage_conversion_pixels', 'archive_restore_entity'])
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual('Invalid value', decoded_response['data']['message'])


class CampaignConversionGoalsTestCase(AgencyViewTestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    def test_permissions(self):
        url = reverse('campaign_conversion_goals', kwargs={'campaign_id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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

        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 9876}),
            follow=True
        )

        self.assertEqual(404, response.status_code)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_post(self, mock_log_useraction):
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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

        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
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

        self.add_permissions(['manage_conversion_goals'])
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

        self.add_permissions(['manage_conversion_goals'])
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


class ConversionGoalTestCase(AgencyViewTestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    def test_permissions(self):
        url = reverse('conversion_goal', kwargs={'campaign_id': 0, 'conversion_goal_id': 0})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_delete(self, mock_log_useraction):
        conversion_goal = models.ConversionGoal.objects.get(id=1)

        self.add_permissions(['manage_conversion_goals'])
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

        self.add_permissions(['manage_conversion_goals'])
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
        self.add_permissions(['manage_conversion_goals'])
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': 9876}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion goal', decoded_response['data']['message'])

    def test_delete_goal_not_belonging_to_campaign(self):
        self.add_permissions(['manage_conversion_goals'])
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 2, 'conversion_goal_id': 1}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion goal', decoded_response['data']['message'])


class UserActivationTest(AgencyViewTestCase):
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

        self.add_permissions(['account_agency_access_permissions'])
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

        self.add_permissions(['account_agency_access_permissions'])
        response = self.client.post(
            reverse('account_reactivation', kwargs={'account_id': 1, 'user_id': 1}),
            data,
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertFalse(decoded_response.get('success'), 'Failed sending message')


class CampaignAgencyTest(AgencyViewTestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_permissions(self):
        url = '/api/campaigns/1/agency/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        self.add_permissions(['campaign_agency_view'])
        response = self.client.get(
            '/api/campaigns/1/agency/'
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(content['data']['settings']['name'], 'test campaign 1')
        self.assertEqual(content['data']['settings']['iab_category'], 'IAB24')

        self.assertEqual(content['data']['history'], [{
            'datetime': '2014-06-04T05:58:21',
            'changed_by': 'non_superuser@zemanta.com',
            'settings': [
                {'name': 'Name', 'value': ''},
                {'name': 'Campaign Manager', 'value': 'user@test.com'},
                {'name': 'IAB Category', 'value': 'Uncategorized'},
                {'name': 'Campaign Goal', 'value': 'new unique visitors'},
                {'name': 'Goal Quantity', 'value': '0.00'},
                {'name': 'Service Fee', 'value': '20%'},
                {'name': 'Promotion Goal', 'value': 'Brand Building'},
                {'name': 'Archived', 'value': 'False'},
                {'name': 'Device targeting', 'value': 'Mobile'},
                {'name': 'Locations', 'value': 'New Caledonia, 501 New York, NY'}
            ],
            'show_old_settings': False,
            'changes_text': 'Created settings'
        }])

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put(self, mock_send_campaign_notification_email, mock_log_useraction, _):
        self.add_permissions(['campaign_agency_view', 'campaign_settings_account_manager'])
        response = self.client.put(
            '/api/campaigns/1/agency/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'campaign_manager': 1,
                    'iab_category': 'IAB17',
                    'name': 'ignore name'
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])

        campaign = models.Campaign.objects.get(pk=1)
        settings = campaign.get_current_settings()

        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertEqual(settings.campaign_manager_id, 1)
        self.assertEqual(settings.iab_category, 'IAB17')

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request, ANY)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CAMPAIGN_AGENCY_SETTINGS,
            campaign=campaign
        )


class CampaignSettingsTest(AgencyViewTestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_permissions(self):
        url = '/api/campaigns/1/settings/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        self.add_permissions(['campaign_settings_view', 'settings_defaults_on_campaign_level'])
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

    def test_get_no_ad_group_default_settings_permission(self):
        self.add_permissions(['campaign_settings_view'])
        response = self.client.get(
            '/api/campaigns/1/settings/'
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertNotIn('target_devices', content['data']['settings'])
        self.assertNotIn('target_regions', content['data']['settings'])

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put(self, mock_send_campaign_notification_email, mock_log_useraction, _):
        campaign = models.Campaign.objects.get(pk=1)

        settings = campaign.get_current_settings()
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertNotEqual(settings.goal_quantity, 10)
        self.assertNotEqual(settings.campaign_goal, 2)
        self.assertNotEqual(settings.target_devices, ['desktop'])
        self.assertNotEqual(settings.target_regions, ['CA', '502'])

        self.add_permissions(['campaign_settings_view', 'settings_defaults_on_campaign_level'])
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
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])

        settings = campaign.get_current_settings()

        # Check if all fields were updated
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertEqual(settings.goal_quantity, 10)
        self.assertEqual(settings.campaign_goal, 2)
        self.assertEqual(settings.target_devices, ['desktop'])
        self.assertEqual(settings.target_regions, ['CA', '502'])

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request, ANY)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CAMPAIGN_SETTINGS,
            campaign=campaign)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals(self, p1, p2, p3):
        self.add_permissions([
            'campaign_settings_view',
            'settings_defaults_on_campaign_level',
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
                    'modified': {goals[0].pk: '0.2'},
                    'primary': goals[0].pk
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
                    'removed': [{'id': goals[0].pk}],
                    'modified': {},
                    'primary': None
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertFalse(models.CampaignGoal.objects.all())
        self.assertFalse(models.CampaignGoalValue.objects.all())

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_no_ad_group_default_settings_permission(self, mock_send_campaign_notification_email,
                                                         mock_log_useraction, mock_insert_adgroup):
        settings = models.Campaign.objects.get(pk=1).get_current_settings()
        self.assertNotEqual(settings.goal_quantity, Decimal('10.00'))
        self.assertEqual(settings.target_devices, ['mobile'])
        self.assertEqual(settings.target_regions, ['NC', '501'])

        self.add_permissions(['campaign_settings_view'])
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
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertNotIn('target_devices', content['data']['settings'])
        self.assertNotIn('target_regions', content['data']['settings'])

        settings = models.Campaign.objects.get(pk=1).get_current_settings()

        # Goal quantity should change, but target info should stay the same
        self.assertEqual(settings.goal_quantity, Decimal('10.00'))
        self.assertEqual(settings.target_devices, ['mobile'])
        self.assertEqual(settings.target_regions, ['NC', '501'])

    def test_validation(self):
        self.add_permissions(['campaign_settings_view', 'settings_defaults_on_campaign_level'])
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

    def test_validation_no_settings_defaults_permission(self):
        self.add_permissions(['campaign_settings_view'])
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

        self.assertIn('campaign_goal', content['data']['errors'])

        # because target devices were copied from the latest settings,
        # there should be no errors
        self.assertNotIn('target_devices', content['data']['errors'])


class AccountAgencyTest(TestCase):
    fixtures = ['test_views.yaml', 'test_account_agency.yaml']

    @classmethod
    def setUpClass(cls):
        super(AccountAgencyTest, cls).setUpClass()

        permission = Permission.objects.get(codename='campaign_settings_account_manager')
        user = User.objects.get(pk=3)
        user.user_permissions.add(permission)
        user.save()

        permission = Permission.objects.get(codename='campaign_settings_sales_rep')
        user = User.objects.get(pk=1)
        user.user_permissions.add(permission)
        user.save()

    def setUp(self):
        account = models.Account.objects.get(pk=1)
        account.allowed_sources.clear()
        account.allowed_sources.add(1, 2)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)

        for perm in permissions_list:
            permission_object = Permission.objects.get(codename=perm)
            user.user_permissions.add(permission_object)
        user.save()

        client = Client()
        client.login(username=user.email, password=password)
        return client

    def _get_form_with_allowed_sources_dict(self, allowed_sources_dict):
        form = forms.AccountAgencySettingsForm()
        form.cleaned_data = {'allowed_sources': allowed_sources_dict}
        return form

    def test_permissions(self):
        url = reverse('account_agency', kwargs={'account_id': 0})
        client = self._get_client_with_permissions([])

        response = client.get(url)
        self.assertEqual(response.status_code, 401)

        response = client.put(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        client = self._get_client_with_permissions(['account_agency_view'])

        response = client.get(
            reverse('account_agency', kwargs={'account_id': 1}),
            follow=True
        )

        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertDictEqual(content['data']['settings'], {
            'name': 'test account 1',
            'service_fee': '13',
            'default_sales_representative': '3',
            'default_account_manager': '2',
            'id': '1',
            'archived': False
        })

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction):
        client = self._get_client_with_permissions([
            'account_agency_view',
            'can_modify_allowed_sources'
        ])

        response = client.put(
            reverse('account_agency', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'name': 'changed name',
                    'service_fee': '15',
                    'default_sales_representative': '1',
                    'default_account_manager': '3',
                    'id': '1',
                    'allowed_sources': {
                        '1': {'allowed': True}
                    }
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
            'name': 'changed name',
            'service_fee': Decimal('0.1500')
        })
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_ACCOUNT_AGENCY_SETTINGS,
            account=account
        )

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put_no_permission_can_modify_allowed_sources(self, mock_log_useraction):
        client = self._get_client_with_permissions([
            'account_agency_view',
        ])
        response = client.put(
            reverse('account_agency', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'name': 'changed name',
                    'service_fee': '15',
                    'default_sales_representative': '1',
                    'default_account_manager': '3',
                    'id': '1',
                    'allowed_sources': {}
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertFalse(content['success'])

    def test_get_history_multiple(self):
        account = models.Account.objects.get(pk=200)
        view = agency.AccountAgency()
        history = view.get_history(account)

        self.assertEqual(len(history), 5)
        self.assertFalse(history[0]['show_old_settings'])
        self.assertTrue(history[1]['show_old_settings'])
        self.assertTrue(history[-1]['show_old_settings'])

    def test_get_history_initial(self):
        account = models.Account.objects.get(pk=201)
        view = agency.AccountAgency()
        history = view.get_history(account)

        self.assertEqual(len(history), 1)
        self.assertFalse(history[0]['show_old_settings'])

    def test_get_history_empty(self):
        account = models.Account.objects.get(pk=202)
        view = agency.AccountAgency()
        history = view.get_history(account)

        self.assertEqual(history, [])

    def test_convert_settings_to_dict(self):
        old_settings = models.AccountSettings.objects.get(pk=200)
        new_settings = models.AccountSettings.objects.get(pk=201)
        view = agency.AccountAgency()

        settings_dict = view.convert_settings_to_dict(new_settings, old_settings)

        self.assertIsNotNone(settings_dict)
        self.assertEqual(len(settings_dict), 5)
        self.assertIn('name', settings_dict['name'])
        self.assertIn('value', settings_dict['name'])
        self.assertIn('old_value', settings_dict['name'])

    def test_convert_settings_to_dict_old_settings_none(self):
        old_settings = None
        new_settings = models.AccountSettings.objects.get(pk=201)
        view = agency.AccountAgency()

        settings_dict = view.convert_settings_to_dict(new_settings, old_settings)

        self.assertIsNotNone(settings_dict)
        self.assertEqual(len(settings_dict), 5)
        self.assertIn('name', settings_dict['name'])
        self.assertIn('value', settings_dict['name'])
        self.assertNotIn('old_value', settings_dict['name'])

    def test_get_changes_text(self):
        expected_changes_strings = [
            'Created settings',
            'Service Fee set to "10%"',
            'Sales Representative set to "superuser@test.com", Service Fee set to "20%"',
            '',
            'some text',
            'Service Fee set to "10%", some text'
        ]

        view = agency.AccountAgency()
        for i in range(6):
            new_settings_pk = 200 + i
            new_settings = models.AccountSettings.objects.get(pk=new_settings_pk)
            old_settings = models.AccountSettings.objects.get(pk=new_settings_pk - 1) if i > 0 else None
            changes_string = view.get_changes_text(new_settings, old_settings)

            self.assertEqual(changes_string, expected_changes_strings[i])

    def test_get_changes_text_for_media_sources(self):
        view = agency.AccountAgency()

        sources = list(models.Source.objects.all())
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
        view = agency.AccountAgency()
        view.set_allowed_sources(account_settings, account, True, self._get_form_with_allowed_sources_dict({
            1: {'allowed': True},
            2: {'allowed': False},
            3: {'allowed': True}
        }))

        self.assertIsNotNone(account_settings.changes_text)
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
        view = agency.AccountAgency()
        view.set_allowed_sources(
            account_settings,
            account,
            False,  # no permission to remove unreleased source 3
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': False},
                2: {'allowed': False},
                3: {'allowed': False}
            }))
        self.assertIsNotNone(account_settings.changes_text)
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

        view = agency.AccountAgency()
        view.set_allowed_sources(
            account_settings,
            account,
            False,  # no permission to add unreleased source 3
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': False},
                2: {'allowed': True},
                3: {'allowed': True}
            }))
        self.assertIsNotNone(account_settings.changes_text)
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
        view = agency.AccountAgency()
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
        view = agency.AccountAgency()
        view.set_allowed_sources(account_settings, account, True, self._get_form_with_allowed_sources_dict(None))
        self.assertIsNone(account_settings.changes_text)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 2])
        )

    def test_get_allowed_sources(self):
        client = self._get_client_with_permissions([
            'account_agency_view',
            'can_modify_allowed_sources',
            'can_see_all_available_sources'
        ])

        response = client.get(
            reverse('account_agency', kwargs={'account_id': 1}),
            follow=True
        )
        response = json.loads(response.content)

        self.assertEqual(response['data']['settings']['allowed_sources'], {
            '2': {'name': 'Source 2', 'allowed': True, 'released': True},
            '3': {'name': 'Source 3', 'released': False}
        })

    def test_get_allowed_sources_no_released(self):
        client = self._get_client_with_permissions([
            'account_agency_view',
            'can_modify_allowed_sources',
        ])

        response = client.get(
            reverse('account_agency', kwargs={'account_id': 1}),
            follow=True
        )
        response = json.loads(response.content)

        self.assertEqual(response['data']['settings']['allowed_sources'], {
            '2': {'name': 'Source 2', 'allowed': True, 'released': True},
        })

    def test_add_error_to_account_agency_form(self):
        view = agency.AccountAgency()
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
        view = agency.AccountAgency()
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
        view = agency.AccountAgency()
        self.assertEqual(view.get_non_removable_sources(account, []), [])

    def test_get_non_removable_sources_source_not_added(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountAgency()
        self.assertEqual(view.get_non_removable_sources(account, [1]), [])

    def test_get_non_removable_sources_source_not_running(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountAgency()
        self.assertEqual(view.get_non_removable_sources(account, [3]), [])

    def test_get_non_removable_sources_source_running(self):
        account = models.Account.objects.get(pk=111)
        view = agency.AccountAgency()

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

        view = agency.AccountAgency()
        account = models.Account.objects.get(pk=111)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [2])

        ad_group = models.AdGroup.objects.get(pk=11122)
        ad_group.is_demo = True
        ad_group.save(mock_request)

        self.assertEqual(view.get_non_removable_sources(account, [2]), [])

        ad_group.is_demo = False
        ad_group.save(mock_request)

    def test_get_non_removable_sources_archived_campaign(self):
        view = agency.AccountAgency()
        account = models.Account.objects.get(pk=111)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [2])

        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        campaign_settings = models.CampaignSettings.objects.get(pk=1112)
        new_campaign_settings = campaign_settings.copy_settings()
        new_campaign_settings.archived = True
        new_campaign_settings.save(request)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [])
