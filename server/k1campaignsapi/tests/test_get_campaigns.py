import itertools
import json
from mock import patch

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse

import dash.constants
import dash.models


class K1CampaignsApiTest(TestCase):

    fixtures = ['test_k1_campaigns_api.yaml']

    def _test_ad_group_source_filter(self, mock_verify_wsgi_request, source_types=None):
        response = self.client.get(
            reverse('k1campaignsapi.get_ad_group_sources'),
            {'source_type': source_types},
        )
        self.assertEqual(response.status_code, 200)
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)

        returned_count = 0
        for source_credentials in data['source_credentials']:
            for account in source_credentials['accounts']:
                self.assertEqual(account['outbrain_marketer_id'],
                                 dash.models.Account.objects.get(pk=account['id']).outbrain_marketer_id)
                for campaign in account['campaigns']:
                    for ad_group in campaign['ad_groups']:
                        for ad_group_source in ad_group['ad_group_sources']:
                            returned_count += 1
                            db_ags = dash.models.AdGroupSource.objects.get(
                                id=ad_group_source['id'])
                            self.assertEqual(source_credentials[
                                             'credentials'], db_ags.source_credentials.credentials)
                            self.assertEqual(source_credentials[
                                             'source_type'], db_ags.source_credentials.source.source_type.type)
                            self.assertEqual(account['id'], db_ags.ad_group.campaign.account_id)
                            self.assertEqual(campaign['id'], db_ags.ad_group.campaign_id)
                            self.assertEqual(ad_group['id'], db_ags.ad_group_id)
                            self.assertEqual(ad_group_source['id'], db_ags.id)
                            self.assertEqual(ad_group_source['source_name'], db_ags.source.name)
                            self.assertEqual(json.loads(
                                ad_group_source['source_campaign_key']), db_ags.source_campaign_key)

        ad_group_sources = dash.models.AdGroupSource.objects
        if source_types:
            ad_group_sources = ad_group_sources.filter(
                source__source_type__type__in=source_types)
        self.assertEqual(returned_count, ad_group_sources.count())

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_ad_group_sources(self, mock_verify_wsgi_request):
        test_cases = [
            [],
            ['b1'],
            ['b1', 'outbrain', 'yahoo'],
        ]
        for source_types in test_cases:
            self._test_ad_group_source_filter(mock_verify_wsgi_request, source_types)

    def _test_content_ads_filters(self, mock_verify_wsgi_request, source_types=None, ad_groups=None):
        response = self.client.get(
            reverse('k1campaignsapi.get_content_ad_sources'),
            {'source_type': source_types, 'ad_group': ad_groups},
        )
        self.assertEqual(response.status_code, 200)
        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')

        data = json.loads(response.content)

        returned_count = 0
        for content_ad_source in data['content_ad_sources']:
            returned_count += 1
            db_cas = dash.models.ContentAdSource.objects.get(
                id=content_ad_source['id'])
            self.assertEqual(content_ad_source['source_content_ad_id'], db_cas.source_content_ad_id)
            self.assertEqual(content_ad_source['content_ad_id'], db_cas.content_ad_id)
            self.assertEqual(content_ad_source['ad_group_id'], db_cas.content_ad.ad_group_id)
            self.assertEqual(content_ad_source['source_id'], db_cas.source_id)
            self.assertEqual(content_ad_source['source_name'], db_cas.source.name)

        contentadsources = dash.models.ContentAdSource.objects
        if ad_groups:
            contentadsources = contentadsources.filter(
                content_ad__ad_group_id__in=ad_groups)
        if source_types:
            contentadsources = contentadsources.filter(
                source__source_type__type__in=source_types)
        self.assertEqual(returned_count, contentadsources.count(), data)

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(K1_API_SIGN_KEY='test_api_key')
    def test_get_content_ads(self, mock_verify_wsgi_request):
        test_source_filters = [
            [],
            ['b1'],
            ['b1', 'outbrain', 'yahoo'],
        ]
        test_ad_group_filters = [
            [],
            ['1'],
            ['2'],
            ['1', '2'],
        ]
        test_cases = itertools.product(test_source_filters, test_ad_group_filters)
        for source_types, ad_groups in test_cases:
            self._test_content_ads_filters(mock_verify_wsgi_request, source_types, ad_groups)
