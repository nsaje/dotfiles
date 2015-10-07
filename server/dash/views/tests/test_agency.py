# -*- coding: utf-8 -*-
import json
import datetime
from mock import patch, ANY, Mock, call
import pytz

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.core import mail
from django.contrib.auth.models import Permission
from django.conf import settings

from zemauth.models import User
from dash import models
from dash import constants
from dash.views import agency


@patch('dash.views.agency.api.order_ad_group_settings_update')
@patch('dash.views.agency.actionlog_api')
class AdGroupSettingsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        self.maxDiff = None
        self.settings_dict = {
            'settings': {
                'state': 1,
                'start_date': '2015-05-01',
                'end_date': '2015-06-30',
                'cpc_cc': '0.3000',
                'daily_budget_cc': '200.0000',
                'target_devices': ['desktop'],
                'target_regions': ['693', 'GB'],
                'name': 'Test ad group name',
                'id': 1
            }
        }

        user = User.objects.get(pk=1)
        self.client.login(username=user.email, password='secret')

    def test_put_update_settings(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        # we need this to track call order across multiple mocks
        mock_manager = Mock()
        mock_manager.attach_mock(mock_actionlog_api, 'mock_actionlog_api')
        mock_manager.attach_mock(mock_order_ad_group_settings_update, 'mock_order_ad_group_settings_update')

        old_settings = ad_group.get_current_settings()

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
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
                    'target_regions': ['693', 'GB'],
                    'tracking_code': '',
                    'enable_ga_tracking': True,
                    'enable_adobe_tracking': False,
                    'adobe_tracking_param': ''
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
            call.mock_actionlog_api.init_enable_ad_group(ad_group, ANY, order=ANY, send=False)
        ])

    def test_put_create_settings(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=10)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        # this ad group does not have settings
        current_settings = ad_group.get_current_settings()
        self.assertIsNone(current_settings.pk)

        self.settings_dict['settings']['id'] = 10

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        self.assertEqual(json.loads(response.content), {
            'data': {
                'action_is_waiting': True,
                'settings': {
                    'cpc_cc': '0.30',
                    'daily_budget_cc': '200.00',
                    'end_date': '2015-06-30',
                    'id': '10',
                    'name': 'Test ad group name',
                    'start_date': '2015-05-01',
                    'state': 1,
                    'target_devices': ['desktop'],
                    'target_regions': ['693', 'GB'],
                    'tracking_code': '',
                    'enable_ga_tracking': True,
                    'adobe_tracking_param': '',
                    'enable_adobe_tracking': False

                }
            },
            'success': True
        })

        new_settings = ad_group.get_current_settings()
        self.assertIsNotNone(new_settings.pk)

        self.assertFalse(mock_actionlog_api.init_enable_ad_group.called)
        self.assertFalse(mock_order_ad_group_settings_update.called)

        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
        default_sources_settings = models.DefaultSourceSettings.objects.filter(auto_add=True).with_credentials()
        self.assertEqual(default_sources_settings.count(), 2)
        self.assertEqual(ad_group_sources.count(), 1)

        for ad_group_source in ad_group_sources:
            default_settings = models.DefaultSourceSettings.objects.get(source=ad_group_source.source)
            # only one settings per ad group source should exist
            ad_group_source_settings = models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source)

            # one settings created ad group source save, the second should be our defaults
            self.assertEqual(ad_group_source_settings.count(), 2)

            ad_group_source_settings = ad_group_source_settings.latest()

            self.assertEqual(ad_group_source_settings.daily_budget_cc, default_settings.daily_budget_cc)
            # the settings are desktop only
            self.assertEqual(ad_group_source_settings.cpc_cc, default_settings.default_cpc_cc)

            # auto_add enabled source was added
            self.assertTrue(default_settings)

    def test_put_without_non_propagated_settings(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_actionlog_api.is_waiting_for_set_actions.return_value = True
        old_settings = ad_group.get_current_settings()

        self.settings_dict['settings']['cpc_cc'] = None
        self.settings_dict['settings']['daily_budget_cc'] = None

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_settings_dict = json.loads(response.content)['data']['settings']

        self.assertEqual(response_settings_dict['cpc_cc'], '')
        self.assertEqual(response_settings_dict['daily_budget_cc'], '')

        new_settings = ad_group.get_current_settings()

        request = HttpRequest()
        request.user = User(id=1)

        # can it actually be saved to the db
        new_settings.save(request)

        self.assertEqual(new_settings.cpc_cc, None)
        self.assertEqual(new_settings.daily_budget_cc, None)

        mock_order_ad_group_settings_update.assert_called_with(
            ad_group, old_settings, new_settings, ANY, send=False)

    def test_put_tracking_codes_with_permission(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        self.settings_dict['settings']['tracking_code'] = 'asd=123'
        self.settings_dict['settings']['enable_ga_tracking'] = False

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_settings_dict = json.loads(response.content)['data']['settings']

        self.assertEqual(response_settings_dict['tracking_code'], 'asd=123')
        self.assertEqual(response_settings_dict['enable_ga_tracking'], False)

    def test_put_invalid_target_region(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        self.settings_dict['settings']['target_regions'] = ["123"]

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertIn('target_regions', response_dict['data']['errors'])

    def test_put_us_and_dmas(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        self.settings_dict['settings']['target_regions'] = ['US', '693']

        response = self.client.put(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            json.dumps(self.settings_dict),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertIn('target_regions', response_dict['data']['errors'])

    def test_get_ad_group_sources_with_settings(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_source = models.AdGroupSource.objects.get(id=1)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_TARGETING_AUTOMATIC
        )
        ad_group_source.source.source_type.save()

        ad_group_source = models.AdGroupSource.objects.get(id=2)
        ad_group_source.source.source_type.available_actions.append(
            constants.SourceAction.CAN_MODIFY_DMA_TARGETING_MANUAL
        )
        ad_group_source.source.source_type.save()

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        response = self.client.get(
            reverse('ad_group_settings', kwargs={'ad_group_id': ad_group.id}),
            follow=True
        )

        response_dict = json.loads(response.content)

        self.assertItemsEqual(response_dict['data']['ad_group_sources'], [{
            'source_state': 1,
            'source_name': 'AdsNative',
            'supports_dma_targeting': True,
            'id': 1
        }, {
            'source_state': 2,
            'source_name': 'Gravity',
            'supports_dma_targeting': True,
            'id': 2
        }, {
            'source_state': 2,
            'source_name': 'Outbrain',
            'supports_dma_targeting': False,
            'id': 3
        }])


@patch('dash.views.agency.api.order_ad_group_settings_update')
@patch('dash.views.agency.actionlog_api')
class AdGroupSettingsAutoAddMediaSourcesTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User(id=1)
        self.request.META['SERVER_NAME'] = 'testname'
        self.request.META['SERVER_PORT'] = 1234

    def test_put_create_settings_dont_auto_add_mobile(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=10)
        current_settings = ad_group.get_current_settings()

        current_settings.target_devices = ['mobile']

        agency.AdGroupSettings()._add_media_sources(ad_group, current_settings, self.request)

        # media sources with default settings that include mobile_cpc_cc should be added
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
        default_sources_settings = models.DefaultSourceSettings.objects.filter(auto_add=True).with_credentials()
        self.assertEqual(default_sources_settings.count(), 2)
        self.assertEqual(ad_group_sources.count(), 2)

        for ad_group_source in ad_group_sources:
            default_settings = models.DefaultSourceSettings.objects.get(source=ad_group_source.source)

            ad_group_source_settings = models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source).latest()

            self.assertIsNotNone(default_settings.mobile_cpc_cc)
            self.assertEqual(ad_group_source_settings.daily_budget_cc, default_settings.daily_budget_cc)
            self.assertEqual(ad_group_source_settings.cpc_cc, default_settings.mobile_cpc_cc)

    def test_put_create_settings_dont_auto_add_desktop(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=10)
        current_settings = ad_group.get_current_settings()

        current_settings.target_devices = ['desktop']

        agency.AdGroupSettings()._add_media_sources(ad_group, current_settings, self.request)

        # media sources with default settings that include default_cpc_cc should be added
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
        default_sources_settings = models.DefaultSourceSettings.objects.filter(auto_add=True).with_credentials()
        self.assertEqual(default_sources_settings.count(), 2)
        self.assertEqual(ad_group_sources.count(), 1)

        for ad_group_source in ad_group_sources:
            default_settings = models.DefaultSourceSettings.objects.get(source=ad_group_source.source)

            ad_group_source_settings = models.AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source).latest()

            self.assertIsNotNone(default_settings.default_cpc_cc)
            self.assertEqual(ad_group_source_settings.daily_budget_cc, default_settings.daily_budget_cc)
            self.assertEqual(ad_group_source_settings.cpc_cc, default_settings.default_cpc_cc)

    def test_put_create_settings_dont_auto_add_mobile_and_desktop(self, mock_actionlog_api,
                                                                  mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=10)
        current_settings = ad_group.get_current_settings()

        current_settings.target_devices = ['desktop', 'mobile']

        agency.AdGroupSettings()._add_media_sources(ad_group, current_settings, self.request)

        # media sources with default settings that include default_cpc_cc should be added
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
        default_sources_settings = models.DefaultSourceSettings.objects.filter(auto_add=True).with_credentials()
        self.assertEqual(default_sources_settings.count(), 2)
        self.assertEqual(ad_group_sources.count(), 1)

        for ad_group_source in ad_group_sources:
            default_settings = models.DefaultSourceSettings.objects.get(source=ad_group_source.source)

            ad_group_source_settings = models.AdGroupSourceSettings.objects\
                                                                   .filter(ad_group_source=ad_group_source).latest()

            self.assertEqual(ad_group_source_settings.daily_budget_cc, default_settings.daily_budget_cc)
            self.assertEqual(ad_group_source_settings.cpc_cc, default_settings.default_cpc_cc)


class AdGroupAgencyTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        self.maxDiff = None
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

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
                        {'name': 'Locations', 'value': 'worldwide'},
                        {'name': 'Tracking code', 'value': 'test tracking code'},
                        {'name': 'Archived', 'value': 'False'},
                        {'name': 'Display URL', 'value': ''},
                        {'name': 'Brand name', 'value': ''},
                        {'name': 'Description', 'value': ''},
                        {'name': 'Call to action', 'value': ''},
                        {'name': 'AdGroup name', 'value': ''},
                        {'name': 'Enable GA tracking', 'value': 'True'},
                        {'name': 'Enable Adobe tracking', 'value': 'False'},
                        {'name': 'Adobe tracking parameter', 'value': ''},
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
                        {'name': 'Locations', 'old_value': 'worldwide', 'value': 'worldwide'},
                        {'name': 'Tracking code', 'old_value': 'test tracking code', 'value': 'test tracking code'},
                        {'name': 'Archived', 'old_value': 'False', 'value': 'False'},
                        {'name': 'Display URL', 'old_value': '', 'value': ''},
                        {'name': 'Brand name', 'old_value': '', 'value': ''},
                        {'name': 'Description', 'old_value': '', 'value': ''},
                        {'name': 'Call to action', 'old_value': '', 'value': ''},
                        {'name': 'AdGroup name', 'old_value': '', 'value': ''},
                        {'name': 'Enable GA tracking', 'old_value': 'True', 'value': 'True'},
                        {'name': 'Enable Adobe tracking', 'old_value': 'False', 'value': 'False'},
                        {'name': 'Adobe tracking parameter', 'old_value': '', 'value': ''},
                    ],
                    'show_old_settings': True
                }]
            },
            'success': True
        })


class AccountConversionPixelsTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.login(username=user.email, password='secret')

    @patch('dash.views.agency.redshift.get_pixels_last_verified_dt')
    def test_get(self, redshift_get_mock):
        utcnow = datetime.datetime.utcnow()
        redshift_get_mock.return_value = {(1, 'test'): utcnow}

        account = models.Account.objects.get(pk=1)
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

    def test_get_no_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.remove(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            follow=True
        )
        self.assertEqual(404, response.status_code)

    @patch('dash.views.agency.redshift.get_pixels_last_verified_dt')
    def test_get_with_permissions(self, redshift_get_mock):
        utcnow = datetime.datetime.utcnow()
        redshift_get_mock.return_value = {(1, 'test'): utcnow}

        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.add(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
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

    def test_post(self):
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

    def test_post_without_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.remove(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'slug'}),
            content_type='application/json',
            follow=True
        )
        self.assertEqual(404, response.status_code)

    def test_post_with_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.add(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.post(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            json.dumps({'slug': 'slug'}),
            content_type='application/json',
            follow=True
        )
        self.assertEqual(200, response.status_code)

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
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.login(username=user.email, password='secret')

    def test_put(self):
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

    def test_put_no_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.remove(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(404, response.status_code)

    def test_put_with_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.add(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.put(
            reverse('conversion_pixel', kwargs={'conversion_pixel_id': 1}),
            json.dumps({'archived': True}),
            content_type='application/json',
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_put_invalid_pixel(self):
        conversion_pixel = models.ConversionPixel.objects.latest('id')
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
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.login(username=user.email, password='secret')

    def test_get(self):
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({
            'rows': [
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
                    'conversion_window': 7,
                    'goal_id': '1',
                    'pixel': {
                        'id': 1,
                        'slug': 'test',
                        'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
                        'archived': False,
                    },
                },
            ],
            'available_pixels': []
        }, decoded_response['data'])

    def test_get_no_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_goals')
        user = User.objects.get(pk=2)
        user.user_permissions.remove(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            follow=True,
        )

        self.assertEqual(404, response.status_code)

        user.user_permissions.add(permission)
        self.client.login(username=user.email, password='secret')
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 1}),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

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
        self.assertEqual({
            'rows': [
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
                    'conversion_window': 7,
                    'goal_id': '1',
                    'pixel': {
                        'id': 1,
                        'slug': 'test',
                        'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
                        'archived': False,
                    },
                },
            ],
            'available_pixels': [{
                'id': new_pixel.id,
                'slug': 'new',
            }]
        }, decoded_response['data'])

    def test_get_non_existing_campaign(self):
        response = self.client.get(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 9876}),
            follow=True
        )
        self.assertEqual(404, response.status_code)

    def test_post(self):
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

    def test_post_no_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_goals')
        user = User.objects.get(pk=2)
        user.user_permissions.remove(permission)

        self.client.login(username=user.email, password='secret')
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
        self.assertEqual(404, response.status_code)

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
                'conversion_window': 7,
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
            'conversion_window': 7,
        }

        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps(data),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)

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

    def test_post_pixel_not_unique_goal_id(self):
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion goal',
                'type': 1,
                'conversion_window': 7,
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
                'type': 1,
                'conversion_window': 7,
                'goal_id': '1'
            }),
            content_type='application/json',
            follow=True
        )
        self.assertEqual(400, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual({'goal_id': ['This field has to be unique.']}, decoded_response['data']['errors'])

    def test_post_pixel_invalid_account(self):
        models.Account.objects.get(id=2).users.add(User.objects.get(id=1))
        response = self.client.post(
            reverse('campaign_conversion_goals', kwargs={'campaign_id': 2}),
            json.dumps({
                'name': 'conversion pixel',
                'type': 1,
                'goal_id': '1',
                'conversion_window': 7,
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
                'conversion_window': 7,
            }),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(404, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual('Invalid conversion pixel', decoded_response['data']['message'])


class ConversionGoalTestCase(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.login(username=user.email, password='secret')

    def test_delete_no_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_goals')
        user = User.objects.get(pk=2)

        user.user_permissions.remove(permission)
        self.client.login(username=user.email, password='secret')
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': 1}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)

        user.user_permissions.add(permission)
        self.client.login(username=user.email, password='secret')
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': 1}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)

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

    def test_delete_success(self):
        conversion_goal = models.ConversionGoal.objects.get(id=1)
        response = self.client.delete(
            reverse('conversion_goal', kwargs={'campaign_id': 1, 'conversion_goal_id': conversion_goal.id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        with self.assertRaises(models.ConversionGoal.DoesNotExist):
            models.ConversionGoal.objects.get(id=1)


class UserActivationTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password='secret')

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_send_mail(self):
        request = HttpRequest()
        request.user = User(id=1)

        data = {}
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

    @patch('utils.email_helper.send_email_to_new_user') # , mock=Mock(side_effect=User.DoesNotExist))
    def test_send_mail_failure(self, mock):
        request = HttpRequest()
        request.user = User(id=1)

        mock.side_effect = User.DoesNotExist

        data = {}
        response = self.client.post(
            reverse('account_reactivation', kwargs={'account_id': 1, 'user_id': 1}),
            data,
            follow=True
        )

        decoded_response = json.loads(response.content)
        self.assertFalse(decoded_response.get('success'), 'Failed sending message')


class CampaignBudgetTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    @patch('dash.views.agency.budget.CampaignBudget')
    def test_get(self, MockCampaignBudget):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        MockCampaignBudget.return_value.get_total.return_value = 1000
        MockCampaignBudget.return_value.get_spend.return_value = 666
        MockCampaignBudget.return_value.get_history.return_value = [models.CampaignBudgetSettings.
                                                                    objects.get(pk=1)]

        response = self.client.get(
            '/api/campaigns/1/budget/'
        )
        content = json.loads(response.content)

        self.assertTrue(content['success'])
        self.assertEqual(content['data']['total'], 1000)
        self.assertEqual(content['data']['available'], 334)
        self.assertEqual(content['data']['spend'], 666)
        self.assertEqual(content['data']['history'], [{
            'comment': u'Added budget',
            'revoke': 0.0,
            'datetime': u'2015-09-23T05:57:22',
            'user': u'superuser@test.com',
            'total': 1000.0,
            'allocate': 1000.0
        }])

    def test_get_no_permission(self):
        password = 'secret'
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

        permission = Permission.objects.get(codename='campaign_budget_management_view')
        self.user.user_permissions.remove(permission)

        response = self.client.get(
            '/api/campaigns/1/budget/'
        )
        content = json.loads(response.content)

        self.assertFalse(content['success'])
        self.assertEqual(response.status_code, 404)

    @patch('dash.views.agency.budget.CampaignBudget')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put(self, mock_send_campaign_notification_email, MockCampaignBudget):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        MockCampaignBudget.return_value.get_total.return_value = 1000
        MockCampaignBudget.return_value.get_spend.return_value = 666
        MockCampaignBudget.return_value.get_history.return_value = [models.CampaignBudgetSettings.
                                                                    objects.get(pk=1)]

        response = self.client.put(
            '/api/campaigns/1/budget/',
            json.dumps({
                'action': 'allocate',
                'amount': 1000,
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)

        campaign = models.Campaign.objects.get(pk=1)

        self.assertTrue(content['success'])
        self.assertEqual(content['data']['total'], 1000)
        self.assertEqual(content['data']['available'], 334)
        self.assertEqual(content['data']['spend'], 666)
        self.assertEqual(content['data']['history'], [{
            'comment': u'Added budget',
            'revoke': 0.0,
            'datetime': u'2015-09-23T05:57:22',
            'user': u'superuser@test.com',
            'total': 1000.0,
            'allocate': 1000.0
        }])

        MockCampaignBudget.return_value.edit.assert_called_with(
            revoke_amount=0, allocate_amount=1000.0, request=response.wsgi_request
        )
        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request)

    @patch('dash.views.agency.budget.CampaignBudget')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_no_permission(self, mock_send_campaign_notification_email, MockCampaignBudget):
        password = 'secret'
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

        permission = Permission.objects.get(codename='campaign_budget_management_view')
        self.user.user_permissions.remove(permission)

        response = self.client.put(
            '/api/campaigns/1/budget/',
            json.dumps({
                'action': 'allocate',
                'amount': 1000,
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)

        self.assertFalse(content['success'])
        self.assertEqual(response.status_code, 404)

        self.assertFalse(MockCampaignBudget.return_value.edit.called)
        self.assertFalse(mock_send_campaign_notification_email.called)


class CampaignAgencyTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_get(self):
        response = self.client.get(
            '/api/campaigns/1/agency/'
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])
        self.assertEqual(content['data']['settings']['name'], 'test campaign 1')
        self.assertEqual(content['data']['settings']['iab_category'], 'IAB24')

    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_post(self, mock_send_campaign_notification_email):
        response = self.client.put(
            '/api/campaigns/1/agency/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'account_manager': 1,
                    'iab_category': 'IAB17',
                    'name': 'ignore name'
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)

        self.assertTrue(content['success'], True)

        campaign = models.Campaign.objects.get(pk=1)
        settings = campaign.get_current_settings()

        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertEqual(settings.account_manager_id, 1)
        self.assertEqual(settings.iab_category, 'IAB17')

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request)


class CampaignSettingsTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

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
        self.assertEqual(content['data']['settings']['goal_quantity'], 0)

    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_post(self, mock_send_campaign_notification_email):
        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
                    'goal_quantity': 10,
                }
            }),
            content_type='application/json',
        )
        content = json.loads(response.content)
        self.assertTrue(content['success'])

        campaign = models.Campaign.objects.get(pk=1)
        settings = campaign.get_current_settings()
        self.assertEqual(campaign.name, 'test campaign 2')
        self.assertEqual(settings.goal_quantity, 10)
        self.assertEqual(settings.campaign_goal, 2)

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request)

    def test_validation(self):
        response = self.client.put(
            '/api/campaigns/1/settings/',
            json.dumps({
                'settings': {
                    'id': 1,
                    'name': 'test campaign 2',
                    'campaign_goal': 2,
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
