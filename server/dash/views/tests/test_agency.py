# -*- coding: utf-8 -*-
import json
import datetime
from mock import patch, ANY

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.core import mail
from django.contrib.auth.models import Permission
from django.conf import settings

from zemauth.models import User
from dash import models
from dash import constants


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

    def test_put(self, mock_actionlog_api, mock_order_ad_group_settings_update):
        ad_group = models.AdGroup.objects.get(pk=1)

        mock_actionlog_api.is_waiting_for_set_actions.return_value = True

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
                    'enable_ga_tracking': True
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

    def test_get(self):
        account = models.Account.objects.get(pk=1)
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': account.id}),
            follow=True
        )
        decoded_response = json.loads(response.content)

        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertEqual([{
            'id': 1,
            'slug': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'status': constants.ConversionPixelStatus.get_text(constants.ConversionPixelStatus.NOT_USED),
            'last_verified_dt': None,
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

    def test_get_with_permissions(self):
        permission = Permission.objects.get(codename='manage_conversion_pixels')
        user = User.objects.get(pk=2)
        user.user_permissions.add(permission)

        self.client.login(username=user.email, password='secret')
        response = self.client.get(
            reverse('account_conversion_pixels', kwargs={'account_id': 1}),
            follow=True
        )
        decoded_response = json.loads(response.content)

        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response['success'])
        self.assertEqual([{
            'id': 1,
            'slug': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'status': constants.ConversionPixelStatus.get_text(constants.ConversionPixelStatus.NOT_USED),
            'last_verified_dt': None,
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
            'slug': 'test',
            'url': settings.CONVERSION_PIXEL_PREFIX + '1/test/',
            'status': constants.ConversionPixelStatus.get_text(constants.ConversionPixelStatus.NOT_USED),
            'last_verified_dt': None,
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
