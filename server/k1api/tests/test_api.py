import itertools
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

    def test_no_signature(self):
        response = self.client.get(
            reverse('k1api.get_accounts'),
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse('k1api.get_source_credentials_for_reports_sync'),
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse('k1api.get_content_ad_source_mapping'),
        )
        self.assertEqual(response.status_code, 404)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_accounts(self, mock_verify_wsgi_request):
        response = self.client.get(
            reverse('k1api.get_accounts'),
        )
        self.assertEqual(response.status_code, 200)
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)

        for account in data['accounts']:
            self.assertEqual(account['outbrain_marketer_id'],
                             dash.models.Account.objects.get(pk=account['id']).outbrain_marketer_id)

    def _test_source_credentials_filter(self, mock_verify_wsgi_request, source_types=None):
        response = self.client.get(
            reverse('k1api.get_source_credentials_for_reports_sync'),
            {'source_type': source_types},
        )
        self.assertEqual(response.status_code, 200)
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)

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
        self.assertEqual(response.status_code, 200)
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)

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
            self._test_content_ad_source_ids_filters(mock_verify_wsgi_request, source_types, source_content_ad_ids)
