# -*- coding: utf-8 -*-
import json
import datetime
import pytz

from mock import patch, ANY, Mock, call
from decimal import Decimal

from django.test import TestCase
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
from utils import exc


@patch('dash.views.agency.api.order_ad_group_settings_update')
@patch('dash.views.agency.actionlog_api')
class AdGroupSettingsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

        # we need this to track call order across multiple mocks
        mock_manager = Mock()
        mock_manager.attach_mock(mock_actionlog_api, 'mock_actionlog_api')
        mock_manager.attach_mock(mock_order_ad_group_settings_update, 'mock_order_ad_group_settings_update')

        old_settings = ad_group.get_current_settings()
        self.assertIsNotNone(old_settings.pk)

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
        mock_log_useraction.assert_called_with(
            response.wsgi_request, constants.UserActionType.SET_AD_GROUP_SETTINGS, ad_group=ad_group)

    def test_put_without_non_propagated_settings(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_actionlog_api.is_waiting_for_set_actions.return_value = True
        old_settings = ad_group.get_current_settings()

        self.assertIsNotNone(old_settings.pk)

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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put_firsttime_create_settings(self, mock_log_useraction, mock_actionlog_api,
                                           mock_order_ad_group_settings_update):
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

        self.assertTrue(mock_actionlog_api.init_enable_ad_group.called)

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

        latest_account_settings = models.AccountSettings.objects.latest('created_dt')
        self.assertEqual('Added conversion pixel with unique identifier slug.',
                         latest_account_settings.changes_text)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.CREATE_CONVERSION_PIXEL,
            account=models.Account.objects.get(pk=1))

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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_put(self, mock_log_useraction):
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

    def test_put_archive_no_permissions(self):
        user = User.objects.get(pk=2)

        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user.user_permissions.add(permission)
        permission = Permission.objects.get(codename='archive_restore_entity')
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
        user = User.objects.get(pk=2)
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user.user_permissions.add(permission)
        permission = Permission.objects.get(codename='archive_restore_entity')
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
                    'conversion_window': 168,
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
                'id': 1,
                'slug': 'test'
            }]
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
                    'conversion_window': 168,
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
                'id': 1,
                'slug': 'test',
            }, {
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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_delete_success(self, mock_log_useraction):
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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.budget.CampaignBudget')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put(self, mock_send_campaign_notification_email, MockCampaignBudget, mock_log_useraction):
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
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CAMPAIGN_BUDGET,
            campaign=campaign
        )

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

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_post(self, mock_send_campaign_notification_email, mock_log_useraction, _):
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

        self.assertTrue(content['success'])

        campaign = models.Campaign.objects.get(pk=1)
        settings = campaign.get_current_settings()

        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertEqual(settings.account_manager_id, 1)
        self.assertEqual(settings.iab_category, 'IAB17')

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CAMPAIGN_AGENCY_SETTINGS,
            campaign=campaign
        )


class CampaignSettingsTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def _login_user(self, user_id):
        password = 'secret'
        self.user = User.objects.get(pk=user_id)
        self.client.login(username=self.user.email, password=password)

    def test_get(self):
        self._login_user(1)

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

    def test_get_no_campaign_settings_permission(self):
        self._login_user(2)

        response = self.client.get(
            '/api/campaigns/1/settings/'
        )

        self.assertEqual(response.status_code, 404)

    def test_get_no_ad_group_default_settings_permission(self):
        self._login_user(2)
        permission = Permission.objects.get(codename='campaign_settings_view')
        self.user.user_permissions.add(permission)

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
        self._login_user(1)

        campaign = models.Campaign.objects.get(pk=1)

        settings = campaign.get_current_settings()
        self.assertEqual(campaign.name, 'test campaign 1')
        self.assertNotEqual(settings.goal_quantity, 10)
        self.assertNotEqual(settings.campaign_goal, 2)
        self.assertNotEqual(settings.target_devices, ['desktop'])
        self.assertNotEqual(settings.target_regions, ['CA', '502'])

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

        mock_send_campaign_notification_email.assert_called_with(campaign, response.wsgi_request)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CAMPAIGN_SETTINGS,
            campaign=campaign)

    def test_put_no_campaign_settings_permission(self):
        self._login_user(2)

        response = self.client.put(
            '/api/campaigns/1/settings/'
        )

        self.assertEqual(response.status_code, 404)

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.agency.email_helper.send_campaign_notification_email')
    def test_put_no_ad_group_default_settings_permission(self, mock_send_campaign_notification_email, mock_log_useraction, mock_insert_adgroup):
        self._login_user(2)
        permission = Permission.objects.get(codename='campaign_settings_view')
        self.user.user_permissions.add(permission)

        settings = models.Campaign.objects.get(pk=1).get_current_settings()
        self.assertNotEqual(settings.goal_quantity, Decimal('10.00'))
        self.assertEqual(settings.target_devices, ['mobile'])
        self.assertEqual(settings.target_regions, ['NC', '501'])

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
        self._login_user(1)

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
        self._login_user(2)
        permission = Permission.objects.get(codename='campaign_settings_view')
        self.user.user_permissions.add(permission)

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
            set([1,])
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


    def test_set_allowed_sources(self):
        account = models.Account.objects.get(pk=1)
        view = agency.AccountAgency()
        view.set_allowed_sources(account, True, self._get_form_with_allowed_sources_dict({
            1: {'allowed': True},
            2: {'allowed': False},
            3: {'allowed': True}
            }))
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1, 3])
        )
    
    def test_set_allowed_sources_cant_remove_unreleased(self):
        account = models.Account.objects.get(pk=1)
        account.allowed_sources.add(3) # add an unreleased source
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1,2,3])
        )
        self.assertFalse(models.Source.objects.get(pk=3).released)

        view = agency.AccountAgency()
        view.set_allowed_sources(
            account,
            False, # no permission to remove unreleased source 3 
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': False},
                2: {'allowed': False},
                3: {'allowed': False}
            }))
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([3,])
        )

    def test_set_allowed_sources_cant_add_unreleased(self):
        account = models.Account.objects.get(pk=1)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1,2])
        )
        self.assertFalse(models.Source.objects.get(pk=3).released)

        view = agency.AccountAgency()
        view.set_allowed_sources(
            account,
            False, # no permission to add unreleased source 3 
            self._get_form_with_allowed_sources_dict({
                1: {'allowed': False},
                2: {'allowed': True},
                3: {'allowed': True}
            }))
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([2,])
        )

    def test_set_allowed_sources_cant_remove_running_source(self):
        account = models.Account.objects.get(pk=111)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([2,3])
        )
        view = agency.AccountAgency()
        form = self._get_form_with_allowed_sources_dict({
            2: {'allowed': False},
            3: {'allowed': True}
        })
        
        view.set_allowed_sources(
            account,
            False, # no permission to add unreleased source 3 
            form
        )
  
        self.assertEqual(
            dict(form.errors),
            {'allowed_sources': [u'Can\'t save changes because media source Source 2 is still used on this account.']}
        )

    def test_set_allowed_sources_none(self):
        account = models.Account.objects.get(pk=1)
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1,2])
        )
        view = agency.AccountAgency()
        view.set_allowed_sources(account, True, self._get_form_with_allowed_sources_dict(None))
        self.assertEqual(
            set(account.allowed_sources.values_list('id', flat=True)),
            set([1,2])
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
            '2': {'name': 'Source 2', 'allowed': True},
            '3': {'name': 'Source 3 (unreleased)'}
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
            '2': {'name': 'Source 2', 'allowed': True},
            })

    def test_add_error_to_account_agency_form(self):
        view = agency.AccountAgency()
        form = self._get_form_with_allowed_sources_dict({})
        view.add_error_to_account_agency_form(form, [1,2])
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

    def test_get_non_removable_sources_source_running(self):
        account = models.Account.objects.get(pk=111)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=11122)
        ad_group_settings.state = constants.AdGroupSettingsState.INACTIVE
        ad_group_settings.save(None)

        view = agency.AccountAgency()
        self.assertEqual(view.get_non_removable_sources(account, [2]), [])

        ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE
        ad_group_settings.save(None)

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

        campaign_settings = models.CampaignSettings.objects.get(pk=1112)
        campaign_settings.archived = True
        campaign_settings.save(None)
        self.assertEqual(view.get_non_removable_sources(account, [2]), [])

        campaign_settings.archived = False
        campaign_settings.save(None)
