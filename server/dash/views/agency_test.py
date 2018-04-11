# -*- coding: utf-8 -*-
import json
import datetime
import http.client

from mock import patch, ANY, call
from decimal import Decimal

from django.test import TestCase, RequestFactory
from django.contrib.auth import models as authmodels
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
from dash.features import ga
import core.multicurrency

from utils import exc
from utils.magic_mixer import magic_mixer
from utils.test_helper import add_permissions, fake_request


class AdGroupSettingsTest(TestCase):
    fixtures = ['test_api', 'test_views', 'test_non_superuser', 'test_geolocations']

    @classmethod
    def _target_regions_repr(cls, countries=[], regions=[], cities=[], dma=[], postal_codes=[]):
        return dict(countries=countries, regions=regions, cities=cities, dma=dma, postal_codes=postal_codes)

    def setUp(self):
        self.maxDiff = None
        self.settings_dict = {
            'settings': {
                'state': constants.AdGroupRunningStatus.INACTIVE,
                'start_date': '2015-05-01',
                'end_date': str(datetime.date.today()),
                'cpc_cc': '0.3000',
                'max_cpm': '1.6000',
                'daily_budget_cc': '200.0000',
                'target_devices': ['DESKTOP'],
                'target_browsers': [{'name': constants.Browser.CHROME}],
                'target_regions': self._target_regions_repr(dma=['693'], countries=['GB']),
                'exclusion_target_regions': self._target_regions_repr(),
                'name': 'Test ad group name',
                'id': 1,
                'campaign_id': '1',
                'autopilot_state': constants.AdGroupSettingsAutopilotState.INACTIVE,
                'autopilot_daily_budget': '150.0000',
                'retargeting_ad_groups': [2],
                'exclusion_retargeting_ad_groups': [9],
                'interest_targeting': ['fun', 'games'],
                'exclusion_interest_targeting': ['religion', 'weather'],
                'audience_targeting': [1],
                'exclusion_audience_targeting': [4],
                'bluekai_targeting': {
                    'AND': [{'category': 'bluekai:123'},
                            {'OR': [{'category': 'lotame:123'},
                                    {'category': 'outbrain:321'}]}]},
                'bluekai_targeting_old': ['and', 'bluekai:123', ['or', 'lotame:123', 'outbrain:321']],
                'tracking_code': 'def=123',
                'autopilot_min_budget': '10',
                'dayparting': {"monday": [0, 1, 2, 3], "tuesday": [10, 11, 12]},
                'b1_sources_group_enabled': True,
                'b1_sources_group_daily_budget': '500.0000',
                'b1_sources_group_state': 1,
                'b1_sources_group_cpc_cc': '0.25',
                'whitelist_publisher_groups': [1],
                'blacklist_publisher_groups': [1],
                'delivery_type': 2,
                'click_capping_daily_ad_group_max_clicks': 15,
                'click_capping_daily_click_budget': '7.5000',
            }
        }

        self.user = User.objects.get(pk=1)
        add_permissions(self.user, ['can_set_click_capping'])

        self.assertFalse(self.user.is_superuser)

        for account in models.Account.objects.all():
            account.users.add(self.user)

        self.client.login(username=self.user.email, password='secret')

        k1_update_patcher = patch('utils.k1_helper.update_ad_group')
        self.k1_update_mock = k1_update_patcher.start()
        self.addCleanup(k1_update_patcher.stop)

    def test_permissions(self):
        url = reverse('ad_group_settings', kwargs={'ad_group_id': 0})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['settings_view', 'can_view_retargeting_settings'])
        add_permissions(self.user, ['settings_view', 'can_target_custom_audiences'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )
        json_blob = json.loads(response.content)
        self.assertDictEqual(json_blob, {
            'data': {
                'can_archive': True,
                'can_restore': True,
                'archived': False,
                'action_is_waiting': False,
                'default_settings': {
                    'target_devices': ['MOBILE'],
                    'target_os': [],
                    'target_placements': [],
                    'target_regions': self._target_regions_repr(dma=['501'], countries=['NC']),
                    'exclusion_target_regions': self._target_regions_repr(),
                },
                'retargetable_adgroups': [
                    {
                        "campaign_name": "test campaign 1",
                        "archived": False,
                        "id": 1, "name": "test adgroup 1 Čžš",
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
                    {
                        "campaign_name": "test campaign 1",
                        "archived": False,
                        "id": 987, "name": "test adgroup 1",
                    },
                ],
                'audiences': [
                    {
                        'id': 1,
                        'name': 'test audience 1',
                        'archived': False,
                    },
                    {
                        'id': 2,
                        'name': 'test audience 2',
                        'archived': False,
                    },
                    {
                        'id': 3,
                        'name': 'test audience 3',
                        'archived': True,
                    },
                    {
                        'id': 4,
                        'name': 'test audience 4',
                        'archived': False,
                    },
                    {
                        'id': 6,
                        'name': 'test audience 6',
                        'archived': False,
                    },
                ],
                'settings': {
                    'cpc_cc': '',
                    'max_cpm': '',
                    'daily_budget_cc': '100.00',
                    'end_date': '2015-04-02',
                    'id': '1',
                    'campaign_id': '1',
                    'name': 'test adgroup 1 Čžš',
                    'start_date': '2015-03-02',
                    'state': 2,
                    'target_devices': ['DESKTOP', 'MOBILE'],
                    'target_os': [],
                    'target_browsers': [],
                    'target_placements': [],
                    'target_regions': self._target_regions_repr(countries=['GB', 'US', 'CA']),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'autopilot_on_campaign': False,
                    'autopilot_state': constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
                    'autopilot_daily_budget': '50.00',
                    'retargeting_ad_groups': [3],
                    'exclusion_retargeting_ad_groups': [4],
                    'audience_targeting': [1, 2],
                    'exclusion_audience_targeting': [3, 4],
                    'tracking_code': 'param1=foo&param2=bar',
                    'autopilot_min_budget': '10',
                    'autopilot_optimization_goal': None,
                    'notes': 'Some note',
                    'bluekai_targeting': {'OR': [{'category': '3'}, {'category': '4'}]},
                    'bluekai_targeting_old': ['or', '3', '4'],
                    'interest_targeting': ['fun', 'games'],
                    'exclusion_interest_targeting': ['religion', 'weather'],
                    'redirect_pixel_urls': ["http://a.com/b.jpg", "http://a.com/c.jpg"],
                    'redirect_javascript': "alert('a')",
                    'dayparting': {"monday": [0, 1, 2, 3], "tuesday": [10, 11, 23], "timezone": "America/New_York"},
                    'b1_sources_group_enabled': True,
                    'b1_sources_group_daily_budget': '500.0000',
                    'b1_sources_group_state': 1,
                    'b1_sources_group_cpc_cc': '0.0100',
                    'whitelist_publisher_groups': [],
                    'blacklist_publisher_groups': [],
                    'landing_mode': False,
                    'delivery_type': 1,
                    'click_capping_daily_ad_group_max_clicks': 10,
                    'click_capping_daily_click_budget': '5.0000',
                },
                'warnings': {}
            },
            'success': True
        })

    @patch.object(core.multicurrency, 'get_exchange_rate')
    def test_get_local(self, mock_get_exchange_rate):
        add_permissions(self.user, ['settings_view', 'can_manage_settings_in_local_currency'])
        mock_get_exchange_rate.return_value = Decimal('2.0')

        account = magic_mixer.blend(models.Account, users=[self.user], currency=constants.Currency.EUR)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update(None, cpc_cc=Decimal(5))

        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )
        json_blob = json.loads(response.content)
        settings = json_blob.get('data').get('settings')
        self.assertEqual(settings.get('cpc_cc'), '10.000')

    def test_get_not_retargetable(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=5)
        source.supports_retargeting = False
        source.save()

        req = RequestFactory().get('/')
        req.user = User(id=1)

        ags = models.AdGroupSource.objects.get(ad_group=ad_group, source=source)
        ags.settings.update_unsafe(None, state=constants.AdGroupSourceSettingsState.ACTIVE)

        add_permissions(self.user, ['settings_view'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )

        self.assertDictEqual(
            json.loads(response.content)['data']['warnings']['retargeting'], {
                'sources': [
                    'Yahoo',
                ],
            }
        )

    def test_get_max_cpm_unsupported(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=5)

        req = RequestFactory().get('/')
        req.user = User(id=1)

        ags = models.AdGroupSource.objects.get(ad_group=ad_group, source=source)
        ags.settings.update_unsafe(None, state=constants.AdGroupSourceSettingsState.ACTIVE)

        add_permissions(self.user, ['settings_view'])
        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )
        self.assertDictEqual(
            json.loads(response.content)['data']['warnings']['max_cpm'], {
                'sources': [
                    'Yahoo',
                ],
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

    @patch('core.entity.settings.AdGroupSettings._validate_all_rtb_campaign_stop')
    @patch('utils.redirector_helper.insert_adgroup')
    @patch('utils.k1_helper.update_ad_group')
    def test_put(self, mock_k1_ping, mock_redirector_insert_adgroup, mock_validate_all_rtb_campaign_stop):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            add_permissions(self.user, [
                'settings_view',
                'can_set_ad_group_max_cpm',
                'can_set_delivery_type',
                'can_set_rtb_sources_as_one_cpc',
                'can_set_white_blacklist_publisher_groups',
                'can_set_advanced_device_targeting',
                'can_set_click_capping',
            ])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )
            mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')

            self.assertEqual(json.loads(response.content), {
                'data': {
                    'archived': False,
                    'action_is_waiting': False,
                    'default_settings': {
                        'target_devices': ['MOBILE'],
                        'target_os': [],
                        'target_placements': [],
                        'target_regions': self._target_regions_repr(dma=['501'], countries=['NC']),
                        'exclusion_target_regions': self._target_regions_repr(),
                    },
                    'settings': {
                        'cpc_cc': '0.300',
                        'max_cpm': '1.600',
                        'daily_budget_cc': '200.00',
                        'end_date': str(datetime.date.today()),
                        'id': '1',
                        'campaign_id': '1',
                        'name': 'Test ad group name',
                        'start_date': '2015-05-01',
                        'state': 2,
                        'target_devices': ['DESKTOP'],
                        'target_os': [],
                        'target_browsers': [{'name': 'CHROME'}],
                        'target_placements': [],
                        'target_regions': self._target_regions_repr(dma=['693'], countries=['GB']),
                        'exclusion_target_regions': self._target_regions_repr(),
                        'autopilot_daily_budget': '150.00',
                        'retargeting_ad_groups': [2],
                        'exclusion_retargeting_ad_groups': [9],
                        'audience_targeting': [1],
                        'exclusion_audience_targeting': [4],
                        'bluekai_targeting': {
                            'AND': [{'category': 'bluekai:123'},
                                    {'OR': [{'category': 'lotame:123'},
                                            {'category': 'outbrain:321'}]}]},
                        'bluekai_targeting_old': ['and', 'bluekai:123', ['or', 'lotame:123', 'outbrain:321']],
                        'tracking_code': 'def=123',
                        'autopilot_state': constants.AdGroupSettingsAutopilotState.INACTIVE,
                        'autopilot_min_budget': '10',
                        'autopilot_optimization_goal': None,
                        'autopilot_on_campaign': False,
                        'notes': 'Some note',
                        'interest_targeting': ['fun', 'games'],
                        'exclusion_interest_targeting': ['religion', 'weather'],
                        'redirect_pixel_urls': ["http://a.com/b.jpg", "http://a.com/c.jpg"],
                        'redirect_javascript': "alert('a')",
                        'dayparting': {"monday": [0, 1, 2, 3], "tuesday": [10, 11, 12]},
                        'b1_sources_group_enabled': True,
                        'b1_sources_group_daily_budget': '500.0000',
                        'b1_sources_group_state': 1,
                        'b1_sources_group_cpc_cc': '0.25',
                        'whitelist_publisher_groups': [1],
                        'blacklist_publisher_groups': [1],
                        'landing_mode': False,
                        'delivery_type': 2,
                        'click_capping_daily_ad_group_max_clicks': 15,
                        'click_capping_daily_click_budget': '7.5000',
                    }
                },
                'success': True
            })

            ad_group.settings.refresh_from_db()
            new_settings = ad_group.get_current_settings()

            self.assertEqual(new_settings.display_url, 'example.com')
            self.assertEqual(new_settings.brand_name, 'Example')
            self.assertEqual(new_settings.description, 'Example description')
            self.assertEqual(new_settings.call_to_action, 'Call to action')
            self.assertEqual(new_settings.delivery_type, 2)

            mock_redirector_insert_adgroup.assert_called_with(ad_group)

            hist = history_helpers.get_ad_group_history(ad_group).first()
            self.assertEqual(constants.HistoryActionType.SETTINGS_CHANGE, hist.action_type)

    @patch.object(core.multicurrency, 'get_exchange_rate')
    @patch.object(models.AdGroupSettings, 'update')
    def test_put_local(self, mock_ad_group_settings_update, mock_get_exchange_rate):
        add_permissions(self.user, ['settings_view', 'can_manage_settings_in_local_currency'])
        mock_get_exchange_rate.return_value = Decimal('2.0')

        account = magic_mixer.blend(models.Account, users=[self.user], currency=constants.Currency.EUR)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)

        self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({
                'settings': {
                    'cpc_cc': '0.5000',
                    'name': 'test local put',
                    'state': constants.AdGroupRunningStatus.INACTIVE,
                    'start_date': '2015-05-01',
                    'target_devices': ['DESKTOP'],
                    'target_regions': self._target_regions_repr(),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'bluekai_targeting': {},
                    'delivery_type': 2,
                }
            }),
            follow=True
        )

        args, kwargs = mock_ad_group_settings_update.call_args
        self.assertIsNone(kwargs.get('cpc_cc'))
        self.assertEqual(kwargs.get('local_cpc_cc'), Decimal('0.5'))

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('utils.k1_helper.update_ad_group')
    def test_put_low_cpc(self, mock_k1_ping, mock_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            add_permissions(self.user, [
                'settings_view',
            ])
            new_settings = {}
            new_settings.update(self.settings_dict)
            new_settings['settings']['cpc_cc'] = '0.05'

            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(new_settings),
                follow=True
            )
            mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')

            resp_json = json.loads(response.content)
            self.assertEqual(resp_json['data']['settings']['cpc_cc'], '0.050')

            for ags in ad_group.adgroupsource_set.all():
                cpc = ags.get_current_settings().cpc_cc
                # All cpc are adjusted to be lower or equal to 0.05
                if ags.source.source_type.type == constants.SourceType.B1:
                    self.assertTrue(cpc <= Decimal('0.05'))

            mock_insert_adgroup.assert_called_with(ad_group)

    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_without_non_propagated_settings(self, mock_redirector_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=987)
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

            mock_redirector_insert_adgroup.assert_called_with(ad_group)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('automation.autopilot.recalculate_budgets_ad_group')
    @patch('automation.campaign_stop.get_max_settable_autopilot_budget', autospec=True)
    def test_put_set_budget_autopilot_triggers_budget_reallocation(
            self, mock_get_max_budget, mock_redirector_insert_adgroup, mock_init_autopilot):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)
            mock_get_max_budget.return_value = 1000

            ad_group = models.AdGroup.objects.get(pk=987)
            old_settings = ad_group.get_current_settings()
            new_settings = old_settings.copy_settings()
            new_settings.autopilot_state = 2
            new_settings.save(None)

            self.assertIsNotNone(old_settings.pk)
            # in order to not change it
            self.settings_dict['settings']['b1_sources_group_cpc_cc'] = str(new_settings.b1_sources_group_cpc_cc)
            self.settings_dict['settings']['b1_sources_group_daily_budget'] = str(new_settings.b1_sources_group_daily_budget)

            self.settings_dict['settings']['autopilot_state'] = 1
            self.settings_dict['settings']['autopilot_daily_budget'] = '200.00'

            add_permissions(self.user, ['settings_view', 'can_set_adgroup_to_auto_pilot'])
            self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            ad_group.settings.refresh_from_db()
            new_settings = ad_group.get_current_settings().copy_settings()

            request = HttpRequest()
            request.user = User(id=1)

            # can it actually be saved to the db
            new_settings.save(request)

            self.assertEqual(new_settings.autopilot_state, 1)
            self.assertEqual(new_settings.autopilot_daily_budget, Decimal('200'))

            self.assertEqual(mock_init_autopilot.called, True)

    @patch('utils.k1_helper.update_ad_group')
    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_firsttime_create_settings(self, mock_redirector_insert_adgroup, mock_k1_ping):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=10)

            self.settings_dict['settings']['id'] = 10

            add_permissions(self.user, [
                'settings_view',
            ])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )
            self.assertTrue(json.loads(response.content).get('success'))
            new_settings = ad_group.get_current_settings()
            self.assertIsNotNone(new_settings.pk)

            mock_redirector_insert_adgroup.assert_called_with(ad_group)

            hist = history_helpers.get_ad_group_history(ad_group).first()
            self.assertEqual(constants.HistoryActionType.SETTINGS_CHANGE, hist.action_type)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('utils.k1_helper.update_ad_group')
    def test_rtb_sources_cpc_change_changes_all_rtb_cpcs(self, mock_k1_ping, mock_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            add_permissions(self.user, [
                'settings_view',
                'can_set_rtb_sources_as_one_cpc',
            ])
            new_settings = {}
            new_settings.update(self.settings_dict)
            new_settings['settings']['b1_sources_group_cpc_cc'] = '0.1'

            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(new_settings),
                follow=True
            )
            mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')

            resp_json = json.loads(response.content)
            self.assertEqual(resp_json['data']['settings']['b1_sources_group_cpc_cc'], '0.1')

            for ags in ad_group.adgroupsource_set.all():
                cpc = ags.get_current_settings().cpc_cc
                # All b1 sources cpcs are adjusted to 0.05
                if ags.source.source_type.type == constants.SourceType.B1:
                    self.assertTrue(cpc == Decimal('0.1'))

            mock_insert_adgroup.assert_called_with(ad_group)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('utils.k1_helper.update_ad_group')
    def test_full_autopilot_to_cpc_autopilot_transition(self, mock_k1_ping, mock_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            old_settings = ad_group.get_current_settings()
            self.assertIsNotNone(old_settings.pk)

            old_settings = old_settings.copy_settings()
            old_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            old_settings.b1_sources_group_enabled = True
            old_settings.b1_sources_group_cpc_cc = Decimal('0.25')
            old_settings.save(None)

            for ad_group_source in ad_group.adgroupsource_set.filter(
                    source__source_type__type=constants.SourceType.B1):
                ad_group_source_settings = ad_group_source.get_current_settings().copy_settings()
                ad_group_source_settings.state = constants.AdGroupSettingsState.INACTIVE
                ad_group_source_settings.save(None)

            ad_group_source_1 = ad_group.adgroupsource_set.get(id=18)
            ad_group_source_1_settings = ad_group_source_1.get_current_settings().copy_settings()
            ad_group_source_1_settings.cpc_cc = Decimal('0.3')
            ad_group_source_1_settings.state = constants.AdGroupSettingsState.ACTIVE
            ad_group_source_1_settings.save(None)

            ad_group_source_2 = ad_group.adgroupsource_set.get(id=1)
            ad_group_source_2_settings = ad_group_source_2.get_current_settings().copy_settings()
            ad_group_source_2_settings.cpc_cc = Decimal('0.13')
            ad_group_source_2_settings.state = constants.AdGroupSettingsState.ACTIVE
            ad_group_source_2_settings.save(None)

            ad_group_source_3 = ad_group.adgroupsource_set.get(id=25)
            ad_group_source_3_settings = ad_group_source_3.get_current_settings().copy_settings()
            ad_group_source_3_settings.cpc_cc = Decimal('0.001')
            ad_group_source_3_settings.save(None)

            add_permissions(self.user, [
                'settings_view',
                'can_set_adgroup_to_auto_pilot',
                'can_set_rtb_sources_as_one_cpc',
            ])
            new_settings = {}
            new_settings.update(self.settings_dict)
            new_settings['settings']['autopilot_state'] = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
            new_settings['settings']['b1_sources_group_enabled'] = True

            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(new_settings),
                follow=True
            )
            mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')
            self.maxDiff = None

            resp_json = json.loads(response.content)
            self.assertEqual(resp_json['data']['settings']['autopilot_state'], constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)
            self.assertEqual(resp_json['data']['settings']['b1_sources_group_cpc_cc'], '0.2150')

            for ags in ad_group.adgroupsource_set.all():
                agss = ags.get_current_settings()
                if ags.source.source_type.type == constants.SourceType.B1:
                    self.assertEqual(Decimal('0.2150'), agss.cpc_cc)

            mock_insert_adgroup.assert_called_with(ad_group)

    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_tracking_codes_with_permission(self, mock_redirector_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            self.settings_dict['settings']['tracking_code'] = 'asd=123'

            add_permissions(self.user, ['settings_view'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_settings_dict = json.loads(response.content)['data']['settings']

            self.assertEqual(response_settings_dict['tracking_code'], 'asd=123')

    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_invalid_target_region(self, mock_redirector_insert_adgroup):
        ad_group = models.AdGroup.objects.get(pk=1)

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

    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_us_and_dmas(self, mock_redirector_insert_adgroup):
        ad_group = models.AdGroup.objects.get(pk=1)

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

    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_invalid_publisher_groups(self, _):
        ad_group = models.AdGroup.objects.get(pk=1)

        self.settings_dict['settings']['whitelist_publisher_groups'] = ['2']
        self.settings_dict['settings']['blacklist_publisher_groups'] = ['2']

        add_permissions(self.user, ['settings_view'])
        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertIn('whitelist_publisher_groups', response_dict['data']['errors'])
        self.assertIn('blacklist_publisher_groups', response_dict['data']['errors'])

    @patch('utils.redirector_helper.insert_adgroup')
    def test_end_date_in_the_past(self, mock_redirector_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)
            new_settings = ad_group.get_current_settings().copy_settings()
            new_settings.state = constants.AdGroupSettingsState.ACTIVE
            new_settings.save(None)

            self.settings_dict['settings']['state'] = constants.AdGroupSettingsState.ACTIVE
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

    @patch('utils.redirector_helper.insert_adgroup')
    def test_put_set_settings_no_permissions(self, mock_redirector_insert_adgroup):
        with patch('utils.dates_helper.local_today') as mock_now:
            # mock datetime so that budget is always valid
            mock_now.return_value = datetime.date(2016, 1, 5)

            ad_group = models.AdGroup.objects.get(pk=1)

            add_permissions(self.user, ['settings_view'])
            response = self.client.put(
                reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
                json.dumps(self.settings_dict),
                follow=True
            )

            response_settings_dict = json.loads(response.content)['data']['settings']

            self.assertNotEqual(response_settings_dict['max_cpm'], '1.600')


class AdGroupSettingsRetargetableAdgroupsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_non_superuser.yaml', 'test_geolocations']

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
    fixtures = ['test_models.yaml', 'test_adgroup_settings_state.yaml', 'test_non_superuser.yaml', 'test_geolocations']

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

    @patch('automation.campaign_stop.can_enable_all_ad_groups')
    @patch('dash.dashapi.data_helper.campaign_has_available_budget')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate(self, mock_k1_ping, mock_budget_check, mock_campaign_stop):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_budget_check.return_value = True
        mock_campaign_stop.return_value = True

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create_unsafe(campaign_id=ad_group.campaign_id)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.ACTIVE)
        mock_k1_ping.assert_called_with(2, msg='AdGroupSettings.put')

    @patch('automation.campaign_stop.can_enable_all_ad_groups')
    @patch('dash.dashapi.data_helper.campaign_has_available_budget')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate_already_activated(self, mock_k1_ping, mock_budget_check, mock_campaign_stop):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_budget_check.return_value = True
        mock_campaign_stop.return_value = True

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create_unsafe(campaign_id=ad_group.campaign_id)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 1}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(mock_k1_ping.called)

    @patch('utils.k1_helper.update_ad_group')
    def test_activate_without_budget(self, mock_k1_ping):
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
        self.assertFalse(mock_k1_ping.called)

    @patch('dash.dashapi.data_helper.campaign_has_available_budget')
    @patch('utils.k1_helper.update_ad_group')
    def test_activate_no_goals(self, mock_k1_ping, mock_budget_check):
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

    def test_campaign_in_landing_mode(self):
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

    @patch('utils.k1_helper.update_ad_group')
    def test_inactivate(self, mock_k1_ping):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 2}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        mock_k1_ping.assert_called_with(1, msg='AdGroupSettings.put')

    @patch('automation.campaign_stop.can_enable_all_ad_groups')
    def test_inactivate_already_inactivated(self, mock_campaign_stop):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_campaign_stop.return_value = True

        add_permissions(self.user, ['can_control_ad_group_state_in_table'])
        response = self.client.post(
            reverse('ad_group_settings_state', kwargs={'ad_group_id': ad_group.id}),
            json.dumps({'state': 2}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(response.status_code, 200)


class ConversionPixelTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml', 'test_non_superuser.yaml', 'test_conversion_pixel.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

    def test_get(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': account.id}),
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertCountEqual([{
            'id': 1,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'archived': False,
            'audience_enabled': True,
            'additional_pixel': False,
        }, {
            'id': 2,
            'name': 'test2',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test2/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': False,
        }], decoded_response['data']['rows'])

    def test_get_additional(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        p = models.ConversionPixel.objects.get(pk=2)
        p.additional_pixel = True
        p.save()

        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': account.id}),
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertCountEqual([{
            'id': 1,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'archived': False,
            'audience_enabled': True,
            'additional_pixel': False,
        }, {
            'id': 2,
            'name': 'test2',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test2/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': True,
        }], decoded_response['data']['rows'])

    def test_get_non_existing_account(self):
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': 9876}),
            follow=True
        )

        self.assertEqual(404, response.status_code)

    def test_get_redirect_url(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        permission = authmodels.Permission.objects.get(codename='can_redirect_pixels')
        self.user.user_permissions.add(permission)

        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': account.id}),
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertCountEqual([{
            'id': 1,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'archived': False,
            'audience_enabled': True,
            'additional_pixel': False,
            'redirect_url': None,
        }, {
            'id': 2,
            'name': 'test2',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test2/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': False,
            'redirect_url': None,
        }], decoded_response['data']['rows'])

    def test_get_notes(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        pixel = models.ConversionPixel.objects.get(pk=1)
        pixel.notes = 'test note'
        pixel.save()

        permission = authmodels.Permission.objects.get(codename='can_see_pixel_notes')
        self.user.user_permissions.add(permission)

        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': account.id}),
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertCountEqual([{
            'id': 1,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'archived': False,
            'audience_enabled': True,
            'additional_pixel': False,
            'notes': 'test note',
        }, {
            'id': 2,
            'name': 'test2',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test2/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': False,
            'notes': '',
        }], decoded_response['data']['rows'])

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_post(self, ping_mock, redirector_mock):
        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'name'}),
            content_type='application/json',
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertDictEqual({
            'id': 3,
            'name': 'name',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/3/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': False,
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_CREATE,
            hist.action_type)
        self.assertEqual('Added conversion pixel named name.',
                         hist.changes_text)
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_post_audience_enabled(self, ping_mock, redirector_mock):
        audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        audience_enabled_pixels[0].audience_enabled = False
        audience_enabled_pixels[0].save()

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'name', 'audience_enabled': True}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        self.assertEqual(audience_enabled_pixels[0].name, 'name')

        self.assertDictEqual({
            'data': {
                'id': audience_enabled_pixels[0].id,
                'name': 'name',
                'archived': False,
                'audience_enabled': True,
                'additional_pixel': False,
                'url': 'https://p1.zemanta.com/p/1/{}/'.format(audience_enabled_pixels[0].slug)
            },
            'success': True
        }, json.loads(response.content))

        ping_mock.assert_called_with(1, msg='conversion_pixel.create')
        self.assertFalse(redirector_mock.called)

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_post_audience_enabled_invalid(self, ping_mock, redirector_mock):
        audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'name', 'audience_enabled': True}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertDictEqual({
            'data': {
                'error_code': 'ValidationError',
                'message': None,
                'errors': {
                    'audience_enabled': 'This pixel cannot be used for building custom audiences because another pixel is already used: test.'
                },
                'data': None
            },
            'success': False
        }, json.loads(response.content))

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

        audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))

    @patch('utils.redirector_helper.update_pixel')
    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_post_redirect_url(self, ping_mock, redirector_mock, update_pixel_mock):
        permission = authmodels.Permission.objects.get(codename='can_redirect_pixels')
        self.user.user_permissions.add(permission)

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'name', 'redirect_url': 'http://test.com'}),
            content_type='application/json',
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertDictEqual({
            'id': 7,
            'name': 'name',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/7/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': False,
            'redirect_url': 'http://test.com'
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_CREATE,
            hist.action_type)
        self.assertEqual('Added conversion pixel named name.',
                         hist.changes_text)
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

        self.assertTrue(update_pixel_mock.called)

    def test_post_redirect_url_inavlid(self):
        permission = authmodels.Permission.objects.get(codename='can_redirect_pixels')
        self.user.user_permissions.add(permission)

        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'name', 'redirect_url': 'invalidurl'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    def test_post_name_empty(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': ''}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    def test_post_name_too_long(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'a' * (models.ConversionPixel._meta.get_field('name').max_length + 1)}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    @patch('utils.redirector_helper.update_pixel')
    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_post_notes(self, ping_mock, redirector_mock, update_pixel_mock):
        permission = authmodels.Permission.objects.get(codename='can_see_pixel_notes')
        self.user.user_permissions.add(permission)

        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'name': 'name', 'notes': 'test notes'}),
            content_type='application/json',
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertDictEqual({
            'id': 6,
            'name': 'name',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/6/',
            'archived': False,
            'audience_enabled': False,
            'additional_pixel': False,
            'notes': 'test notes'
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_CREATE,
            hist.action_type)
        self.assertEqual('Added conversion pixel named name.',
                         hist.changes_text)
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)
        self.assertFalse(update_pixel_mock.called)

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_put_audience_enabled(self, ping_mock, redirector_mock):
        existing_audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(existing_audience_enabled_pixels))
        existing_audience_enabled_pixels[0].audience_enabled = False
        existing_audience_enabled_pixels[0].save()

        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': existing_audience_enabled_pixels[0].id}),
            json.dumps({'name': 'name', 'audience_enabled': True}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        self.assertEqual(audience_enabled_pixels[0].id, existing_audience_enabled_pixels[0].id)

        self.assertDictEqual({
            'data': {
                'id': audience_enabled_pixels[0].id,
                'name': 'name',
                'archived': False,
                'audience_enabled': True,
                'additional_pixel': False,
                'url': 'https://p1.zemanta.com/p/1/{}/'.format(audience_enabled_pixels[0].slug)
            },
            'success': True
        }, json.loads(response.content))

        ping_mock.assert_called_with(1, msg='conversion_pixel.update')
        self.assertEqual(redirector_mock.call_count, 4)

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.k1_helper.update_account')
    def test_put_audience_enabled_invalid(self, ping_mock, redirector_mock):
        existing_audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(existing_audience_enabled_pixels))

        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 2}),
            json.dumps({'name': 'name', 'audience_enabled': True}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertDictEqual({
            'data': {
                'error_code': 'ValidationError',
                'message': None,
                'errors': {
                    'audience_enabled': 'This pixel cannot be used for building custom audiences because another pixel is already used: test.'
                },
                'data': None
            },
            'success': False
        }, json.loads(response.content))

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

        audience_enabled_pixels = models.ConversionPixel.objects.\
            filter(audience_enabled=True).\
            filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        self.assertEqual(1, existing_audience_enabled_pixels[0].id)

    @patch('utils.redirector_helper.upsert_audience')
    def test_put_archive(self, redirector_mock):
        add_permissions(self.user, ['archive_restore_entity'])

        conversion_pixel = models.ConversionPixel.objects.get(pk=2)
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 2}),
            json.dumps({'archived': True, 'name': conversion_pixel.name, 'audience_enabled': False}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertDictEqual({
            'id': 2,
            'archived': True,
            'name': 'test2',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test2/',
            'audience_enabled': False,
            'additional_pixel': False,
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_ARCHIVE_RESTORE,
            hist.action_type)
        self.assertEqual('Archived conversion pixel named test2.', hist.changes_text)

        self.assertFalse(redirector_mock.called)

    @patch('utils.redirector_helper.upsert_audience')
    def test_put_archive_audience_enabled(self, redirector_mock):
        add_permissions(self.user, ['archive_restore_entity'])

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True, 'name': conversion_pixel.name, 'audience_enabled': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        self.assertFalse(conversion_pixel.archived)

        self.assertDictEqual({
            'data': {
                'error_code': 'ValidationError',
                'message': None,
                'errors': {
                    'audience_enabled': 'Cannot archive pixel used for building custom audiences.'},
                'data': None
            },
            'success': False
        }, json.loads(response.content))

        self.assertFalse(redirector_mock.called)

    @patch('utils.redirector_helper.upsert_audience')
    def test_put_name(self, redirector_mock):
        add_permissions(self.user, ['archive_restore_entity'])
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': 'New name', 'audience_enabled': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({
            'id': 1,
            'archived': conversion_pixel.archived,
            'name': 'New name',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'audience_enabled': True,
            'additional_pixel': False,
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_RENAME,
            hist.action_type)
        self.assertEqual('Renamed conversion pixel named test to New name.', hist.changes_text)

        self.assertEqual(redirector_mock.call_count, 4)

    @patch('utils.redirector_helper.upsert_audience')
    def test_put_archive_no_permissions(self, redirector_mock):
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        self.assertFalse(conversion_pixel.archived)

        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True, 'name': conversion_pixel.name}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertDictEqual({
            'id': 1,
            'archived': False,
            'name': conversion_pixel.name,
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'audience_enabled': False,
            'additional_pixel': False,
        }, decoded_response['data'])

        self.assertFalse(redirector_mock.called)

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
        new_conversion_pixel = models.ConversionPixel.objects.create(account_id=4, name='abcd')

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

    def test_empty_name(self):
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': ''}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual(['Please specify a name.'], decoded_response['data']['errors']['name'])

    def test_name_too_long(self):
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': 'aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeefffff'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual(['Name is too long (55/50).'], decoded_response['data']['errors']['name'])

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.redirector_helper.update_pixel')
    def test_put_redirect_url(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ['can_redirect_pixels'])
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': 'test', 'audience_enabled': False, 'redirect_url': 'http://test.com'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({
            'id': 1,
            'archived': conversion_pixel.archived,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'audience_enabled': False,
            'additional_pixel': False,
            'redirect_url': 'http://test.com',
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_SET_REDIRECT_URL,
            hist.action_type)
        self.assertEqual('Set redirect url of pixel named test to http://test.com.', hist.changes_text)

        self.assertEqual(upsert_audience_mock.call_count, 0)
        update_pixel_mock.assert_called_once_with(conversion_pixel)

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.redirector_helper.update_pixel')
    def test_put_redirect_url_remove(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ['can_redirect_pixels'])

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.redirect_url = 'http://test.com'
        conversion_pixel.save()

        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': 'test', 'audience_enabled': False, 'redirect_url': ''}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({
            'id': 1,
            'archived': conversion_pixel.archived,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'audience_enabled': False,
            'additional_pixel': False,
            'redirect_url': '',
        }, decoded_response['data'])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(
            constants.HistoryActionType.CONVERSION_PIXEL_SET_REDIRECT_URL,
            hist.action_type)
        self.assertEqual('Removed redirect url of pixel named test.', hist.changes_text)

        self.assertEqual(upsert_audience_mock.call_count, 0)
        update_pixel_mock.assert_called_once_with(conversion_pixel)

    def test_put_redirect_url_invalid(self):
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': 'test', 'audience_enabled': False, 'redirect_url': 'invalidurl'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual(['Enter a valid URL.'], decoded_response['data']['errors']['redirect_url'])

    @patch('utils.redirector_helper.upsert_audience')
    @patch('utils.redirector_helper.update_pixel')
    def test_put_notes(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ['can_see_pixel_notes'])
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'name': 'test', 'audience_enabled': False, 'notes': 'test notes'}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({
            'id': 1,
            'archived': conversion_pixel.archived,
            'name': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'audience_enabled': False,
            'additional_pixel': False,
            'notes': 'test notes',
        }, decoded_response['data'])

        self.assertEqual(upsert_audience_mock.call_count, 0)
        self.assertEqual(update_pixel_mock.call_count, 0)


class UserActivationTest(TestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_permissions(self):
        url = reverse('account_user_action', kwargs={'account_id': 0, 'user_id': 0, 'action': 'activate'})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_send_mail(self):
        request = HttpRequest()
        request.user = User(id=1)

        data = {}

        add_permissions(self.user, ['account_agency_access_permissions'])
        response = self.client.post(
            reverse('account_user_action', kwargs={'account_id': 1, 'user_id': 1, 'action': 'activate'}),
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
            reverse('account_user_action', kwargs={'account_id': 1, 'user_id': 1, 'action': 'activate'}),
            data,
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertFalse(decoded_response.get('success'), 'Failed sending message')


class CampaignSettingsTest(TestCase):
    fixtures = ['test_views.yaml', 'test_non_superuser.yaml', 'test_agency.yaml', 'test_geolocations']

    @classmethod
    def _target_regions_repr(cls, countries=[], regions=[], cities=[], dma=[], postal_codes=[]):
        return dict(countries=countries, regions=regions, cities=cities, dma=dma, postal_codes=postal_codes)

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
        self.assertEqual(content['data']['settings']['target_devices'], ['MOBILE'])
        self.assertEqual(content['data']['settings']['target_regions'], self._target_regions_repr(dma=['501'], countries=['NC']))
        self.assertEqual(content['data']['settings']['exclusion_target_regions'], self._target_regions_repr())
        self.assertEqual(content['data']['settings']['enable_ga_tracking'], True)
        self.assertEqual(content['data']['settings']['enable_adobe_tracking'], False)
        self.assertEqual(content['data']['settings']['ga_tracking_type'], 1)
        self.assertEqual(content['data']['settings']['ga_property_id'], '')
        self.assertEqual(content['data']['settings']['adobe_tracking_param'], '')
        self.assertEqual(content['data']['settings']['whitelist_publisher_groups'], [1])
        self.assertEqual(content['data']['settings']['blacklist_publisher_groups'], [1])
        self.assertEqual(content['data']['settings']['autopilot'], False)

    @patch('automation.autopilot.recalculate_budgets_campaign')
    @patch('dash.views.agency.ga.is_readable')
    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.agency.email_helper.send_ga_setup_instructions')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    @patch('utils.k1_helper.update_ad_group')
    def test_put(self, mock_k1_ping, mock_send_campaign_notification_email, mock_send_ga_email, mock_r1_insert_adgroup, mock_ga_readable, mock_autopilot):
        mock_ga_readable.return_value = False

        add_permissions(self.user, [
            'can_modify_campaign_manager',
            'can_modify_campaign_iab_category',
            'can_set_ga_api_tracking',
            'can_set_white_blacklist_publisher_groups',
        ])
        campaign = models.Campaign.objects.get(pk=1)

        settings = campaign.get_current_settings()
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertNotEqual(settings.campaign_goal, 2)
        self.assertNotEqual(settings.target_devices, ['desktop'])
        self.assertNotEqual(settings.target_regions, self._target_regions_repr(dma=['502'], countries=['CA']))
        self.assertNotEqual(settings.exclusion_target_regions, self._target_regions_repr(dma=['502'], countries=['CA']))
        self.assertNotEqual(settings.ga_tracking_type, 2)
        self.assertNotEqual(settings.ga_property_id, 'UA-123456789-3')
        self.assertNotEqual(settings.enable_adobe_tracking, True)
        self.assertNotEqual(settings.adobe_tracking_param, 'cid')

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create_unsafe(campaign_id=campaign.id)

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'language': constants.Language.ENGLISH,
                    'target_devices': ['DESKTOP'],
                    'target_regions': self._target_regions_repr(dma=['502'], countries=['CA']),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'campaign_manager': 1,
                    'iab_category': 'IAB17',
                    'enable_ga_tracking': True,
                    'enable_adobe_tracking': True,
                    'ga_tracking_type': 2,
                    'ga_property_id': 'UA-123456789-3',
                    'adobe_tracking_param': 'cid',
                    'whitelist_publisher_groups': [1, 3],
                    'blacklist_publisher_groups': [1, 3],
                    'autopilot': True,
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])

        self.assertEqual(mock_k1_ping.call_count, 1)

        settings = campaign.get_current_settings()
        settings.refresh_from_db()

        # Check if all fields were updated
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertEqual(settings.campaign_goal, 2)
        self.assertEqual(settings.target_devices, ['desktop'])
        self.assertEqual(settings.target_regions, ['CA', '502'])
        self.assertEqual(settings.exclusion_target_regions, [])
        self.assertEqual(settings.campaign_manager_id, 1)
        self.assertEqual(settings.iab_category, 'IAB17')
        self.assertEqual(settings.enable_ga_tracking, True)
        self.assertEqual(settings.ga_tracking_type, 2)
        self.assertEqual(settings.ga_property_id, 'UA-123456789-3')
        self.assertEqual(settings.enable_adobe_tracking, True)
        self.assertEqual(settings.adobe_tracking_param, 'cid')
        self.assertEqual(settings.whitelist_publisher_groups, [1, 3])
        self.assertEqual(settings.blacklist_publisher_groups, [1, 3])
        self.assertEqual(settings.autopilot, True)

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request, ANY)
        mock_send_ga_email.assert_called_with(self.user)
        mock_ga_readable.assert_called_with('UA-123456789-3')
        mock_r1_insert_adgroup.assert_has_calls(
            [call(ag) for ag in campaign.adgroup_set.all()])

        hist = history_helpers.get_campaign_history(models.Campaign.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.SETTINGS_CHANGE, hist.action_type)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals_added(self, p1, p3):
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
                    'language': constants.Language.ENGLISH,
                    'target_devices': ['DESKTOP'],
                    'target_regions': self._target_regions_repr(dma=['502'], countries=['CA']),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'enable_ga_tracking': False,
                    'enable_adobe_tracking': False,
                    'ga_tracking_type': 2,
                    'ga_property_id': 'UA-123456789-1',
                    'adobe_tracking_param': 'cid',
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
                    'language': constants.Language.ENGLISH,
                    'target_devices': ['DESKTOP'],
                    'target_regions': self._target_regions_repr(dma=['502'], countries=['CA']),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'enable_ga_tracking': False,
                    'enable_adobe_tracking': False,
                    'ga_tracking_type': 2,
                    'ga_property_id': 'UA-123456789-1',
                    'adobe_tracking_param': 'cid',
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
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals_modified(self, p1, p3):
        goal = models.CampaignGoal.objects.create_unsafe(
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
                    'language': constants.Language.ENGLISH,
                    'campaign_goal': 2,
                    'target_devices': ['DESKTOP'],
                    'target_regions': self._target_regions_repr(dma=['502'], countries=['CA']),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'enable_ga_tracking': False,
                    'enable_adobe_tracking': False,
                    'ga_tracking_type': 2,
                    'ga_property_id': 'UA-123456789-1',
                    'adobe_tracking_param': 'cid',
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
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_goals_removed(self, p1, p3):

        campaign_id = 1

        # ensure this campaign has more than 1 goal
        models.CampaignGoal.objects.create_unsafe(campaign_id=campaign_id)

        goal = models.CampaignGoal.objects.create_unsafe(
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
                    'language': constants.Language.ENGLISH,
                    'target_devices': ['DESKTOP'],
                    'target_regions': self._target_regions_repr(dma=['502'], countries=['CA']),
                    'exclusion_target_regions': self._target_regions_repr(),
                    'enable_ga_tracking': False,
                    'enable_adobe_tracking': False,
                    'ga_tracking_type': 2,
                    'ga_property_id': 'UA-123456789-1',
                    'adobe_tracking_param': 'cid',
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
                    'target_regions': self._target_regions_repr(dma=['501'], countries=['NC']),
                    'exclusion_target_regions': self._target_regions_repr()
                }
            }),
            content_type='application/json',
        )

        content = json.loads(response.content)
        self.assertFalse(content['success'])

        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 50,
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertFalse(content['success'])
        self.assertTrue('campaign_goal' in content['data']['errors'])
        self.assertTrue('target_devices' in content['data']['errors'])

    def test_get_with_conversion_goals(self):

        ad_group = models.AdGroup.objects.get(pk=987)

        add_permissions(self.user, ['can_see_campaign_goals'])

        convpix = models.ConversionPixel.objects.create(
            account=ad_group.campaign.account,
            name='janez_name',
        )
        convg = models.ConversionGoal.objects.create_unsafe(
            campaign=ad_group.campaign,
            type=constants.ConversionGoalType.PIXEL,
            name='janezjanez',
            pixel=convpix,
            conversion_window=7,
            goal_id='9',
        )

        models.CampaignGoal.objects.create_unsafe(
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
                'pixel_url': 'https://p1.zemanta.com/p/1/2/',
            },
            content['data']['goals'][0]['conversion_goal'],
        )

    def test_get_campaign_managers_no_permission(self):
        add_permissions(self.user, [])

        user = User.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        response = self.client.get(
            '/api/campaigns/1000/settings/'
        )
        content = json.loads(response.content)

        self.assertTrue(content['success'])
        self.assertIsNone(content['data'].get('campaign_managers'))

    def test_get_campaign_managers_from_agency(self):
        add_permissions(self.user, ['can_modify_campaign_manager'])

        user = User.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        response = self.client.get(
            '/api/campaigns/1000/settings/'
        )
        content = json.loads(response.content)

        self.assertTrue(content['success'])
        self.assertEqual(content['data'].get('campaign_managers'), [{
            'id': '1',
            'name': 'non_superuser@zemanta.com',
        }])

    def test_get_campaign_managers_from_account(self):
        add_permissions(self.user, ['can_modify_campaign_manager'])

        user = User.objects.get(pk=1)
        account = models.Account.objects.get(pk=1000)
        account.users.add(user)

        response = self.client.get(
            '/api/campaigns/1000/settings/'
        )
        content = json.loads(response.content)

        self.assertTrue(content['success'])
        self.assertEqual(content['data'].get('campaign_managers'), [
            {
                'id': '1',
                'name': 'non_superuser@zemanta.com',
            }
        ])

    def test_get_campaign_managers_can_see_all_users(self):
        add_permissions(self.user, ['can_modify_campaign_manager', 'can_see_all_users_for_managers'])

        user = User.objects.get(pk=1)
        account = models.Account.objects.get(pk=1000)
        account.users.add(user)

        response = self.client.get(
            '/api/campaigns/1000/settings/'
        )
        content = json.loads(response.content)

        self.assertTrue(content['success'])
        self.assertEqual(len(content['data'].get('campaign_managers')), 4)

    @patch.object(ga, 'is_readable')
    def test_ga_property_validation(self, mock_is_readable):
        ga_property_id = 'UA-123-1'
        request = HttpRequest
        request.user = User.objects.get(pk=1)
        campaign = models.Campaign.objects.get(pk=1)
        settings = campaign.get_current_settings()
        settings_view = agency.CampaignSettings()

        # not set
        settings_dict = settings_view.get_dict(request, settings, campaign)
        mock_is_readable.assert_not_called()
        self.assertNotIn('ga_property_readable', settings_dict)

        # is set
        settings.enable_ga_tracking = True
        settings.ga_property_id = ga_property_id

        # is readable
        mock_is_readable.return_value = True
        settings_dict = settings_view.get_dict(request, settings, campaign)
        mock_is_readable.called_with(ga_property_id)
        self.assertEqual(settings_dict['ga_property_readable'], True)

        # not readable
        mock_is_readable.return_value = False
        settings_dict = settings_view.get_dict(request, settings, campaign)
        mock_is_readable.called_with(ga_property_id)
        self.assertEqual(settings_dict['ga_property_readable'], False)


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
        self.account = account

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
        form = forms.AccountSettingsForm(self.account)
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
            'can_see_salesforce_url',
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
            'salesforce_url': None,
            'id': '1',
            'archived': False,
            'facebook_status': 'Empty',
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [1],
            'currency': 'USD',
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
            'archived': False,
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
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
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
        })

        add_permissions(user, ['can_set_account_cs_representative'])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'name': 'Chuck ads',
            'default_account_manager': None,
            'default_sales_representative': None,
            'default_cs_representative': None,
            'id': '1000',
            'archived': False,
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
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
            'default_cs_representative': None,
            'allowed_sources': {'2': {'name': 'Source 2', 'released': True, 'deprecated': False},
                                '100': {'name': 'AdsNative', 'released': True, 'deprecated': False},
                                '200': {'name': 'Facebook', 'released': True, 'deprecated': False}
                                },
            'id': '1000',
            'archived': False,
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
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
            'default_cs_representative': None,
            'allowed_sources': {'2': {'name': 'Source 2', 'released': True, 'deprecated': False},
                                '100': {'name': 'AdsNative', 'released': True, 'deprecated': False},
                                '200': {'name': 'Facebook', 'released': True, 'deprecated': False}
                                },
            'account_type': constants.AccountType.UNKNOWN,
            'id': '1000',
            'archived': False,
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
        })

        add_permissions(user, ['can_see_salesforce_url'])

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'name': 'Chuck ads',
            'default_account_manager': None,
            'default_sales_representative': None,
            'default_cs_representative': None,
            'allowed_sources': {'2': {'name': 'Source 2', 'released': True, 'deprecated': False},
                                '100': {'name': 'AdsNative', 'released': True, 'deprecated': False},
                                '200': {'name': 'Facebook', 'released': True, 'deprecated': False}
                                },
            'account_type': constants.AccountType.UNKNOWN,
            'salesforce_url': None,
            'id': '1000',
            'archived': False,
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
        })

    def test_get_can_set_agency(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
            'can_set_agency_for_account',
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
            'archived': False,
            'agency': 'Alfa&Omega',
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
            'currency': 'USD',
        })
        agencies = [{
            'name': 'Alfa&Omega',
            'default_account_type': 1,
            'sales_representative': None,
            'cs_representative': None,
        }]
        self.assertEqual(agencies, response['data']['agencies'])

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
            'currency': 'USD',
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
            'currency': 'USD',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 400, msg='Designated sales rep doesn''t have permission')

        add_permissions(User.objects.get(pk=3), ['campaign_settings_sales_rep'])
        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 401, 'agency manager cannot set sales rep. without permission')

        add_permissions(user, ['can_set_account_sales_representative'])
        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 200)

    def test_put_as_agency_manager_cs_rep(self):
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
            'default_cs_representative': '3',
            'currency': 'USD',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 400, msg='Designated cs rep doesn''t have permission')

        add_permissions(User.objects.get(pk=3), ['campaign_settings_cs_rep'])
        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 401, 'agency manager cannot set cs rep. without permission')

        add_permissions(user, ['can_set_account_cs_representative'])
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
            'currency': 'USD',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 401,
                         msg='Agency manager doesn''t have permission for changing allowed sources')

        add_permissions(user, ['can_modify_allowed_sources'])

        response, _ = self._put_account_agency(client, basic_settings, 1000)
        self.assertEqual(response.status_code, 200)

    def test_put_agency_no_permission(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
        ])

        basic_settings = {
            'id': 1,
            'name': 'changed name',
            'default_account_manager': '3',
            'agency': 'Alfa&Omega',
            'currency': 'USD',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1)
        self.assertEqual(response.status_code, 401)

    def test_put_agency(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
            'can_set_agency_for_account',
        ])

        basic_settings = {
            'id': 1,
            'name': 'changed name',
            'default_account_manager': '3',
            'agency': 'Alfa&Omega',
            'currency': 'USD',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1)
        self.assertEqual(response.status_code, 200)

        account = models.Account.objects.get(pk=1)
        self.assertEqual(1, account.agency_id)

    def test_put_new_agency(self):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
            'can_set_agency_for_account',
        ])

        basic_settings = {
            'id': 1,
            'name': 'changed name',
            'default_account_manager': '3',
            'agency': 'New agency',
            'currency': 'USD',
        }

        response, _ = self._put_account_agency(client, basic_settings, 1)
        self.assertEqual(response.status_code, 200)

        account = models.Account.objects.select_related('agency').get(pk=1)
        self.assertEqual('New agency', account.agency.name)
        self.assertEqual(2, account.agency_id)

    def test_get_account_manager_users_no_permission(self):
        client = self._get_client_with_permissions([])
        user = User.objects.get(pk=2)
        agency = models.Agency.objects.get(pk=1)
        agency.users.add(user)

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertIsNone(response['data'].get('account_managers'))

    def test_get_account_manager_users_from_agency(self):
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
        self.assertCountEqual(response['data']['account_managers'], [
            {
                'id': '2',
                'name': 'user@test.com',
            }
        ])

    def test_get_account_manager_users_from_account(self):
        client = self._get_client_with_permissions([
            'can_modify_account_manager'
        ])
        user = User.objects.get(pk=2)
        account = models.Account.objects.get(pk=1000)
        account.users.add(user)

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertCountEqual(response['data']['account_managers'], [
            {
                'id': '2',
                'name': 'user@test.com',
            }
        ])

    def test_get_account_manager_users_can_see_all_users(self):
        client = self._get_client_with_permissions([
            'can_modify_account_manager',
            'can_see_all_users_for_managers',
        ])
        user = User.objects.get(pk=2)
        account = models.Account.objects.get(pk=1000)
        account.users.add(user)

        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1000}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']['account_managers']), 5)

    def test_get_no_permission_can_modify_account_type(self):
        client = self._get_client_with_permissions([])
        response = client.get(
            reverse('account_settings', kwargs={'account_id': 1}),
            follow=True
        ).json()

        self.assertTrue(response['success'])
        self.assertDictEqual(response['data']['settings'], {
            'id': '1',
            'archived': False,
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [1],
            'currency': 'USD',
        })

    @patch('requests.get')
    @patch('requests.post')
    def test_put(self, mock_request, mock_page_id):
        client = self._get_client_with_permissions([
            'can_modify_account_name',
            'can_modify_account_manager',
            'can_modify_account_type',
            'can_modify_allowed_sources',
            'can_set_account_sales_representative',
            'can_set_account_cs_representative',
            'can_modify_facebook_page',
        ])
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        response._content = b'{"id": "1234"}'
        mock_page_id.return_value = response

        add_permissions(User.objects.get(pk=2), ['campaign_settings_cs_rep'])

        response = client.put(
            reverse('account_settings', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'name': 'changed name',
                    'default_sales_representative': '1',
                    'default_cs_representative': '2',
                    'default_account_manager': '3',
                    'account_type': '4',
                    'salesforce_url': '',
                    'id': '1',
                    'allowed_sources': {
                        '1': {'allowed': True}
                    },
                    'facebook_page': 'http://www.facebook.com/dummy_page',
                    'currency': 'USD',
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
            'default_cs_representative': User.objects.get(pk=2),
            'default_account_manager': User.objects.get(pk=3),
            'account_type': 4,
            'name': 'changed name',
            'salesforce_url': None,
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [1],
        })
        self.assertEqual(content['data']['settings']['facebook_page'], 'http://www.facebook.com/dummy_page')
        self.assertEqual(content['data']['settings']['facebook_status'], 'Pending')

        hist = history_helpers.get_account_history(account).first()
        self.assertEqual(constants.HistoryActionType.SETTINGS_CHANGE, hist.action_type)

    def test_put_no_permission_can_modify_account_type(self):
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
                    'currency': 'USD',
                }
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)

    def test_put_no_permission_can_modify_allowed_sources(self):
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
                    'currency': 'USD',
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
            {'allowed_sources': ['Can\'t save changes because media source Source 2 is still used on this account.']}
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
            '1': {'name': 'Source 1', 'allowed': True, 'released': True, 'deprecated': True},
            '2': {'name': 'Source 2', 'allowed': True, 'released': True, 'deprecated': False},
            '3': {'name': 'Source 3', 'released': False, 'deprecated': False},
            '100': {'name': 'AdsNative', 'released': True, 'deprecated': False},
            '200': {'name': 'Facebook', 'released': True, 'deprecated': False},
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
            '1': {'name': 'Source 1', 'allowed': True, 'released': True, 'deprecated': True},
            '2': {'name': 'Source 2', 'allowed': True, 'released': True, 'deprecated': False},
            '100': {'name': 'AdsNative', 'released': True, 'deprecated': False},
            '200': {'name': 'Facebook', 'released': True, 'deprecated': False},
        })

    def test_add_error_to_account_agency_form(self):
        view = agency.AccountSettings()
        form = self._get_form_with_allowed_sources_dict({})
        view.add_error_to_account_agency_form(form, [1, 2])
        self.assertEqual(
            dict(form.errors),
            {
                'allowed_sources':
                    ['Can\'t save changes because media sources Source 1, Source 2 are still used on this account.']
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
                    ['Can\'t save changes because media source Source 1 is still used on this account.']
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

    def test_change_currency_account_has_campaigns(self):
        client = self._get_client_with_permissions([])

        response = client.put(
            reverse('account_settings', kwargs={'account_id': 1}),
            json.dumps({
                'settings': {
                    'id': 1,
                    'currency': 'EUR',
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertFalse(content['success'])
        self.assertIn('currency', content['data']['errors'])

    def test_change_currency(self):
        user = User.objects.get(pk=2)
        account = magic_mixer.blend(models.Account, users=[user])
        client = self._get_client_with_permissions([])

        response = client.put(
            reverse('account_settings', kwargs={'account_id': account.id}),
            json.dumps({
                'settings': {
                    'id': account.id,
                    'currency': 'EUR',
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(content['data']['settings']['currency'], 'EUR')

        account.refresh_from_db()
        self.assertEqual(account.currency, 'EUR')


class AccountUsersTest(TestCase):
    fixtures = ['test_views.yaml', 'test_agency.yaml']

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)
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
        user = User.objects.get(pk=2)

        self.assertIsNone(response.json()['data']['agency_managers'])
        self.assertCountEqual([
            {
                'name': '',
                'is_active': True,
                'is_agency_manager': False,
                'id': 2,
                'last_login': user.last_login.date().isoformat(),
                'email': 'user@test.com'
            },
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': False,
                'id': 3,
                'last_login': '2014-06-16',
                'email': 'john@test.com'
            },
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': False,
                'id': 1,
                'last_login': '2014-06-16',
                'email': 'superuser@test.com'
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

        user = User.objects.get(pk=2)
        response = client.get(
            reverse('account_users', kwargs={'account_id': 1}),
        )

        self.assertCountEqual([
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': True,
                'id': 1,
                'last_login': '2014-06-16',
                'email': 'superuser@test.com'
            }
        ],
            response.json()['data']['agency_managers']
        )

        self.assertCountEqual([
            {
                'name': '',
                'is_active': True,
                'is_agency_manager': False,
                'id': 2,
                'last_login': user.last_login.date().isoformat(),
                'email': 'user@test.com'
            },
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': False,
                'id': 3,
                'last_login': '2014-06-16',
                'email': 'john@test.com'
            },
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': False,
                'id': 1,
                'last_login': '2014-06-16',
                'email': 'superuser@test.com'
            }
        ],
            response.json()['data']['users']
        )

    def test_get_agency_with_can_see_agency_managers(self):
        client = self._get_client_with_permissions([
            'account_agency_access_permissions',
            'can_see_agency_managers_under_access_permissions',
        ])

        acc = models.Account.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        acc.agency = agency
        acc.save(fake_request(User.objects.get(pk=1)))

        user = User.objects.get(pk=1)
        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        response = client.get(
            reverse('account_users', kwargs={'account_id': 1}),
        )

        self.assertCountEqual([
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': True,
                'id': 1,
                'last_login': '2014-06-16',
                'email': 'superuser@test.com'
            }
        ],
            response.json()['data']['agency_managers']
        )

        self.assertCountEqual([
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': True,
                'id': 1,
                'last_login': '2014-06-16',
                'email': 'superuser@test.com'
            },
            {
                'name': '',
                'is_active': True,
                'is_agency_manager': False,
                'id': 2,
                'last_login': user.last_login.date().isoformat(),
                'email': 'user@test.com'
            },
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': False,
                'id': 3,
                'last_login': '2014-06-16',
                'email': 'john@test.com'
            },
            {
                'name': '',
                'is_active': False,
                'is_agency_manager': False,
                'id': 1,
                'last_login': '2014-06-16',
                'email': 'superuser@test.com'
            }
        ],
            response.json()['data']['users']
        )

    def test_remove_normal_user(self):
        client = self._get_client_with_permissions([
            'account_agency_access_permissions',
        ])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))

        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        acc1.users.add(user)
        acc2.users.add(user)
        response = client.delete(
            reverse('account_users_manage', kwargs={'account_id': 1, 'user_id': user.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertTrue(acc2.users.filter(pk=user.pk))

    def test_remove_normal_user_from_all_accounts(self):
        client = self._get_client_with_permissions([
            'account_agency_access_permissions',
        ])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))

        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        acc1.users.add(user)
        acc2.users.add(user)
        response = client.delete(
            reverse('account_users_manage', kwargs={'account_id': 1,
                                                    'user_id': user.pk}) + '?remove_from_all_accounts=1',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertFalse(acc2.users.filter(pk=user.pk))

    def test_remove_agency_user(self):
        client = self._get_client_with_permissions([
            'account_agency_access_permissions',
        ])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))

        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        user.first_name = 'Someone'
        user.last_name = 'Important'
        user.save()

        acc1.users.add(user)
        acc2.users.add(user)
        agency.users.add(user)

        response = client.delete(
            reverse('account_users_manage', kwargs={'account_id': 1, 'user_id': user.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertFalse(acc2.users.filter(pk=user.pk))
        self.assertFalse(agency.users.filter(pk=user.pk))
        self.assertEqual(
            models.History.objects.filter(agency=agency, account=None).order_by('-created_dt').first().changes_text,
            'Removed agency user Someone Important (user@test.com)'
        )


class UserPromoteTest(TestCase):
    fixtures = ['test_views.yaml', 'test_agency.yaml']

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_without_permission(self):
        client = self._get_client_with_permissions([])

        response = client.post(
            reverse('account_user_action', kwargs={'account_id': 1000, 'user_id': 2, 'action': 'promote'}),
        )

        self.assertEqual(401, response.status_code)

    def test_promote(self):
        client = self._get_client_with_permissions([
            'can_promote_agency_managers',
        ])

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename='group_agency_manager_add')
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        account.users.add(user)

        response = client.post(
            reverse('account_user_action', kwargs={'account_id': 1000, 'user_id': 2, 'action': 'promote'}),
        )
        self.assertEqual(200, response.status_code)

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)

        self.assertIn(user, agency.users.all())
        self.assertNotIn(user, account.users.all())
        self.assertIn(group, user.groups.all())

    def test_promote_unrelated_user(self):
        client = self._get_client_with_permissions([
            'can_promote_agency_managers',
        ])

        account = models.Account.objects.get(pk=1000)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename='group_agency_manager_add')
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        account.users.add(user)

        user2 = User.objects.get(pk=3)
        account.users.remove(user2)

        response = client.post(
            reverse('account_user_action', kwargs={'account_id': 1000, 'user_id': 3, 'action': 'promote'}),
        )
        self.assertEqual(401, response.status_code)
        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=3)
        self.assertNotIn(user, agency.users.all())
        self.assertNotIn(user, account.users.all())


class UserDowngradeTest(TestCase):
    fixtures = ['test_views.yaml', 'test_agency.yaml']

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_without_permission(self):
        client = self._get_client_with_permissions([])

        response = client.post(
            reverse('account_user_action', kwargs={'account_id': 1000, 'user_id': 2, 'action': 'downgrade'}),
        )

        self.assertEqual(401, response.status_code)

    def test_downgrade(self):
        client = self._get_client_with_permissions([
            'can_promote_agency_managers',
        ])

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename='group_agency_manager_add')
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        agency.users.add(user)
        user.groups.add(group)

        response = client.post(
            reverse('account_user_action', kwargs={'account_id': 1000, 'user_id': 2, 'action': 'downgrade'}),
        )
        self.assertEqual(200, response.status_code)

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)

        self.assertNotIn(user, agency.users.all())
        self.assertIn(user, account.users.all())
        self.assertNotIn(group, user.groups.all())

    def test_downgrade_unrelated_user(self):
        client = self._get_client_with_permissions([
            'can_promote_agency_managers',
        ])

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename='group_agency_manager_add')
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        agency.users.add(user)

        user2 = User.objects.get(pk=3)
        account.users.remove(user2)

        response = client.post(
            reverse('account_user_action', kwargs={'account_id': 1000, 'user_id': 3, 'action': 'downgrade'}),
        )
        self.assertEqual(401, response.status_code)
        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=3)
        self.assertNotIn(user, agency.users.all())
        self.assertNotIn(user, account.users.all())


class CampaignContentInsightsTest(TestCase):
    fixtures = ['test_views.yaml']

    def user(self):
        return User.objects.get(pk=2)

    @patch('redshiftapi.api_breakdowns.query')
    def test_permission(self, mock_query):
        cis = agency.CampaignContentInsights()
        with self.assertRaises(exc.AuthorizationError):
            cis.get(fake_request(self.user()), 1)

        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [],
                'worst_performer_rows': [],
            },
            'success': True,
        }, json.loads(response.content))

    @patch('redshiftapi.api_breakdowns.query')
    def test_basic_archived(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1,
            archived=True,
        )
        cad.save()

        mock_query.return_value = [
            {
                'content_ad_id': cad.id,
                'clicks': 1000,
                'impressions': 10000,
            }
        ]
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual({
            'data': {
                'metric': 'CTR',
                'summary': 'Title',
                'best_performer_rows': [],
                'worst_performer_rows': [],
            },
            'success': True,
        }, json.loads(response.content))

    @patch('redshiftapi.api_breakdowns.query')
    def test_basic_title_ctr(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1
        )
        cad.save()

        mock_query.return_value = [
            {
                'content_ad_id': cad.id,
                'clicks': 1000,
                'impressions': 10000,
            }
        ]
        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(http.client.OK, response.status_code)
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

    @patch('redshiftapi.api_breakdowns.query')
    def test_duplicate_title_ctr(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad1 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1
        )
        cad1.save()

        cad2 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.bidder.com',
            batch_id=1
        )
        cad2.save()

        mock_query.return_value = [
            {
                'content_ad_id': cad1.id,
                'clicks': 1000,
                'impressions': 10000,
            },
            {
                'content_ad_id': cad2.id,
                'clicks': 9000,
                'impressions': 10000,
            }
        ]

        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(http.client.OK, response.status_code)
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

    @patch('redshiftapi.api_breakdowns.query')
    def test_order_title_ctr(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ['can_view_campaign_content_insights_side_tab'])

        campaign = models.Campaign.objects.get(pk=1)
        cad1 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title='Test Ad',
            url='http://www.zemanta.com',
            batch_id=1
        )
        cad1.save()

        cad2 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title='Awesome Ad',
            url='http://www.bidder.com',
            batch_id=1
        )
        cad2.save()

        mock_query.return_value = [
            {
                'content_ad_id': cad1.id,
                'clicks': 100,
                'impressions': 100000,
            },
            {
                'content_ad_id': cad2.id,
                'clicks': 1000,
                'impressions': 100000,
            }
        ]

        response = cis.get(fake_request(self.user()), 1)
        self.assertEqual(http.client.OK, response.status_code)
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
                        'metric': '0.10%',
                        'summary': 'Test Ad',
                    },
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
            level=constants.HistoryLevel.AD_GROUP,
            changes={'name': 'test'},
            changes_text="Name changed to 'test'",
            created_by=self.user,
        )

        models.History.objects.create(
            campaign=campaign,
            account=account,
            level=constants.HistoryLevel.CAMPAIGN,
            changes={'targeting': ['US']},
            changes_text="Geographic targeting changed to 'US'",
            created_dt=self.dt,
            created_by=self.user,
        )
        models.History.objects.create(
            account=account,
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

        response = self.get_history({'level': 0})
        self.assertFalse(response['success'])

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

    class HistoryTest(models.HistoryMixinOld):

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
        mix.snapshot()
        self.assertEqual({'test_field': ''}, mix.snapshotted_state)
        self.assertTrue(mix.post_init_newly_created)

        mix.id = 5
        mix.snapshot(previous=mix)

        self.assertEqual({'test_field': ''}, mix.snapshotted_state)
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
        self.assertDictEqual(content['data'], {'status': 'Connected'})
        get_all_pages_mock.assert_called_with('fake_business_id', 'fake_access_token')

    def _get_client_with_permissions(self, permissions_list):
        password = 'secret'
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client
