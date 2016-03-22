import datetime
import json
import mock

from mock import patch
from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest

import dash.constants
import dash.models


class K1CampaignsApiTest(TestCase):

    fixtures = ['test_k1_campaigns_api.yaml']


    def _test_ad_group_source_filter(self, source_types=None):
        response = self.client.get(
            reverse('k1campaignsapi.get_ad_groups'),
            {'source_type': source_types},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        returned_count = 0
        for account in data['accounts']:
            for campaign in account['campaigns']:
                for ad_group in campaign['ad_groups']:
                    for adgroupsource in ad_group['adgroupsources']:
                        returned_count += 1
                        db_ags = dash.models.AdGroupSource.objects.get(
                            id=adgroupsource['id'])
                        self.assertEqual(account['id'], db_ags.ad_group.campaign.account_id)
                        self.assertEqual(campaign['id'], db_ags.ad_group.campaign_id)
                        self.assertEqual(ad_group['id'], db_ags.ad_group_id)
                        self.assertEqual(adgroupsource['id'], db_ags.id)
                        self.assertEqual(adgroupsource['source_name'], db_ags.source.name)
                        self.assertEqual(adgroupsource['source_type'], db_ags.source.source_type.type)
                        self.assertEqual(adgroupsource['source_credentials'], db_ags.source_credentials.credentials)
                        self.assertEqual(json.loads(adgroupsource['source_campaign_key']), db_ags.source_campaign_key)

        adgroupsources = dash.models.AdGroupSource.objects
        if source_types:
            adgroupsources = adgroupsources.filter(
                source__source_type__type__in=source_types)
        self.assertEqual(returned_count, adgroupsources.count())

    def test_get_ad_groups(self):
        test_cases = [
            [],
            ['b1'],
            ['b1', 'outbrain', 'yahoo'],
        ]
        for source_types in test_cases:
            self._test_ad_group_source_filter(source_types)


    def _test_content_ads_filters(source_types, ad_groups):
        response = self.client.get(
            reverse('k1campaignsapi.get_ad_groups'),
            {'source_type': source_types},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)


    def test_get_content_ads(self):
        test_cases = [
            ([], []),
            (['b1'], []),
            (['b1', 'outbrain', 'yahoo'], []),
        ]
        for source_types, ad_groups in test_cases:
            self._test_content_ads_filters(source_types, ad_groups)
