# -*- coding: utf-8 -*-

import json
from mock import patch, ANY
import datetime
import decimal

from django.test import TestCase, Client, TransactionTestCase, RequestFactory
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Permission

from zemauth.models import User

from dash import models
from dash import constants
from dash import api
from dash.views import views

from reports import redshift
import reports.models

import actionlog.models
import zemauth.models


class UserTest(TestCase):
    fixtures = ['test_views.yaml']

    class MockDatetime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 3, 1)

    class MockDatetimeNonExistent(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 3, 8, 2, 30)

    class MockDatetimeAmbiguous(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2002, 10, 27, 1, 30, 00)

    @patch('dash.views.views.datetime.datetime', MockDatetime)
    def test_get(self):
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'name': '',
                    'permissions': {},
                    'show_onboarding_guidance': False,
                    'timezone_offset': -18000.0
                }
            },
            'success': True
        })

    @patch('dash.views.views.datetime.datetime', MockDatetimeNonExistent)
    def test_get_non_existent_time(self):
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'name': '',
                    'permissions': {},
                    'show_onboarding_guidance': False,
                    'timezone_offset': -14400.0
                }
            },
            'success': True
        })

    @patch('dash.views.views.datetime.datetime', MockDatetimeAmbiguous)
    def test_get_ambiguous_time(self):
        self.maxDiff = None
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'name': '',
                    'permissions': {},
                    'show_onboarding_guidance': False,
                    'timezone_offset': -14400.0
                }
            },
            'success': True
        })


@patch('dash.views.views.helpers.log_useraction_if_necessary')
class AccountCampaignsTest(TestCase):
    fixtures = ['test_views.yaml']

    class MockSettingsWriter(object):
        def __init__(self, init):
            pass

        def set(self, resource, request):
            pass

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def test_put(self, mock_log_useraction):
        campaign_name = 'New campaign'

        response = self.client.put(
            reverse('account_campaigns', kwargs={'account_id': '1'}),
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)['data']
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], campaign_name)

        campaign_id = data['id']
        campaign = models.Campaign.objects.get(pk=campaign_id)

        self.assertEqual(campaign.name, campaign_name)

        settings = models.CampaignSettings.objects.get(campaign_id=campaign_id)

        self.assertEqual(settings.target_devices, constants.AdTargetDevice.get_all())
        self.assertEqual(settings.target_regions, ['US'])
        self.assertEqual(settings.name, campaign_name)
        self.assertEqual(settings.campaign_manager.id, 2)

        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.CREATE_CAMPAIGN,
            campaign=campaign
        )


class AdGroupSourceSettingsTest(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml', ]

    class MockSettingsWriter(object):
        def __init__(self, init):
            pass

        def set(self, resource, request):
            pass

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')
        self.ad_group = models.AdGroup.objects.get(pk=1)

    def _set_ad_group_end_date(self, days_delta=0):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.end_date = datetime.datetime.utcnow().date() + datetime.timedelta(days=days_delta)
        new_settings.save(None)

    def _set_campaign_landing_mode(self):
        new_campaign_settings = self.ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

    def _set_campaign_automatic_landing_mode(self, automatic_landing_mode):
        current_settings = self.ad_group.campaign.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.automatic_landing_mode = automatic_landing_mode
        request = HttpRequest()
        request.user = User.objects.get(id=1)
        new_settings.save(request)

    def test_end_date_past(self):
        self._set_ad_group_end_date(-1)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_end_date_future(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 200)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_set_state_landing_mode(self):
        self._set_campaign_landing_mode()
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'state': 1})
        )
        self.assertEqual(response.status_code, 400)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_set_cpc_landing_mode(self):
        self._set_campaign_landing_mode()
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 400)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_set_daily_budget_landing_mode(self):
        self._set_campaign_landing_mode()
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '15.00'})
        )
        self.assertEqual(response.status_code, 400)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_logs_user_action(self, mock_log_useraction):
        self._set_ad_group_end_date(days_delta=0)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 200)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_MEDIA_SOURCE_SETTINGS,
            ad_group=self.ad_group)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    @patch('automation.campaign_stop.get_max_settable_daily_budget')
    def test_daily_budget_over_max_settable(self, mock_max_daily_budget):
        mock_max_daily_budget.return_value = decimal.Decimal('500')
        self._set_ad_group_end_date(days_delta=3)
        self._set_campaign_automatic_landing_mode(False)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '600'})
        )
        self.assertEqual(response.status_code, 200)

        self._set_campaign_automatic_landing_mode(True)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '600'})
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '500'})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '400'})
        )
        self.assertEqual(response.status_code, 200)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_source_cpc_over_ad_group_maximum(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '1.10'})
        )
        self.assertEqual(response.status_code, 400)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_source_cpc_equal_ad_group_maximum(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '1.00'})
        )
        self.assertEqual(response.status_code, 200)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    @patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group')
    def test_adgroup_on_budget_autopilot_trigger_budget_autopilot_on_source_state_change(self, mock_budget_ap):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '4', 'source_id': '1'}),
            data=json.dumps({'state': '2'})
        )
        mock_budget_ap.assert_called_with(models.AdGroup.objects.get(id=4), send_mail=False)
        self.assertEqual(response.status_code, 200)

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    @patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group')
    def test_adgroup_not_on_budget_autopilot_not_trigger_budget_autopilot_on_source_state_change(self, mock_budget_ap):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'state': '2'})
        )
        self.assertEqual(mock_budget_ap.called, False)
        self.assertEqual(response.status_code, 200)

    def test_adgroup_w_retargeting_and_source_without(self):
        for source in models.Source.objects.all():
            source.supports_retargeting = False
            source.save()

        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'state': '1'})
        )
        self.assertEqual(response.status_code, 400)


class CampaignAdGroups(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml']

    def setUp(self):
        self.client = Client()
        user = User.objects.get(pk=1)
        self.user = user
        self.client.login(username=user.email, password='secret')

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('actionlog.zwei_actions.send')
    def test_put(self, mock_insert_adgroup, mock_zwei_send):
        campaign = models.Campaign.objects.get(pk=1)

        response = self.client.put(
            reverse('campaign_ad_groups', kwargs={'campaign_id': campaign.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_zwei_send.called)

        response_dict = json.loads(response.content)
        self.assertDictContainsSubset({'name': 'New ad group'}, response_dict['data'])

        ad_group = models.AdGroup.objects.get(pk=response_dict['data']['id'])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
        waiting_sources = actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group)

        self.assertIsNotNone(ad_group_settings.id)
        self.assertIsNotNone(ad_group_settings.changes_text)
        self.assertEqual(len(ad_group_sources), 1)
        self.assertEqual(len(waiting_sources), 1)

        # check if default settings from campaign level are
        # copied to the newly created settings
        self.assertEqual(ad_group_settings.target_devices, ['mobile'])
        self.assertEqual(ad_group_settings.target_regions, ['NC', '501'])

    def test_create_ad_group(self):
        campaign = models.Campaign.objects.get(pk=1)
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User.objects.get(pk=1)
        view = views.CampaignAdGroups()
        ad_group, ad_group_settings, actions = view._create_ad_group(campaign, request)

        self.assertIsNotNone(ad_group)
        self.assertIsNotNone(ad_group_settings)
        self.assertEqual(len(actions), 1)

    def test_create_ad_group_no_add_media_sources_automatically_permission(self):
        campaign = models.Campaign.objects.get(pk=1)
        request = HttpRequest()
        request.user = User.objects.get(pk=2)
        view = views.CampaignAdGroups()
        ad_group, ad_group_settings, actions = view._create_ad_group(campaign, request)

        self.assertIsNotNone(ad_group)
        self.assertIsNotNone(ad_group_settings)
        self.assertEqual(len(actions), 0)

    @patch('actionlog.api.create_campaign')
    def test_add_media_sources(self, mock_create_campaign):
        ad_group = models.AdGroup.objects.get(pk=2)
        ad_group_settings = ad_group.get_current_settings()
        request = None

        view = views.CampaignAdGroups()
        actions = view._add_media_sources(ad_group, ad_group_settings, request)

        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
        waiting_ad_group_sources = actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group)
        added_source = models.Source.objects.get(pk=1)

        self.assertEqual(len(actions), 1)
        self.assertEqual(mock_create_campaign.call_count, 1)
        self.assertFalse(mock_create_campaign.call_args[1]['send'])

        self.assertEqual(len(ad_group_sources), 1)
        self.assertEqual(ad_group_sources[0].source, added_source)
        self.assertEqual(waiting_ad_group_sources, [])

        self.assertEqual(
                ad_group_settings.changes_text,
                'Created settings and automatically created campaigns for 1 sources (AdBlade)'
        )


        ad_group_source_settings = models.AdGroupSourceSettings.objects.all().filter(
            ad_group_source__ad_group=ad_group
        ).group_current_settings()
        self.assertTrue(all(
            [adgss.state == constants.AdGroupSourceSettingsState.ACTIVE for adgss in ad_group_source_settings]
        ))

    @patch('actionlog.api.create_campaign')
    def test_add_media_sources_with_retargeting(self, mock_create_campaign):
        ad_group = models.AdGroup.objects.get(pk=2)

        # remove ability to retarget from all sources
        for source in models.Source.objects.all():
            source.supports_retargeting = False
            source.save()

        request = RequestFactory()
        request.user = self.user

        ad_group_settings = ad_group.get_current_settings()
        ad_group_settings = ad_group_settings.copy_settings()
        ad_group_settings.retargeting_ad_groups = 1
        ad_group_settings.save(request)
        request = None

        ad_group_source_settings = models.AdGroupSourceSettings.objects.all().filter(
            ad_group_source__ad_group=ad_group
        ).group_current_settings()
        self.assertTrue(all(
            [adgss.state == constants.AdGroupSourceSettingsState.INACTIVE for adgss in ad_group_source_settings]
        ))

    @patch('dash.views.helpers.set_ad_group_source_settings')
    def test_create_ad_group_source(self, mock_set_ad_group_source_settings):
        # adblade must not be in maintenance for this particular test
        # so it supports retargeting - which is checked on adgroupsourc creation
        adblade = models.Source.objects.filter(name__icontains='adblade').first()
        adblade.maintenance = False
        adblade.save()

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        source_settings = models.DefaultSourceSettings.objects.get(pk=1)
        request = None
        view = views.CampaignAdGroups()
        ad_group_source = view._create_ad_group_source(request, source_settings, ad_group_settings)

        self.assertIsNotNone(ad_group_source)
        self.assertTrue(mock_set_ad_group_source_settings.called)
        named_call_args = mock_set_ad_group_source_settings.call_args[1]
        self.assertEqual(named_call_args['active'], True)
        self.assertEqual(named_call_args['mobile_only'], True)

    def test_create_new_settings(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        request = None

        view = views.CampaignAdGroups()
        new_settings = view._create_new_settings(ad_group, request)
        campaign_settings = ad_group.campaign.get_current_settings()

        self.assertEqual(new_settings.target_devices, campaign_settings.target_devices)
        self.assertEqual(new_settings.target_regions, campaign_settings.target_regions)


class AdGroupContentAdCSVTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_get_all(self):
        data = {
            'select_all': True
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional),crop areas (optional),tracker url (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",http://testurl.com http://testurl2.com\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description,,\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_all_include_archived(self):
        data = {
            'select_all': True,
            'archived': 'true'
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional),crop areas (optional),tracker url (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",http://testurl.com http://testurl2.com\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description,,\r
http://testurl.com,Test Article with no content_ad_sources 2,123456789.jpg,Example description,,\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_all_ad_selected(self):
        data = {
            'select_all': True,
            'content_ad_ids_not_selected': '1'
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional),crop areas (optional),tracker url (optional)\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description,,\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_batch(self):
        data = {
            'select_batch': 1,
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional),crop areas (optional),tracker url (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",http://testurl.com http://testurl2.com\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description,,\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_batch_ad_selected(self):
        data = {
            'select_batch': 2,
            'content_ad_ids_selected': '1'
        }

        response = self._get_csv_from_server(data)

        expected_lines = ['url,title,image_url,description (optional),crop areas (optional),tracker url (optional)',
                          'http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",http://testurl.com http://testurl2.com',
                          'http://testurl.com,Test Article with no content_ad_sources 4,123456789.jpg,Example description,,',
                          'http://testurl.com,Test Article with no content_ad_sources 3,123456789.jpg,Example description,,']

        lines = response.content.splitlines()

        self.assertEqual(len(lines), len(expected_lines))
        self.assertItemsEqual(lines, expected_lines)

    def test_get_ad_selected(self):
        data = {'content_ad_ids_selected': '1,2'}

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional),crop areas (optional),tracker url (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",http://testurl.com http://testurl2.com\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description,,\r
'''

        self.assertEqual(response.content, expected_content)

    def _get_csv_from_server(self, data):
        return self.client.get(
            reverse(
                'ad_group_content_ad_csv',
                kwargs={'ad_group_id': 1}),
            data=data,
            follow=True
        )

    def test_get_content_ad_ids_validation_error(self):
        response = self._get_csv_from_server({'content_ad_ids_selected': '1,a'})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')


class AdGroupContentAdStateTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_state(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_state',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_post(self, mock_log_useraction):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_id = 1
        content_ad_id = 1

        data = {
            'state': constants.ContentAdSourceState.INACTIVE,
            'content_ad_ids_selected': [content_ad_id],
        }

        response = self._post_content_ad_state(ad_group_id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        content_ad_sources = models.ContentAdSource.objects.filter(content_ad=content_ad)
        self.assertEqual(len(content_ad_sources), 3)

        for content_ad_source in content_ad_sources:
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertJSONEqual(response.content, {
            'success': True
        })

        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CONTENT_AD_STATE,
            ad_group=models.AdGroup.objects.get(pk=1))

    def test_state_set_all(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        content_ads = models.ContentAd.objects.filter(ad_group__id=1)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

        payload = {
            'select_all': True,
            'state': constants.ContentAdSourceState.INACTIVE,
        }

        self._post_content_ad_state(1, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=1)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

    def test_state_set_batch(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        content_ads = models.ContentAd.objects.filter(batch__id=1)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE
                              for ad in content_ads]))

        payload = {
            'select_all': False,
            'select_batch': 1,
            'state': constants.ContentAdSourceState.INACTIVE,
        }

        self._post_content_ad_state(1, payload)

        content_ads = models.ContentAd.objects.filter(batch__id=1)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE
                             for ad in content_ads]))

    def test_dont_set_state_on_archived_ads(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        archived_ad = models.ContentAd.objects.get(pk=3)
        archived_ad.archived = True
        archived_ad.save()
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        restored_ad = models.ContentAd.objects.get(pk=4)
        self.assertFalse(restored_ad.archived)
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        payload = {
            'content_ad_ids_selected': [archived_ad.id, restored_ad.id],
            'state': constants.ContentAdSourceState.ACTIVE,
        }

        self._post_content_ad_state(2, payload)

        archived_ad.refresh_from_db()
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        restored_ad.refresh_from_db()
        self.assertEqual(restored_ad.state, constants.ContentAdSourceState.ACTIVE)

    @patch('dash.views.views.actionlog.zwei_actions.send')
    def test_update_content_ads(self, mock_send):
        content_ad = models.ContentAd.objects.get(pk=1)
        state = constants.ContentAdSourceState.INACTIVE
        request = None

        api.update_content_ads_state([content_ad], state, request)

        content_ad.refresh_from_db()

        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        for content_ad_source in content_ad.contentadsource_set.all():
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertTrue(mock_send.called)

    def test_get_content_ad_ids_validation_error(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')
        response = self._post_content_ad_state(1, {'content_ad_ids_selected': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(settings.changes_text, 'Content ad(s) 1, 2, 3 set to Enabled.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(
            settings.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more set to Enabled.'
        )


class AdGroupArchiveRestoreTest(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml', ]

    class MockSettingsWriter(object):
        def __init__(self, init):
            pass

        def set(self, resource, request):
            pass

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def _post_archive_ad_group(self, ad_group_id):
        return self.client.post(
            reverse(
                'ad_group_archive',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def _post_restore_ad_group(self, ad_group_id):
        return self.client.post(
            reverse(
                'ad_group_restore',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def test_basic_archive_restore(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertFalse(ad_group.is_archived())

        ad_group_settings = ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.state = constants.AdGroupRunningStatus.INACTIVE
        new_ad_group_settings.save(None)

        self._post_archive_ad_group(1)

        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertTrue(ad_group.is_archived())

        self._post_restore_ad_group(1)

        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertFalse(ad_group.is_archived())

    def test_archive_restore_with_pub_blacklisting(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertFalse(ad_group.is_archived())

        ad_group_settings = ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.state = constants.AdGroupRunningStatus.INACTIVE
        new_ad_group_settings.save(None)

        self._post_archive_ad_group(1)

        adiant = models.Source.objects.get(id=2)
        adiant.source_type.available_actions = [
            constants.SourceAction.CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC
        ]
        adiant.source_type.save()

        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            campaign=ad_group.campaign,
            source=adiant,
            status=constants.PublisherStatus.BLACKLISTED
        )
        models.PublisherBlacklist.objects.create(
            name='google.com',
            account=ad_group.campaign.account,
            source=adiant,
            status=constants.PublisherStatus.BLACKLISTED
        )

        # do some blacklisting inbetween
        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertTrue(ad_group.is_archived())

        self._post_restore_ad_group(1)

        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertFalse(ad_group.is_archived())

        pub_blacklist_actions = actionlog.models.ActionLog.objects.filter(
            action='set_publisher_blacklist',
        )
        self.assertEqual(2, pub_blacklist_actions.count())

        first_al_entry = pub_blacklist_actions[0]
        self.assertDictEqual({
            u'key': [1],
            u'level': u'account',
            'publishers': [
                {
                    u'domain': u'google.com',
                    u'exchange': u'adiant',
                    u'source_id': 2,
                    u'ad_group_id': 1,
                }
            ],
            'state': 2
        }, first_al_entry.payload['args'])

        second_al_entry = pub_blacklist_actions[1]
        self.assertDictEqual({
            u'key': [1],
            u'level': u'campaign',
            'publishers': [
                {
                    u'domain': u'zemanta.com',
                    u'exchange': u'adiant',
                    u'source_id': 2,
                    u'ad_group_id': 1,
                }
            ],
            'state': 2
        }, second_al_entry.payload['args'])


class AdGroupContentAdArchive(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_archive(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_archive',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_post(self, mock_send_mail, mock_log_useraction):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ad_id = 2

        data = {
            'content_ad_ids_selected': [content_ad_id],
        }

        response = self._post_content_ad_archive(ad_group.id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], {
            '2': {
                'archived': True,
                'status_setting': 2
            }})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, 'Content ad(s) 2 Archived.')
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.ARCHIVE_RESTORE_CONTENT_AD,
            ad_group=ad_group
        )

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_archive_set_all(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True,
        }

        response = self._post_content_ad_archive(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertTrue(all([ad.archived is True for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': True,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_archive_set_batch(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        batch_id = 2
        content_ads = models.ContentAd.objects.filter(batch__id=batch_id, archived=False)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': False,
            'select_batch': batch_id,
        }

        response = self._post_content_ad_archive(ad_group.id, payload)

        for content_ad in content_ads:
            content_ad.refresh_from_db()

        self.assertTrue(all([ad.archived is True for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': True,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_archive_pause_active_before_archiving(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id, archived=False)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

        active_count = len([ad for ad in content_ads if ad.state == constants.ContentAdSourceState.ACTIVE])
        archived_count = len(content_ads)

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_archive(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE and ad.archived
                             for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['active_count'], active_count)
        self.assertEqual(response_dict['data']['archived_count'], archived_count)

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, 'Content ad(s) 1, 2 Archived.')

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_content_ad_ids_validation_error(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)

        response = self._post_content_ad_archive(ad_group.id, {'content_ad_ids_selected': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

        self.assertFalse(mock_send_mail.called)

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, True, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(settings.changes_text, 'Content ad(s) 1, 2, 3 Archived.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, True, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(
            settings.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more Archived.'
        )


class AdGroupContentAdRestore(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_restore(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_restore',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_post(self, mock_send_mail, mock_log_useraction):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ad_id = 2

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        content_ad.archived = True
        content_ad.save()

        data = {
            'content_ad_ids_selected': [content_ad_id],
        }

        response = self._post_content_ad_restore(ad_group.id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], {'2': {'archived': False, 'status_setting': content_ad.state}})

        mock_send_mail.assert_called_with(
            ad_group, response.wsgi_request, 'Content ad(s) 2 Restored.')
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.ARCHIVE_RESTORE_CONTENT_AD,
            ad_group=ad_group
        )

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_restore_set_all(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        for ad in content_ads:
            ad.archived = True
            ad.save()

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True,
        }

        response = self._post_content_ad_restore(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertTrue(all([ad.archived is False for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': False,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_archive_set_batch(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        batch_id = 2
        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)
        for ad in content_ads:
            ad.archived = True
            ad.save()

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': False,
            'select_batch': batch_id,
        }

        response = self._post_content_ad_restore(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)
        self.assertTrue(all([ad.archived is False for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': False,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_restore_success_when_all_restored(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)

        self.assertGreater(len(content_ads), 0)
        self.assertTrue(all([not ad.archived for ad in content_ads]))

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_restore(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertFalse(all([ad.archived for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertTrue(response_dict['success'])

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_content_ad_ids_validation_error(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)

        response = self._post_content_ad_restore(ad_group.id, {'content_ad_ids_selected': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

        self.assertFalse(mock_send_mail.called)

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, False, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(settings.changes_text, 'Content ad(s) 1, 2, 3 Restored.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, False, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(
            settings.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more Restored.'
        )


class AdGroupAdsPlusUploadTest(TestCase):
    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.views.upload.process_async')
    def test_post(self, mock_process_async, mock_log_useraction):
        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
        )
        ad_group_settings.save(request)

        mock_file = SimpleUploadedFile('testfile.csv', 'Url,title,image_url\nhttp://example.com,testtitle,http://example.com/image')

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'content_ads': mock_file,
                'batch_name': 'testname',
                'display_url': 'test.com',
                'brand_name': 'testbrand',
                'description': 'testdesc',
                'call_to_action': 'testcall',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_process_async.called)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.UPLOAD_CONTENT_ADS,
            ad_group=models.AdGroup.objects.get(pk=1))

    @patch('dash.views.views.upload.process_async')
    def test_post_empty_fields_not_in_csv(self, mock_process_async):
        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
        )
        ad_group_settings.save(request)

        mock_file = SimpleUploadedFile('testfile.csv', 'Url,title,image_url\nhttp://example.com,testtitle,http://example.com/image')

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'content_ads': mock_file,
                'batch_name': 'testname',
                'display_url': '',
                'brand_name': '',
                'description': '',
                'call_to_action': '',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content),
                    {
                        'data': {
                        "message": None,
                        "data": None,
                        "errors": {
                            "display_url": ["This field is required."],
                            "call_to_action": ["This field is required."],
                            "brand_name": ["This field is required."],
                            "description": ["This field is required."],
                            },

                        "error_code": "ValidationError"
                        },
                        "success": False
                    })
        self.assertFalse(mock_process_async.called)

    def test_validation_error(self):
        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}), follow=True)

        self.assertEqual(response.status_code, 400)

    def test_permission(self):
        response = self._get_client(superuser=False).post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}), follow=True)

        self.assertEqual(response.status_code, 403)

    def test_missing_ad_group(self):
        non_existent_ad_group_id = 0

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': non_existent_ad_group_id}),
            follow=True
        )

        self.assertEqual(response.status_code, 404)

    def test_description_too_long(self):
        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'description': 'a'*141
            },
            follow=True
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Description is too long', response.content)

    def test_description_right_length(self):
        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'description': 'a'*140
            },
            follow=True
        )

        self.assertNotIn('Description is too long', response.content)


class AdGroupAdsPlusUploadStatusTest(TestCase):

    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    def _get_status(self):
        response = self._get_client().get(
            reverse('ad_group_ads_plus_upload_status', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        return json.loads(response.content)['data']

    def test_get(self):
        batch = models.UploadBatch.objects.get(pk=2)
        batch.processed_content_ads = 55
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 2,
            'count': 55,
            'batch_size': 100,
        })

        batch.inserted_content_ads = 55
        batch.save()

        # processing ended
        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 3,
            'count': 55,
            'batch_size': 100,
        })

        # inserting ended, but did not yet switched
        batch.inserted_content_ads = batch.batch_size
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 3,
            'count': 100,
            'batch_size': 100,
        })

        batch.propagated_content_ads = 22
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 4,
            'count': 22,
            'batch_size': 100,
        })

    def test_get_cancelled(self):
        batch = models.UploadBatch.objects.get(pk=2)
        batch.processed_content_ads = 55
        batch.status = constants.UploadBatchStatus.CANCELLED
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.CANCELLED,
            'step': 2,
            'count': 55,
            'batch_size': 100,
            'errors': {
                'details': {
                    'description': 'Content Ads upload was cancelled.'
                }
            }
        })

    def test_get_failed(self):
        batch = models.UploadBatch.objects.get(pk=2)
        batch.processed_content_ads = 55
        batch.status = constants.UploadBatchStatus.FAILED
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.FAILED,
            'step': 2,
            'count': 55,
            'batch_size': 100,
            'errors': {
                'details': {
                    'description': 'An error occured while processing file.'
                }
            }
        })

    def test_get_failed_csv_errors(self):
        batch = models.UploadBatch.objects.get(pk=2)
        batch.processed_content_ads = 55
        batch.status = constants.UploadBatchStatus.FAILED
        batch.error_report_key = 123
        batch.num_errors = 12
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.FAILED,
            'step': 2,
            'count': 55,
            'batch_size': 100,
            'errors': {
                'details': {
                    'report_url': '/api/ad_groups/1/contentads_plus/upload/2/report/',
                    'description': 'Found 12 errors.'
                }
            }
        })

    def test_permission(self):
        response = self._get_client(superuser=False).get(
            reverse('ad_group_ads_plus_upload_status', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        self.assertEqual(response.status_code, 403)


class AdGroupAdsPlusUploadCancelTest(TestCase):

    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    def _get_status(self):
        response = self._get_client().get(
            reverse('ad_group_ads_plus_upload_status', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        return json.loads(response.content)['data']

    def test_get(self):
        batch = models.UploadBatch.objects.get(pk=2)
        self.assertFalse(batch.cancelled)
        response = self._get_client(superuser=True).get(
            reverse('ad_group_ads_plus_upload_cancel', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        response_dict = json.loads(response.content)
        self.assertDictEqual(response_dict, {'success': True})

        batch.refresh_from_db()
        self.assertEqual(batch.status, constants.UploadBatchStatus.CANCELLED)

    def test_permission(self):
        response = self._get_client(superuser=False).get(
            reverse('ad_group_ads_plus_upload_cancel', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        self.assertEqual(response.status_code, 403)

    def test_validation(self):
        batch = models.UploadBatch.objects.get(pk=2)
        batch.propagated_content_ads = batch.batch_size
        batch.save()

        response = self._get_client(superuser=True).get(
            reverse('ad_group_ads_plus_upload_cancel', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        self.assertEqual(response.status_code, 400)

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['errors']['cancel'], 'Cancel action unsupported at this stage')


class AdGroupSourcesTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def test_get_name(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'Account š name that is toooooooo long',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'Campaign š name that is toooooooo long',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'Ad group š name that is toooooooo long',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Account š name that is / Campaign š name that / Ad group š name that / 123 / Outbrain')

    def test_get_name_long_first_word(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'Accountšnamethatistoooooooolong',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'Campaignšnamethatistoooooooolong',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'Adgroupšnamethatistoooooooolong',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Accountšnamethatistooo / Campaignšnamethatistoo / Adgroupšnamethatistooo / 123 / Outbrain')

    def test_get_name_empty_strings(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()

        self.assertEqual(
            name, u'ONE:  /  /  / 123 / Outbrain')

    def test_get_dma_targeting_compatible(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_source = models.AdGroupSource.objects.get(id=3)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC
        ]
        ad_group_source.source.source_type.save()

        response = self.client.get(
            reverse(
                'ad_group_sources',
                kwargs={'ad_group_id': 2}),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertItemsEqual(response_dict['data']['sources'], [
            {'id': 2, 'name': 'Gravity', 'can_target_existing_regions': False, 'can_retarget': True},  # should return False when DMAs used
            {'id': 3, 'name': 'Outbrain', 'can_target_existing_regions': True, 'can_retarget': True},
            {'id': 9, 'name': 'Sharethrough', 'can_target_existing_regions': False, 'can_retarget': True},
        ])

    def test_available_sources(self):
        response = self.client.get(
                reverse('ad_group_sources', kwargs={'ad_group_id': 1}),
                follow=True
        )
        # Expected sources - 9 (Sharethrough)
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict['data']['sources']), 1)
        self.assertEqual(response_dict['data']['sources'][0]['id'], 9)

    def test_available_sources_with_filter(self):
        response = self.client.get(
                reverse('ad_group_sources', kwargs={'ad_group_id': 1}),
                {'filtered_sources': '7,8,9'},
                follow=True
        )
        # Expected sources - 9 (Sharethrough)
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict['data']['sources']), 1)
        self.assertEqual(response_dict['data']['sources'][0]['id'], 9)

    def test_available_sources_with_filter_empty(self):
        response = self.client.get(
            reverse('ad_group_sources', kwargs={'ad_group_id': 1}),
            {'filtered_sources': '7,8'},
            follow=True
        )
        # Expected sources - none
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict['data']['sources']), 0)

    def test_put(self):
        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '9'})
        )
        self.assertEqual(response.status_code, 200)

        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        waiting_sources = (ad_group_source.source for ad_group_source
                           in actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group))
        self.assertIn(source, ad_group_sources)
        self.assertIn(source, waiting_sources)

    def test_put_with_retargeting(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        request = RequestFactory()
        request.user = User(id=1)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.retargeting_ad_groups = [2]
        new_settings.save(request)

        source = models.Source.objects.get(pk=9)
        source.supports_retargeting = False
        source.save()

        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '9'})
        )
        self.assertEqual(response.status_code, 400)

        ad_group_sources = ad_group.sources.all()
        waiting_sources = (ad_group_source.source for ad_group_source
                           in actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group))
        self.assertNotIn(source, ad_group_sources)
        self.assertNotIn(source, waiting_sources)

    def test_put_existing_source(self):
        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '1'})
        )
        self.assertEqual(response.status_code, 400)


@patch('dash.views.views.actionlog.api_contentads.init_update_content_ad_action')
class SharethroughApprovalTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()

    def test_approved_creative(self, mock_update):
        data = {
            'status': 0,
            'crid': 1,
            'seat': 'abc123',
            'expiry': '2015-12-31'
        }
        cas = models.ContentAdSource.objects.get(content_ad_id=1, source=models.Source.objects.get(name='Sharethrough'))
        self.assertEqual(1, cas.submission_status)

        self.client.post(
            reverse('sharethrough_approval'),
            follow=True,
            content_type='application/json',
            data=json.dumps(data)
        )

        cas = models.ContentAdSource.objects.get(id=cas.id)

        self.assertEqual(2, cas.submission_status)
        self.assertEqual(None, cas.submission_errors)
        self.assertTrue(mock_update.called)
        mock_update.assert_called_with(cas, {'state': cas.state}, request=None, send=True)

    def test_rejected_creative(self, mock_update):
        data = {
            'status': 1,
            'crid': 1,
            'seat': 'abc123',
            'expiry': '2015-12-31'
        }
        cas = models.ContentAdSource.objects.get(content_ad_id=1, source=models.Source.objects.get(name='Sharethrough'))
        self.assertEqual(1, cas.submission_status)

        self.client.post(
            reverse('sharethrough_approval'),
            follow=True,
            content_type='application/json',
            data=json.dumps(data)
        )

        cas = models.ContentAdSource.objects.get(id=cas.id)

        self.assertEqual(3, cas.submission_status)
        self.assertEqual(None, cas.submission_errors)
        self.assertTrue(mock_update.called)
        mock_update.assert_called_with(cas, {'state': cas.state}, request=None, send=True)


class PublishersBlacklistStatusTest(TransactionTestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()
        redshift.STATS_DB_NAME = 'default'
        for s in models.SourceType.objects.all():
            if s.available_actions is None:
                s.available_actions = []
            s.available_actions.append(constants.SourceAction.CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC)
            s.save()

    def _post_publisher_blacklist(self, ad_group_id, data, user_id=3, with_status=False):
        user = User.objects.get(pk=user_id)
        self.client.login(username=user.username, password='secret')
        reversed_url = reverse(
            'ad_group_publishers_blacklist',
            kwargs={'ad_group_id': ad_group_id})
        response = self.client.post(
            reversed_url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )
        if not with_status:
            return json.loads(response.content)
        else:
            json_blob = None
            try:
                json_blob = json.loads(response.content)
            except:
                json_blob = {'text': response.content}
            return json_blob, response.status_code

    def _fake_payload_data(self, level):
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        return {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": level,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": []
        }

    def _fake_cursor_data(self, cursor):
        cursor().dictfetchall.return_value = [{
            'domain': u'zemanta.com',
            'ctr': 0.0,
            'exchange': 'adiant',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]

    @patch('reports.redshift.get_cursor')
    def test_post_blacklist_permission_none(self, cursor):
        for level in (constants.PublisherBlacklistLevel.get_all()):
            payload = self._fake_payload_data(level)
            res, status = self._post_publisher_blacklist(1, payload, user_id=2, with_status=True)
            self.assertFalse(res.get('success'), 'No permissions for blacklisting')

    @patch('reports.redshift.get_cursor')
    def test_post_blacklist_permission_adgroup(self, cursor):
        self._fake_cursor_data(cursor)
        accessible_levels = (constants.PublisherBlacklistLevel.ADGROUP,)

        permission = Permission.objects.get(codename='can_modify_publisher_blacklist_status')
        user = zemauth.models.User.objects.get(pk=2)
        user.user_permissions.add(permission)
        user.save()

        for level in constants.PublisherBlacklistLevel.get_all():
            payload = self._fake_payload_data(level)
            res, status = self._post_publisher_blacklist(1, payload, user_id=2, with_status=True)
            if level in accessible_levels:
                self.assertTrue(res.get('success'), 'level {} should be accessible'.format(level))
            else:
                self.assertFalse(res.get('success'), 'level {} should be inaccessible'.format(level))

    @patch('reports.redshift.get_cursor')
    def test_post_blacklist_permission_campaign_account(self, cursor):
        self._fake_cursor_data(cursor)
        accessible_levels = (
            constants.PublisherBlacklistLevel.ADGROUP,
            constants.PublisherBlacklistLevel.CAMPAIGN,
            constants.PublisherBlacklistLevel.ACCOUNT,
        )

        permissions = Permission.objects.filter(
            codename__in=(
                'can_modify_publisher_blacklist_status',
                'can_access_campaign_account_publisher_blacklist_status',
            )
        )
        user = zemauth.models.User.objects.get(pk=2)
        for permission in permissions:
            user.user_permissions.add(permission)
        user.save()

        for level in constants.PublisherBlacklistLevel.get_all():
            payload = self._fake_payload_data(level)
            res, status = self._post_publisher_blacklist(1, payload, user_id=2, with_status=True)
            if level in accessible_levels:
                self.assertTrue(res.get('success'), 'level {} should be accessible'.format(level))
            else:
                self.assertFalse(res.get('success'), 'level {} should be inaccessible'.format(level))

    @patch('reports.redshift.get_cursor')
    def test_post_blacklist_permission_global(self, cursor):
        self._fake_cursor_data(cursor)
        accessible_levels = (
            constants.PublisherBlacklistLevel.ADGROUP,
            constants.PublisherBlacklistLevel.CAMPAIGN,
            constants.PublisherBlacklistLevel.ACCOUNT,
            constants.PublisherBlacklistLevel.GLOBAL,
        )

        permissions = Permission.objects.filter(
            codename__in=(
                'can_modify_publisher_blacklist_status',
                'can_access_campaign_account_publisher_blacklist_status',
                'can_access_global_publisher_blacklist_status',
            )
        )
        user = zemauth.models.User.objects.get(pk=2)
        for permission in permissions:
            user.user_permissions.add(permission)
        user.save()

        for level in constants.PublisherBlacklistLevel.get_all():
            payload = self._fake_payload_data(level)
            res, status = self._post_publisher_blacklist(1, payload, user_id=2, with_status=True)
            if level in accessible_levels:
                self.assertTrue(res.get('success'), 'level {} should be accessible'.format(level))
            else:
                self.assertFalse(res.get('success'), 'level {} should be inaccessible'.format(level))

    @patch('reports.redshift.get_cursor')
    def test_post_blacklist(self, cursor):
        cursor().dictfetchall.return_value = [
        {
            'domain': u'掌上留园－6park',  # an actual domain from production
            'ctr': 0.0,
            'exchange': 'adiant',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.ADGROUP,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": []
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(1, publisher_blacklist_action.count())
        self.assertDictEqual(
            {
                u"key": [1],
                u"state": 2,
                u"level": u"adgroup",
                u"publishers": [{
                    u"exchange": u"adiant",
                    u"source_id": 7,
                    u"domain": u"掌上留园－6park",
                    u"ad_group_id": 1
                    }]
            }, publisher_blacklist_action.first().payload['args'])
        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())
        publisher_blacklist = models.PublisherBlacklist.objects.first()
        self.assertEqual(constants.PublisherStatus.PENDING, publisher_blacklist.status)
        self.assertEqual(1, publisher_blacklist.ad_group.id)
        self.assertEqual('b1_adiant', publisher_blacklist.source.tracking_slug)
        self.assertEqual(u'掌上留园－6park', publisher_blacklist.name)

    @patch('reports.redshift.get_cursor')
    def test_post_enable(self, cursor):

        # blacklist must first exist in order to be deleted
        models.PublisherBlacklist.objects.create(
            name="zemanta.com",
            ad_group=models.AdGroup.objects.get(pk=1),
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED
        )

        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]

        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.ENABLED,
            "level": constants.PublisherBlacklistLevel.ADGROUP,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected":[],
            "publishers_not_selected":[]
        }
        res = self._post_publisher_blacklist('1', payload)
        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(1, publisher_blacklist_action.count())
        self.assertDictEqual(
            {
                u"key": [1],
                u"state": 1,
                u"level": u"adgroup",
                u"publishers": [{
                    u"exchange": u"adiant",
                    u"source_id": 7,
                    u"domain": u"zemanta.com",
                    u"ad_group_id": 1
                    }]
            }, publisher_blacklist_action.first().payload['args'])

        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())

        publisher_blacklist = models.PublisherBlacklist.objects.first()
        self.assertEqual(constants.PublisherStatus.PENDING, publisher_blacklist.status)
        self.assertEqual(1, publisher_blacklist.ad_group.id)
        self.assertEqual('b1_adiant', publisher_blacklist.source.tracking_slug)
        self.assertEqual('zemanta.com', publisher_blacklist.name)

    @patch('reports.redshift.get_cursor')
    def test_post_global_blacklist(self, cursor):
        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.GLOBAL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": []
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(1, publisher_blacklist_action.count())
        self.assertDictEqual(
            {
                u"key": None,
                u"state": 2,
                u"level": u"global",
                u"publishers": [{
                    u"domain": u"zemanta.com",
                }]
            }, publisher_blacklist_action.first().payload['args'])
        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())
        publisher_blacklist = models.PublisherBlacklist.objects.first()

        self.assertTrue(publisher_blacklist.everywhere)
        self.assertEqual(constants.PublisherStatus.PENDING, publisher_blacklist.status)
        self.assertIsNone(publisher_blacklist.ad_group)
        self.assertEqual('b1_adiant', publisher_blacklist.source.tracking_slug)
        self.assertEqual('zemanta.com', publisher_blacklist.name)

    @patch('reports.redshift.get_cursor')
    def test_post_global_blacklist_1(self, cursor):
        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.GLOBAL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": False,
            "publishers_selected": [
                {
                    "blacklisted": "Active",
                    "checked": True,
                    "domain": "zemanta.com",
                    "source_id": 7
                }
            ],
            "publishers_not_selected": []
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )

        self.assertEqual(1, publisher_blacklist_action.count())
        self.assertDictEqual(
            {
                u"key": None,
                u"state": 2,
                u"level": u"global",
                u"publishers": [{
                    u"domain": u"zemanta.com",
                }]
            }, publisher_blacklist_action.first().payload['args'])
        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())
        publisher_blacklist = models.PublisherBlacklist.objects.first()

        self.assertTrue(publisher_blacklist.everywhere)
        self.assertEqual(constants.PublisherStatus.PENDING, publisher_blacklist.status)
        self.assertIsNone(publisher_blacklist.ad_group)
        self.assertEqual('b1_adiant', publisher_blacklist.source.tracking_slug)
        self.assertEqual('zemanta.com', publisher_blacklist.name)

    @patch('reports.redshift.get_cursor')
    def test_post_global_all_but_blacklist_1(self, cursor):
        # simulate select all
        # unselect the only publisher
        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.GLOBAL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": [
                {
                    "blacklisted": "Active",
                    "checked": True,
                    "domain": "zemanta.com",
                    "source_id": 7
                }
            ]
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(0, publisher_blacklist_action.count())
        self.assertTrue(res['success'])
        self.assertEqual(0, models.PublisherBlacklist.objects.count())

    @patch('reports.redshift.get_cursor')
    def test_post_global_all_but_blacklist_2(self, cursor):
        # simulate select all
        # publisher is already blacklisted
        # (essentialy blacklisting blacklisted pub)

        models.PublisherBlacklist.objects.create(
            name="zemanta.com",
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED,
            everywhere=True
        )

        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.GLOBAL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": [],
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(0, publisher_blacklist_action.count())
        self.assertTrue(res['success'])
        self.assertEqual(1, models.PublisherBlacklist.objects.count())


    @patch('reports.redshift.get_cursor')
    def test_post_global_all_but_enable_1(self, cursor):
        models.PublisherBlacklist.objects.create(
            name="zemanta.com",
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED,
            everywhere=True
        )

        # simulate select all
        # unselect the only publisher
        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.ENABLED,
            "level": constants.PublisherBlacklistLevel.GLOBAL,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": [
                {
                    "blacklisted": "Enabled",
                    "checked": True,
                    "domain": "zemanta.com",
                    "source_id": 7
                }
            ]
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(0, publisher_blacklist_action.count())
        self.assertTrue(res['success'])
        self.assertEqual(1, models.PublisherBlacklist.objects.count())

    @patch('reports.redshift.get_cursor')
    def test_post_campaign_blacklist(self, cursor):

        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]

        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.CAMPAIGN,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected":[],
            "publishers_not_selected":[]
        }
        res = self._post_publisher_blacklist('1', payload)
        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(1, publisher_blacklist_action.count())
        self.assertDictEqual(
            {
                u"key": [1],
                u"state": 2,
                u"level": u"campaign",
                u"publishers": [{
                        u"exchange": u"adiant",
                        u"source_id": 7,
                        u"domain": u"zemanta.com",
                        u"ad_group_id": 1
                    },
                    {
                        u'ad_group_id': 9,
                        u'domain': u'zemanta.com',
                        u'exchange': u'adiant',
                        u'source_id': 7
                    }
                ]
            }, publisher_blacklist_action.first().payload['args'])

        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())

        publisher_blacklist = models.PublisherBlacklist.objects.first()
        self.assertEqual(constants.PublisherStatus.PENDING, publisher_blacklist.status)
        self.assertIsNone(publisher_blacklist.ad_group)
        self.assertEqual(1, publisher_blacklist.campaign.id)
        self.assertEqual('b1_adiant', publisher_blacklist.source.tracking_slug)
        self.assertEqual('zemanta.com', publisher_blacklist.name)


        adg1 = models.AdGroup.objects.get(pk=1)
        settings1 = adg1.get_current_settings()

        self.assertEqual(
            'Blacklisted the following publishers on campaign level: zemanta.com on Adiant.',
            settings1.changes_text
        )

        adg9 = models.AdGroup.objects.get(pk=9)
        settings9 = adg9.get_current_settings()

        self.assertEqual(
            'Blacklisted the following publishers on campaign level: zemanta.com on Adiant.',
            settings9.changes_text
        )

        useractionlogs = models.UserActionLog.objects.filter(
            action_type=constants.UserActionType.SET_CAMPAIGN_PUBLISHER_BLACKLIST
        )
        self.assertEqual(2, useractionlogs.count())
        for useractionlog in useractionlogs:
            self.assertTrue(useractionlog.ad_group.id in (1, 9))


    @patch('reports.redshift.get_cursor')
    def test_post_campaign_all_but_blacklist_1(self, cursor):
        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]

        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.CAMPAIGN,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected":[],
            "publishers_not_selected":[{
                "blacklisted": "Enabled",
                "checked": True,
                "domain": "zemanta.com",
                "source_id": 7
            }]
        }
        res = self._post_publisher_blacklist('1', payload)
        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(0, publisher_blacklist_action.count())
        self.assertTrue(res['success'])

        self.assertEqual(0, models.PublisherBlacklist.objects.count())

    @patch('reports.redshift.get_cursor')
    def test_post_campaign_all_but_blacklist_2(self, cursor):
        models.PublisherBlacklist.objects.create(
            name="zemanta.com",
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED,
            campaign=models.Campaign.objects.get(pk=1)
        )

        cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'exchange': 'adiant',
        },
        ]

        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.CAMPAIGN,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected":[],
            "publishers_not_selected":[]
        }
        res = self._post_publisher_blacklist('1', payload)
        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(0, publisher_blacklist_action.count())
        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())

    @patch('reports.redshift.get_cursor')
    def test_post_outbrain_account_blacklist(self, cursor):
        cursor().dictfetchall.return_value = [
        {
            'domain': u'Test',
            'ctr': 0.0,
            'exchange': 'outbrain',
            'external_id': 'sfdafkl1230899012asldas',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.ACCOUNT,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": []
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(1, publisher_blacklist_action.count())
        self.assertDictEqual(
            {
                u"key": [1, ''],
                u"state": 2,
                u"level": u"account",
                u"publishers": [{
                    u"exchange": u"outbrain",
                    u"source_id": 3,
                    u"domain": u"Test",
                    u"ad_group_id": 1,
                    u"external_id": u"sfdafkl1230899012asldas"
                    }]
            }, publisher_blacklist_action.first().payload['args'])
        self.assertTrue(res['success'])

        self.assertEqual(1, models.PublisherBlacklist.objects.count())
        publisher_blacklist = models.PublisherBlacklist.objects.first()
        self.assertEqual(constants.PublisherStatus.PENDING, publisher_blacklist.status)
        self.assertEqual(1, publisher_blacklist.account.id)
        self.assertEqual('outbrain', publisher_blacklist.source.tracking_slug)
        self.assertEqual(u'Test', publisher_blacklist.name)

    @patch('reports.redshift.get_cursor')
    def test_post_outbrain_invalid_level_blacklist(self, cursor):
        cursor().dictfetchall.return_value = [
        {
            'domain': u'Test',
            'ctr': 0.0,
            'exchange': 'outbrain',
            'external_id': 'sfdafkl1230899012asldas',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)

        for level in (constants.PublisherBlacklistLevel.ADGROUP,
                      constants.PublisherBlacklistLevel.CAMPAIGN,
                      constants.PublisherBlacklistLevel.GLOBAL):
            payload = {
                "state": constants.PublisherStatus.BLACKLISTED,
                "level": level,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "select_all": True,
                "publishers_selected": [],
                "publishers_not_selected": []
            }
            res = self._post_publisher_blacklist(1, payload)
            self.assertTrue(res['success'])

            publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
                action_type=actionlog.constants.ActionType.AUTOMATIC,
                action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
            )
            self.assertEqual(0, publisher_blacklist_action.count())

    @patch('reports.redshift.get_cursor')
    def test_post_outbrain_over_quota(self, cursor):
        for i in xrange(10):
            models.PublisherBlacklist.objects.create(
                account=models.Account.objects.get(pk=1),
                source=models.Source.objects.get(tracking_slug=constants.SourceType.OUTBRAIN),
                name='test_{}'.format(i),
                status=constants.PublisherStatus.BLACKLISTED,
            )

        cursor().dictfetchall.return_value = [
        {
            'domain': u'Test',
            'ctr': 0.0,
            'exchange': 'outbrain',
            'external_id': 'sfdafkl1230899012asldas',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=31)
        payload = {
            "state": constants.PublisherStatus.BLACKLISTED,
            "level": constants.PublisherBlacklistLevel.ACCOUNT,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "select_all": True,
            "publishers_selected": [],
            "publishers_not_selected": []
        }
        res = self._post_publisher_blacklist(1, payload)

        publisher_blacklist_action = actionlog.models.ActionLog.objects.filter(
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST
        )
        self.assertEqual(0, publisher_blacklist_action.count())
        self.assertTrue(res['success'])

        self.assertEqual(10, models.PublisherBlacklist.objects.count())


class AdGroupOverviewTest(TestCase):
    fixtures = ['test_api.yaml', 'users']

    def setUp(self):
        self.client = Client()
        self.user = zemauth.models.User.objects.get(email='chuck.norris@zemanta.com')
        redshift.STATS_DB_NAME = 'default'

    def setUpPermissions(self):
        permissions = [
            'can_see_infobox',
            'can_access_ad_group_infobox'
        ]
        for p in permissions:
            self.user.user_permissions.add(Permission.objects.get(codename=p))
        self.user.save()
        campaign = models.Campaign.objects.get(pk=1)
        campaign.users.add(self.user)

    def _get_ad_group_overview(self, ad_group_id, with_status=False):
        self.client.login(username=self.user.username, password='norris')
        reversed_url = reverse(
                'ad_group_overview',
                kwargs={'ad_group_id': ad_group_id})

        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        ret = [s for s in settings if name in s['name'].lower()]
        if ret != []:
            return ret[0]
        else:
            return None

    def test_user_access_1(self):
        response = self._get_ad_group_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

        permission = Permission.objects.get(codename='can_see_infobox')
        self.user.user_permissions.add(permission)
        self.user.save()

        response = self._get_ad_group_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

    def test_user_access_2(self):
        response = self._get_ad_group_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

        permission_2 = Permission.objects.get(codename='can_access_ad_group_infobox')
        self.user.user_permissions.add(permission_2)
        self.user.save()

        response = self._get_ad_group_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

    @patch('reports.redshift.get_cursor')
    def test_run_empty(self, cursor):
        self.setUpPermissions()
        cursor().dictfetchall.return_value = [{
            'adgroup_id': 1,
            'source_id': 9,
            'cost_cc_sum': 0.0
        }]

        ad_group = models.AdGroup.objects.get(pk=1)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        credit = models.CreditLineItem.objects.create(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        models.BudgetLineItem.objects.create(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        response = self._get_ad_group_overview(1)

        self.assertTrue(response['success'])
        header = response['data']['header']
        self.assertEqual(header['title'], u'AdGroup name')
        self.assertEqual(constants.InfoboxStatus.INACTIVE, header['active'])

        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']
        flight_setting = self._get_setting(settings, 'flight')
        self.assertEqual('03/02 - 04/02', flight_setting['value'])

        flight_setting = self._get_setting(settings, 'daily')
        self.assertEqual('$50.00', flight_setting['value'])

        device_setting = self._get_setting(settings, 'targeting')
        self.assertEqual('Device: Desktop, Mobile', device_setting['value'])

        region_setting = [s for s in settings if 'location' in s['value'].lower()][0]
        self.assertEqual('Location:', region_setting['value'])
        self.assertEqual('UK, US, CA', region_setting['details_content'])

        tracking_setting = self._get_setting(settings, 'tracking')
        self.assertEqual(tracking_setting['value'], 'Yes')
        self.assertEqual(tracking_setting['details_content'], 'param1=foo&param2=bar')

        yesterday_spend = self._get_setting(settings, 'yesterday')
        self.assertEqual('$0.00', yesterday_spend['value'])

        budget_setting = self._get_setting(settings, 'daily budget')
        self.assertEqual('$50.00', budget_setting['value'])

        budget_setting = self._get_setting(settings, 'campaign budget')
        self.assertEqual('$80.00', budget_setting['value'])
        self.assertEqual('$80.00 remaining', budget_setting['description'])

        pacing_setting = self._get_setting(settings, 'pacing')
        self.assertEqual('$0.00', pacing_setting['value'])
        self.assertEqual('0.00% on plan', pacing_setting['description'])
        self.assertEqual('sad', pacing_setting['icon'])

        retargeting_setting = self._get_setting(settings, 'retargeting')
        self.assertIsNone(retargeting_setting, 'no permission')

        goal_setting = [s for s in settings if 'goal' in s['name'].lower()]
        self.assertEqual([], goal_setting)

        # try aqgain with retargeting permission
        permission = Permission.objects.get(codename='can_view_retargeting_settings')
        self.user.user_permissions.add(permission)
        self.user.save()

        response = self._get_ad_group_overview(1)
        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']
        retargeting_setting = self._get_setting(settings, 'retargeting')
        self.assertEqual('test adgroup 3', retargeting_setting['details_content'])

    @patch('reports.redshift.get_cursor')
    @patch('reports.api_contentads.get_actual_yesterday_cost')
    def test_run_mid(self, mock_cost, cursor):
        self.setUpPermissions()
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        # check values for adgroup that is in the middle of flight time
        # and is overperforming
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.start_date = start_date
        new_ad_group_settings.end_date = end_date
        new_ad_group_settings.save(None)

        credit = models.CreditLineItem.objects.create(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        budget = models.BudgetLineItem.objects.create(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        reports.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=datetime.datetime.today() - datetime.timedelta(days=1),
            media_spend_nano=60 * 10**9,
            data_spend_nano=0,
            license_fee_nano=0
        )

        cursor().diftfetchall.return_value = {
            1: {
                'cost_cc_sum': 500000.0,
            }
        }

        mock_cost.return_value = {
            1: 60.0
        }

        response = self._get_ad_group_overview(1)

        self.assertTrue(response['success'])
        header = response['data']['header']
        self.assertEqual(header['title'], u'AdGroup name')
        self.assertEqual(constants.InfoboxStatus.INACTIVE, header['active'])

        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        flight_setting = self._get_setting(settings, 'flight')
        self.assertEqual('{sm}/{sd} - {em}/{ed}'.format(
            sm="{:02d}".format(start_date.month),
            sd="{:02d}".format(start_date.day),
            em="{:02d}".format(end_date.month),
            ed="{:02d}".format(end_date.day),
        ), flight_setting['value'])

        flight_setting = self._get_setting(settings, 'daily')
        self.assertEqual('$50.00', flight_setting['value'])
        yesterday_setting = self._get_setting(settings, 'yesterday')
        self.assertEqual('$60.00', yesterday_setting['value'])
        self.assertEqual('120.00% of daily budget', yesterday_setting['description'])


class CampaignOverviewTest(TestCase):
    fixtures = ['test_api', 'users']

    def setUp(self):
        self.client = Client()
        self.user = zemauth.models.User.objects.get(email='chuck.norris@zemanta.com')
        redshift.STATS_DB_NAME = 'default'

    def setUpPermissions(self):
        permissions = [
            'can_see_infobox',
            'can_access_campaign_infobox'
        ]
        for p in permissions:
            self.user.user_permissions.add(Permission.objects.get(codename=p))
        self.user.save()
        campaign = models.Campaign.objects.get(pk=1)
        campaign.users.add(self.user)

    def _get_campaign_overview(self, campaign_id, user_id=2, with_status=False):
        self.client.login(username=self.user.username, password='norris')
        reversed_url = reverse(
                'campaign_overview',
                kwargs={'campaign_id': campaign_id})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        return [s for s in settings if name in s['name'].lower()][0]

    def test_user_access_1(self):
        response = self._get_campaign_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

        permission = Permission.objects.get(codename='can_see_infobox')
        self.user.user_permissions.add(permission)
        self.user.save()

        response = self._get_campaign_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

    def test_user_access_2(self):
        response = self._get_campaign_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

        permission_2 = Permission.objects.get(codename='can_access_campaign_infobox')
        self.user.user_permissions.add(permission_2)
        self.user.save()

        response = self._get_campaign_overview(1)
        self.assertFalse(response['success'])
        self.assertEqual('AuthorizationError', response['data']['error_code'])

    @patch('reports.redshift.get_cursor')
    def test_run_empty(self, cursor):
        req = RequestFactory().get('/')
        req.user = self.user

        adg_start_date = datetime.datetime.now() - datetime.timedelta(days=1)
        adg_end_date = datetime.datetime.now() + datetime.timedelta(days=1)

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = adg_start_date
            new_adgs.end_date = adg_end_date
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)

        self.setUpPermissions()
        cursor().dictfetchall.return_value = [{
            'adgroup_id': 1,
            'source_id': 9,
            'cost_cc_sum': 0.0
        }]

        campaign = models.Campaign.objects.get(pk=1)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        credit = models.CreditLineItem.objects.create(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        models.BudgetLineItem.objects.create(
            campaign=campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        response = self._get_campaign_overview(1)
        self.assertTrue(response['success'])

        header = response['data']['header']
        self.assertEqual(u'test campaign 1 \u010c\u017e\u0161', header['title'])
        self.assertEqual(constants.InfoboxStatus.ACTIVE, header['active'])

        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        active_adgroup_settings = self._get_setting(settings, 'active ad groups')
        self.assertEqual('1', active_adgroup_settings['value'])

        flight_setting = self._get_setting(settings, 'flight')
        self.assertEqual('{sm:02d}/{sd:02d} - {em:02d}/{ed:02d}'.format(
            sm=adg_start_date.month,
            sd=adg_start_date.day,
            em=adg_end_date.month,
            ed=adg_end_date.day,

        ), flight_setting['value'])

        device_setting = self._get_setting(settings, 'targeting')
        self.assertEqual('Device: Mobile, Desktop', device_setting['value'])

        location_setting = [s for s in settings if 'location' in s['value'].lower()][0]
        self.assertEqual('Location: US', location_setting['value'])

        budget_setting = self._get_setting(settings, 'daily budget')
        self.assertEqual('$50.00', budget_setting['value'])

        budget_setting = self._get_setting(settings, 'campaign budget')
        self.assertEqual('$80.00', budget_setting['value'])
        self.assertEqual('$80.00 remaining', budget_setting['description'])

        pacing_setting = self._get_setting(settings, 'pacing')
        self.assertEqual('$0.00', pacing_setting['value'])
        self.assertEqual('0.00% on plan', pacing_setting['description'])
        self.assertEqual('sad', pacing_setting['icon'])

        goal_setting = [s for s in settings if 'goal' in s['name'].lower()]
        self.assertEqual([], goal_setting)


class AccountOverviewTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()
        redshift.STATS_DB_NAME = 'default'

        permission = Permission.objects.get(codename='can_see_infobox')
        permission_2 = Permission.objects.get(codename='can_access_account_infobox')
        permission_3 = Permission.objects.get(codename='view_archived_entities')
        user = zemauth.models.User.objects.get(pk=2)
        user.user_permissions.add(permission)
        user.user_permissions.add(permission_2)
        user.user_permissions.add(permission_3)
        user.save()
        self.user = user

    def _get_account_overview(self, account_id, user_id=2, with_status=False):
        user = User.objects.get(pk=user_id)
        self.client.login(username=user.username, password='secret')
        reversed_url = reverse(
                'account_overview',
                kwargs={'account_id': account_id})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        return [s for s in settings if name in s['name'].lower()][0]

    @patch('reports.redshift.get_cursor')
    @patch('dash.models.Account.get_current_settings')
    def test_run_empty(self, mock_current_settings, cursor):
        req = RequestFactory().get('/')
        req.user = self.user

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            new_adgs.end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)

        settings = models.AccountSettings(
            default_account_manager=zemauth.models.User.objects.get(pk=1),
            default_sales_representative=zemauth.models.User.objects.get(pk=2),
        )

        mock_current_settings.return_value = settings

        # do some extra setup to the account
        cursor().dictfetchall.return_value = [{
            'adgroup_id': 1,
            'source_id': 9,
            'cost_cc_sum': 0.0
        }]
        response = self._get_account_overview(1)
        settings = response['data']['basic_settings']

        count_setting = self._get_setting(settings, 'active campaigns')
        # 1 campaign has no adroupsourcesettings
        self.assertEqual('1', count_setting['value'])
        self.assertTrue(response['success'])

    @patch('reports.redshift.get_cursor')
    @patch('dash.models.Account.get_current_settings')
    def test_run_empty_non_archived(self, mock_current_settings, cursor):
        req = RequestFactory().get('/')
        req.user = self.user

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            new_adgs.end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)
        settings = models.AccountSettings(
            default_account_manager=zemauth.models.User.objects.get(pk=1),
            default_sales_representative=zemauth.models.User.objects.get(pk=2),
        )

        mock_current_settings.return_value = settings

        campaign_settings = models.Campaign.objects.get(pk=1).get_current_settings()
        new_campaign_settings = campaign_settings.copy_settings()
        new_campaign_settings.archived = True
        new_campaign_settings.save(req)

        adgroup_settings = models.AdGroup.objects.get(pk=1).get_current_settings()
        new_adgroup_settings = adgroup_settings.copy_settings()
        new_adgroup_settings.archived = True
        new_adgroup_settings.save(req)

        # do some extra setup to the account
        cursor().dictfetchall.return_value = [{
            'adgroup_id': 1,
            'source_id': 9,
            'cost_cc_sum': 0.0
        }]
        response = self._get_account_overview(1)
        settings = response['data']['basic_settings']

        count_setting = self._get_setting(settings, 'active campaigns')
        # 1 campaign has no adroupsourcesettings
        self.assertEqual('1', count_setting['value'])
        self.assertTrue(response['success'])


class AllAccountsOverviewTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()
        redshift.STATS_DB_NAME = 'default'

        permission = Permission.objects.get(codename='can_see_infobox')
        permission_2 = Permission.objects.get(codename='can_access_all_accounts_infobox')
        user = zemauth.models.User.objects.get(pk=2)
        user.user_permissions.add(permission)
        user.user_permissions.add(permission_2)
        user.save()

    def _get_all_accounts_overview(self, campaign_id, user_id=2, with_status=False):
        user = User.objects.get(pk=user_id)
        self.client.login(username=user.username, password='secret')
        reversed_url = reverse(
            'all_accounts_overview',
            kwargs={})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def test_run_empty(self):
        response = self._get_all_accounts_overview(1)
        self.assertTrue(response['success'])
