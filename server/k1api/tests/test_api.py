import itertools
import time
import json
from mock import patch
import urllib

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse

import dash.constants
import dash.models

import logging

from utils.test_helper import ListMatcher

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class K1ApiTest(TestCase):

    fixtures = ['test_k1_api.yaml']

    def _test_signature(self, path):
        response = self.client.get(
            reverse(path),
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.get(
            reverse(path),
            TS_HEADER=str(int(time.time())),
            SIGNATURE_HEADER='abc'
        )
        self.assertEqual(response.status_code, 404)

    def test_signature(self):
        test_paths = [
            'k1api.get_accounts',
            'k1api.get_custom_audiences',
            'k1api.update_source_pixel',
            'k1api.get_source_credentials_for_reports_sync',
            'k1api.get_content_ad_source_mapping',
            'k1api.get_ga_accounts',
            'k1api.get_publishers_blacklist',
            'k1api.get_ad_groups',
            'k1api.get_ad_groups_exchanges',
            'k1api.get_facebook_accounts',
            'k1api.update_facebook_account',
        ]
        for path in test_paths:
            self._test_signature(path)

    def _assert_response_ok(self, response, data):
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', data)
        self.assertEqual(data['error'], None)
        self.assertIn('response', data)
        self.assertNotEqual(data['response'], None)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_accounts(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_accounts'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertTrue(len(data['accounts']), 3)
        self.assertDictEqual(data, {u'accounts': ListMatcher([
            {u'id': 1,
             u'outbrain_marketer_id': u'abcde',
             u'pixels': [
                 {u'id': 1,
                  u'slug': u'testslug1',
                  u'source_pixels': ListMatcher([
                      {u'url': u'http://www.ob.com/pixelendpoint',
                       u'source_pixel_id': u'ob_zem1',
                       u'source_type': u'outbrain',
                       },
                      {u'url': u'http://www.y.com/pixelendpoint',
                       u'source_pixel_id': u'y_zem1',
                       u'source_type': u'yahoo',
                       },
                      {u'url': u'http://www.fb.com/pixelendpoint',
                       u'source_pixel_id': u'fb_zem1',
                       u'source_type': u'facebook',
                       },
                  ])},
                 {u'id': 2,
                  u'slug': u'testslug2',
                  u'source_pixels': ListMatcher([
                      {u'url': u'http://www.ob.com/pixelendpoint',
                       u'source_pixel_id': u'ob_zem2',
                       u'source_type': u'outbrain',
                       },
                      {u'url': u'http://www.y.com/pixelendpoint',
                       u'source_pixel_id': u'y_zem2',
                       u'source_type': u'yahoo',
                       },
                      {u'url': u'http://www.fb.com/pixelendpoint',
                       u'source_pixel_id': u'fb_zem2',
                       u'source_type': u'facebook',
                       },
                  ])},
             ]},
            {u'id': 2,
             u'outbrain_marketer_id': None,
             u'pixels': [
                 {u'id': 3,
                  u'slug': u'testslug3',
                  u'source_pixels': []
                  },
             ]},
            {u'id': 3,
             u'outbrain_marketer_id': None,
             u'pixels': [],
             },
        ])})
        self.assertIsNone(data.get('credentials'))

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_accounts_with_id(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_accounts'), {'account_id': 1, 'bidder_slug': 'outbrain'},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertTrue(len(data['accounts']), 1)
        self.assertDictEqual(data['accounts'][0], {
            u'id': 1,
            u'outbrain_marketer_id': u'abcde',
            u'pixels': [
                {u'id': 1,
                 u'slug': u'testslug1',
                 u'source_pixels': ListMatcher([
                     {u'url': u'http://www.ob.com/pixelendpoint',
                      u'source_pixel_id': u'ob_zem1',
                      u'source_type': u'outbrain',
                      },
                     {u'url': u'http://www.y.com/pixelendpoint',
                      u'source_pixel_id': u'y_zem1',
                      u'source_type': u'yahoo',
                      },
                     {u'url': u'http://www.fb.com/pixelendpoint',
                      u'source_pixel_id': u'fb_zem1',
                      u'source_type': u'facebook',
                      },
                 ])},
                {u'id': 2,
                 u'slug': u'testslug2',
                 u'source_pixels': ListMatcher([
                     {u'url': u'http://www.ob.com/pixelendpoint',
                      u'source_pixel_id': u'ob_zem2',
                      u'source_type': u'outbrain',
                      },
                     {u'url': u'http://www.y.com/pixelendpoint',
                      u'source_pixel_id': u'y_zem2',
                      u'source_type': u'yahoo',
                      },
                     {u'url': u'http://www.fb.com/pixelendpoint',
                      u'source_pixel_id': u'fb_zem2',
                      u'source_type': u'facebook',
                      },
                 ])},
            ]})
        self.assertEqual(data['credentials'], u'c')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_custom_audience(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_custom_audiences'),
            {'account_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(2, len(data))
        self.assertDictEqual(data[0], {
            u'id': 1,
            u'pixel_id': 1,
            u'rules': ListMatcher([
                {u'id': 1,
                 u'type': 1,
                 u'values': u'dummy',
                 },
                {u'id': 2,
                 u'type': 2,
                 u'values': u'dummy2',
                 },
            ]),
            u'ttl': 90,
        })
        self.assertDictEqual(data[1], {
            u'id': 2,
            u'pixel_id': 2,
            u'rules': ListMatcher([
                {u'id': 3,
                 u'type': 1,
                 u'values': u'dummy3',
                 },
                {u'id': 4,
                 u'type': 2,
                 u'values': u'dummy4',
                 },
            ]),
            u'ttl': 60,
        })

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_custom_audience_no_id(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_custom_audiences'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Account id must be specified.')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_source_pixel_with_existing(self, mock_verify_wsgi_request):
        body = {
            'pixel_id': 1,
            'source_type': 'facebook',
            'url': 'http://www.dummy_fb.com/pixie_endpoint',
            'source_pixel_id': 'fb_dummy_id',
        }
        response = self.client.put(
            reverse('k1api.update_source_pixel'), json.dumps(body), 'application/json',
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self.assertDictEqual(body, data['response'])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=3)
        self.assertEqual(updated_pixel.url, 'http://www.dummy_fb.com/pixie_endpoint')
        self.assertEqual(updated_pixel.source_pixel_id, 'fb_dummy_id')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_source_pixel_create_new(self, mock_verify_wsgi_request):
        body = {
            'pixel_id': 3,
            'source_type': 'facebook',
            'url': 'http://www.dummy_fb.com/pixie_endpoint',
            'source_pixel_id': 'fb_dummy_id',
        }
        response = self.client.put(
            reverse('k1api.update_source_pixel'), json.dumps(body), 'application/json',
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self.assertDictEqual(body, data['response'])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=7)
        self.assertEqual(updated_pixel.url, 'http://www.dummy_fb.com/pixie_endpoint')
        self.assertEqual(updated_pixel.source_pixel_id, 'fb_dummy_id')

    def _test_source_credentials_filter(self, mock_verify_wsgi_request, source_types=None):
        response = self.client.get(
            reverse('k1api.get_source_credentials_for_reports_sync'),
            {'source_type': source_types},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        for source_credentials in data['source_credentials_list']:
            sc = dash.models.SourceCredentials.objects.get(pk=source_credentials['id'])
            self.assertEqual(sc.credentials, source_credentials['credentials'])
            self.assertEqual(sc.source.source_type.type, source_credentials['source_type'])

        scs = dash.models.SourceCredentials.objects.filter(sync_reports=True)
        if source_types:
            scs = scs.filter(source__source_type__type__in=source_types)
        self.assertEqual(len(data['source_credentials_list']), scs.count())

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_source_credentials(self, mock_verify_wsgi_request):
        test_cases = [
            ['b1'],
            ['b1', 'outbrain', 'yahoo'],
        ]
        for source_types in test_cases:
            self._test_source_credentials_filter(mock_verify_wsgi_request, source_types)

    def _test_content_ad_source_ids_filters(self, mock_verify_wsgi_request, source_types=None,
                                            source_content_ad_ids=None):
        query_params = urllib.urlencode({'source_type': source_types})
        response = self.client.generic(
            'GET',
            reverse('k1api.get_content_ad_source_mapping'),
            data=json.dumps(source_content_ad_ids),
            QUERY_STRING=query_params
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        for content_ad_source in data['content_ad_sources']:
            db_cas = dash.models.ContentAdSource.objects.get(
                id=content_ad_source['id'])
            self.assertEqual(content_ad_source['source_content_ad_id'], db_cas.source_content_ad_id)
            self.assertEqual(content_ad_source['content_ad_id'], db_cas.content_ad_id)
            self.assertEqual(content_ad_source['ad_group_id'], db_cas.content_ad.ad_group_id)
            self.assertEqual(content_ad_source['source_id'], db_cas.source_id)
            self.assertEqual(content_ad_source['source_name'], db_cas.source.name)
            self.assertEqual(content_ad_source['slug'], db_cas.source.bidder_slug)

        contentadsources = dash.models.ContentAdSource.objects
        if source_content_ad_ids:
            contentadsources = contentadsources.filter(
                source_content_ad_id__in=source_content_ad_ids)
        if source_types:
            contentadsources = contentadsources.filter(
                source__source_type__type__in=source_types)
        logger.error('abc')
        self.assertEqual(len(data['content_ad_sources']), contentadsources.count())

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_content_ad_source_mapping(self, mock_verify_wsgi_request):
        test_source_filters = [
            ['b1'],
            ['b1', 'outbrain', 'yahoo'],
        ]
        test_source_content_ads = [
            ['987654321'],
            ['987654321', '123456789'],
        ]
        test_cases = itertools.product(test_source_filters, test_source_content_ads)
        for source_types, source_content_ad_ids in test_cases:
            self._test_content_ad_source_ids_filters(
                mock_verify_wsgi_request, source_types, source_content_ad_ids)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ga_accounts(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ga_accounts'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data['ga_accounts']), 2)
        self.assertEqual(data['ga_accounts'][0]['account_id'], 1)
        self.assertEqual(data['ga_accounts'][1]['account_id'], 1)
        self.assertEqual(data['ga_accounts'][0]['ga_account_id'], 'acc1')
        self.assertEqual(data['ga_accounts'][1]['ga_account_id'], 'acc2')
        self.assertEqual(data['ga_accounts'][0]['ga_web_property_id'], 'prop1')
        self.assertEqual(data['ga_accounts'][1]['ga_web_property_id'], 'prop2')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_group_source_ids(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_group_source_ids'),
            {'source_type': 'adblade',
             'credentials_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        expected = dash.models.AdGroupSource.objects.filter(
            source__source_type__type='adblade', source_credentials_id=1)
        expected = [{u'ad_group_id': e.ad_group_id, u'source_campaign_key': e.source_campaign_key} for e in expected]
        self.assertEqual(data, list(expected))

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_group_source(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_group_source'),
            {'source_type': 'adblade',
             'ad_group_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        required_fields = {
            u'ad_group_source_id',
            u'ad_group_id',
            u'credentials',
            u'source_campaign_key',
            u'state',
            u'cpc_cc',
            u'daily_budget_cc',
            u'name',
            u'start_date',
            u'end_date',
            u'target_devices',
            u'target_regions',
            u'tracking_code',
            u'tracking_slug',
        }

        db_ags = dash.models.AdGroupSource.objects.get(
            source__source_type__type='adblade', ad_group_id=1)
        self.assertEqual(data['ad_group_id'], db_ags.ad_group_id)
        self.assertEqual(data['ad_group_source_id'], db_ags.id)
        self.assertEqual(data['source_campaign_key'], db_ags.source_campaign_key)
        self.assertLessEqual(required_fields, set(data.keys()))

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_group_source_nonexisting(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_group_source'),
            {'source_type': 'nonexistingsource',
             'ad_group_id': 1},
        )
        self.assertEqual(response.status_code, 404)

    def _test_get_content_ad_sources_for_ad_group(self, mock_verify_wsgi_request, ad_group_id, content_ad_id):
        response = self.client.get(
            reverse('k1api.get_content_ad_sources_for_ad_group'),
            {'source_type': 'adblade',
             'ad_group_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        required_fields = {
            u'content_ad_source_id',
            u'credentials',
            u'source_campaign_key',
            u'ad_group_id',
            u'content_ad_id',
            u'source_content_ad_id',
            u'state',
            u'title',
            u'url',
            u'submission_status',
            u'image_id',
            u'image_width',
            u'image_height',
            u'image_hash',
            u'image_crop',
            u'redirect_id',
            u'display_url',
            u'brand_name',
            u'description',
            u'call_to_action',
            u'tracking_slug',
            u'tracker_urls',
        }

        db_ags = dash.models.ContentAdSource.objects.filter(content_ad__ad_group_id=ad_group_id)
        if content_ad_id:
            db_ags = db_ags.filter(content_ad_id=content_ad_id)

        for cas in data:
            self.assertLessEqual(required_fields, set(cas.keys()))

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_content_ad_sources_for_ad_group(self, mock_verify_wsgi_request):
        test_cases = [
            (1, None),
            (1, 1),
        ]
        for ad_group_id, content_ad_id in test_cases:
            self._test_get_content_ad_sources_for_ad_group(mock_verify_wsgi_request, ad_group_id, content_ad_id)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_content_ad_sources_for_ad_group_no_adgroupsource(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_content_ad_sources_for_ad_group'),
            {'source_type': 'outbrain',
             'ad_group_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']
        self.assertEqual(data, [])

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_sources_by_tracking_slug(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_sources_by_tracking_slug')
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertGreater(len(data), 0)
        for source in data.values():
            self.assertIn('id', source)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_accounts_slugs_ad_groups(self, mock_verify_wsgi_request):
        accounts = (1, 2)
        response = self.client.get(
            reverse('k1api.get_accounts_slugs_ad_groups'),
            {'account': accounts},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        for account_id, account_data in data.items():
            self.assertIn(int(account_id), accounts)

            self.assertIn('ad_groups', account_data)
            self.assertIn('slugs', account_data)

            self.assertGreater(len(account_data['ad_groups']), 0)
            for ad_group in account_data['ad_groups'].values():
                self.assertIn('campaign_id', ad_group)

            self.assertGreater(len(account_data['slugs']), 0)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_publishers_blacklist_outbrain(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_publishers_blacklist_outbrain'),
            {'marketer_id': 'abcde'}
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        expected = (
            dash.models.PublisherBlacklist.objects
                .filter(account__outbrain_marketer_id='abcde')
                .filter(source__source_type__type='outbrain')
                .filter(external_id__isnull=False)
                .values(u'name', u'external_id')
        )
        self.assertEqual(data, {u'blacklist': list(expected)})

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_publishers_blacklist(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_publishers_blacklist'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data['blacklist']), 10)

        sorted_blacklist = sorted(data['blacklist'], key=lambda b: (b['ad_group_id'], b['status'], b['domain']))
        self.assertDictEqual(sorted_blacklist[0], {
            'ad_group_id': None,
            'domain': 'global',
            'exchange': None,
            'status': 1,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[1], {
            'ad_group_id': 1,
            'domain': 'pub1.com',
            'exchange': 'adiant',
            'status': 1,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[2], {
            'ad_group_id': 1,
            'domain': 'pub2.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[3], {
            'ad_group_id': 1,
            'domain': 'pub5.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[4], {
            'ad_group_id': 1,
            'domain': 'pub6.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[5], {
            'ad_group_id': 1,
            'domain': 'pub7.com',
            'exchange': 'facebook',
            'status': 2,
            'external_id': 'outbrain-pub-id',
        })
        self.assertDictEqual(sorted_blacklist[6], {
            'ad_group_id': 2,
            'domain': 'pub3.com',
            'exchange': 'google',
            'status': 1,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[7], {
            'ad_group_id': 2,
            'domain': 'pub5.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[8], {
            'ad_group_id': 2,
            'domain': 'pub6.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_publishers_blacklist_with_ad_group_id(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_publishers_blacklist'),
            {'ad_group_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data['blacklist']), 5)

        sorted_blacklist = sorted(data['blacklist'], key=lambda b: b['domain'])
        self.assertDictEqual(sorted_blacklist[0], {
            'ad_group_id': 1,
            'domain': 'pub1.com',
            'exchange': 'adiant',
            'status': 1,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[1], {
            'ad_group_id': 1,
            'domain': 'pub2.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[2], {
            'ad_group_id': 1,
            'domain': 'pub5.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })
        self.assertDictEqual(sorted_blacklist[3], {
            'ad_group_id': 1,
            'domain': 'pub6.com',
            'exchange': 'google',
            'status': 2,
            'external_id': '',
        })

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_groups_with_id(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_groups'),
            {'ad_group_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)

        self.assertDictEqual(data[0], {
            u'id': 1,
            u'name': u'ONE: test account 1 / test campaign 1 / test adgroup 1 / 1',
            u'start_date': u'2014-06-04',
            u'end_date': None,
            u'time_zone': u'America/New_York',
            u'brand_name': u'brand1',
            u'display_url': u'brand1.com',
            u'tracking_codes': u'tracking1&tracking2',
            u'device_targeting': [],
            u'iab_category': u'IAB24',
            u'target_regions': [],
            u'retargeting': [{u'event_id': u'1', u'event_type': u'aud', u'exclusion': False},
                             {u'event_id': u'2', u'event_type': u'aud', u'exclusion': False}],
            u'campaign_id': 1,
            u'account_id': 1,
            u'goal_types': [2, 5],
        })

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_groups(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_groups'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 3)

        required_fields = {
            u'id',
            u'name',
            u'start_date',
            u'end_date',
            u'time_zone',
            u'brand_name',
            u'display_url',
            u'tracking_codes',
            u'device_targeting',
            u'iab_category',
            u'target_regions',
            u'retargeting',
            u'campaign_id',
            u'account_id',
            u'goal_types',
        }

        for item in data:
            self.assertEqual(required_fields, set(item.keys()))

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_groups_exchanges(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_groups_exchanges'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 2)
        self.assertEqual(len(data['1']), 1)
        self.assertEqual(len(data['2']), 2)

        self.assertDictEqual(data['1'][0], {
            u'exchange': 'b1_adiant',
            u'status': 1,
            u'cpc_cc': '0.1200',
            u'daily_budget_cc': '1.5000',
        })

        sorted_exchanges = sorted(data['2'], key=lambda b: b['exchange'])
        self.assertDictEqual(sorted_exchanges[0], {
            u'exchange': u'b1_facebook',
            u'status': 1,
            u'cpc_cc': u'0.1400',
            u'daily_budget_cc': u'1.7000',
        })
        self.assertDictEqual(sorted_exchanges[1], {
            u'exchange': u'b1_google',
            u'status': 1,
            u'cpc_cc': u'0.1300',
            u'daily_budget_cc': u'1.6000',
        })

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_groups_exchanges_with_id(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_ad_groups_exchanges'),
            {'ad_group_id': 1},
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)

        self.assertDictEqual(data['1'][0], {
            u'exchange': 'b1_adiant',
            u'status': 1,
            u'cpc_cc': '0.1200',
            u'daily_budget_cc': '1.5000',
        })

    def test_get_content_ads(self):
        # TODO matijav 03.05.2016
        pass

    def test_get_content_ads_exchanges(self):
        # TODO matijav 03.05.2016
        pass

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_content_ad_status(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.update_content_ad_status'),
            json.dumps({'content_ad_id': 1, 'source_slug': 'adblade',
                        'submission_status': 2, 'submission_errors': 'my-errors',
                        'source_content_ad_id': 123}),
            'application/json',
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        cas = dash.models.ContentAdSource.objects.filter(content_ad_id=1, source__bidder_slug='adblade')[0]
        self.assertEqual(cas.submission_status, 2)
        self.assertEqual(cas.submission_errors, 'my-errors')
        self.assertEqual(cas.source_content_ad_id, '123')

        response = self.client.put(
            reverse('k1api.update_content_ad_status'),
            json.dumps({'content_ad_id': 1000, 'source_slug': 'adblade',
                        'submission_status': 2, 'submission_errors': 'my-errors',
                        'source_content_ad_id': 123}),
            'application/json',
        )
        self.assertEqual(response.status_code, 404)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_set_source_campaign_key(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.set_source_campaign_key'),
            json.dumps({'ad_group_source_id': 1, 'source_campaign_key': ['abc']}),
            'application/json',
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        ags = dash.models.AdGroupSource.objects.get(pk=1)
        # self.assertEqual(1, 2)
        self.assertEqual(ags.source_campaign_key, ['abc'])

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_outbrain_marketer_id(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_outbrain_marketer_id'),
            {'ad_group_id': '1'}
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        ag = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(ag.campaign.account.outbrain_marketer_id, data['response'])

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_outbrain_marketer_id_assign_new(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_outbrain_marketer_id'),
            {'ad_group_id': '3'}
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        ag = dash.models.AdGroup.objects.get(pk=3)
        self.assertEqual(ag.campaign.account.outbrain_marketer_id, data['response'])

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_facebook_accounts(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_facebook_accounts'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        data = data['response']
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {
            u'account_id': 1,
            u'ad_account_id': u'act_123',
            u'page_id': u'1234',
        })
        self.assertDictEqual(data[1], {
            u'account_id': 2,
            u'ad_account_id': u'act_456',
            u'page_id': u'5678',
        })

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_facebook_accounts_with_ad_group(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_facebook_accounts'),
            {'ad_group_id': '1'}
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        fb_account = dash.models.FacebookAccount.objects.get(pk=1)
        self.assertEqual(fb_account.ad_account_id, data['response']['ad_account_id'])

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_facebook_accounts_with_account(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_facebook_accounts'),
            {'account_id': '1'}
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        fb_account = dash.models.FacebookAccount.objects.get(pk=1)
        self.assertEqual(fb_account.ad_account_id, data['response']['ad_account_id'])

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_ad_group_source_state(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.update_ad_group_source_state'),
            json.dumps({'ad_group_id': 1,
                        'bidder_slug': 'adblade',
                        'conf': {'state': 2}}),
            'application/json'
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        a = dash.models.AdGroupSource.objects.get(ad_group__id=1,
                                                  source__bidder_slug='adblade')

        self.assertEqual(a.get_current_settings().state, 2)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_ad_group_source_state_no_ad_group(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.update_ad_group_source_state'),
            json.dumps({'ad_group_id': 12345,
                        'bidder_slug': 'adblade',
                        'conf': {'state': 2}}),
            'application/json'
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'No AdGroupSource exists for ad_group_id: 12345 with bidder_slug adblade')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_ad_group_source_state_incorrect_body(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.update_ad_group_source_state'),
            json.dumps({'conf': {'state': 2}}),
            'application/json'
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Must provide ad_group_id, bidder_slug and conf')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_facebook_account(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.update_facebook_account'),
            json.dumps({'status': 5, 'ad_account_id': 'act_555', 'account_id': 1}),
            'application/json'
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        fb_account = dash.models.FacebookAccount.objects.get(account__id=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fb_account.status, 5)
        self.assertEqual(fb_account.ad_account_id, 'act_555')

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_update_facebook_account_error(self, mock_verify_wsgi_request):
        response = self.client.put(
            reverse('k1api.update_facebook_account'),
            json.dumps({'status': 5, 'ad_account_id': 'act_555'}),
            'application/json'
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'account id must be specified')
        self.assertEqual(response.status_code, 400)
