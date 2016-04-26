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
            'k1api.get_source_credentials_for_reports_sync',
            'k1api.get_content_ad_source_mapping',
            'k1api.get_ga_accounts',
            'k1api.get_publishers_blacklist',
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

        for account in data['response']['accounts']:
            self.assertEqual(account['outbrain_marketer_id'],
                             dash.models.Account.objects.get(pk=account['id']).outbrain_marketer_id)

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
            source__source_type__type='adblade', source_credentials_id=1).values(u'ad_group_id', u'source_campaign_key')
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
        }

        db_ags = dash.models.AdGroupSource.objects.get(
            source__source_type__type='adblade', ad_group_id=1)
        self.assertEqual(data['ad_group_id'], db_ags.ad_group_id)
        self.assertEqual(data['ad_group_source_id'], db_ags.id)
        self.assertEqual(data['source_campaign_key'], db_ags.source_campaign_key)
        self.assertLessEqual(required_fields, set(data.keys()))

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
    def test_get_publishers_blacklist(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_publishers_blacklist'),
        )
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data['blacklist']), 3)

        sorted_blacklist = sorted(data['blacklist'], key=lambda b: (b['ad_group_id'], b['status']))
        self.assertDictEqual(sorted_blacklist[0], {
            'ad_group_id': 1,
            'domain': 'pub1.com',
            'exchange': 'adblade',
            'status': 1,
        })
        self.assertDictEqual(sorted_blacklist[1], {
            'ad_group_id': 1,
            'domain': 'pub2.com',
            'exchange': 'gravity',
            'status': 2,
        })
        self.assertDictEqual(sorted_blacklist[2], {
            'ad_group_id': 2,
            'domain': 'pub3.com',
            'exchange': 'gravity',
            'status': 1,
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

        self.assertEqual(len(data['blacklist']), 2)

        sorted_blacklist = sorted(data['blacklist'], key=lambda b: b['domain'])
        self.assertDictEqual(sorted_blacklist[0], {
            'ad_group_id': 1,
            'domain': 'pub1.com',
            'exchange': 'adblade',
            'status': 1,
        })
        self.assertDictEqual(sorted_blacklist[1], {
            'ad_group_id': 1,
            'domain': 'pub2.com',
            'exchange': 'gravity',
            'status': 2,
        })
