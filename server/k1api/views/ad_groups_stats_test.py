import json
import datetime

from mock import patch

from django.core.urlresolvers import reverse

import dash.features.geolocation
import dash.features.ga
import dash.constants
import dash.models

import logging

from redshiftapi import api_quickstats

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AdGroupsTest(K1APIBaseTest):

    @patch.object(api_quickstats, 'query_adgroup', autospec=True)
    def test_get_ad_group_stats(self, mock_quickstats):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        mock_stats = {
            'total_cost': '123.0',
            'impressions': 123,
            'clicks': 12,
            'cpc': '0.15',
        }
        mock_quickstats.return_value = mock_stats

        response = self.client.get(
            reverse('k1api.ad_groups.stats'),
            {'ad_group_id': 1, 'source_slug': 'yahoo'}
        )

        from_date = ad_group.created_dt.date()
        to_date = datetime.date.today() + datetime.timedelta(days=1)
        mock_quickstats.assert_called_with(1, from_date, to_date, 5)

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(data, mock_stats)

    def test_get_ad_group_stats_false_source(self):
        response = self.client.get(
            reverse('k1api.ad_groups.stats'),
            {'ad_group_id': 1, 'source_slug': 'doesnotexist'}
        )

        self.assertEqual(response.status_code, 400)
