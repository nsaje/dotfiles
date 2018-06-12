import json

from mock import patch

from django.core.urlresolvers import reverse

import dash.features.geolocation
import dash.features.ga
import dash.constants
import dash.models

import logging

from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AdGroupsTest(K1APIBaseTest):

    def test_get_ad_groups_with_id(self):
        response = self.client.get(
            reverse('k1api.ad_groups'),
            {'ad_group_ids': 1},
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)

        self.assertDictEqual(data[0], {
            'id': 1,
            'name': 'ONE: test account 1 / test campaign 1 / test adgroup 1 / 1',
            'start_date': '2014-06-04',
            'end_date': None,
            'time_zone': 'America/New_York',
            'brand_name': 'brand1',
            'display_url': 'brand1.com',
            'tracking_codes': 'tracking1&tracking2',
            'target_devices': [],
            'target_os': None,
            'target_browsers': None,
            'target_placements': None,
            'iab_category': 'IAB24',
            'campaign_language': 'en',
            'target_regions': [],
            'exclusion_target_regions': [],
            'retargeting': [
                             {'event_id': '100', 'event_type': 'redirect_adgroup', 'exclusion': False},
                             {'event_id': '200', 'event_type': 'redirect_adgroup', 'exclusion': True},
                             {'event_id': '1', 'event_type': 'aud', 'exclusion': False},
                             {'event_id': '2', 'event_type': 'aud', 'exclusion': True}],
            'demographic_targeting': ["or", "bluekai:1", "bluekai:2"],
            'interest_targeting': ["tech", "entertainment"],
            'exclusion_interest_targeting': ["politics", "war"],
            'campaign_id': 1,
            'account_id': 1,
            'agency_id': 20,
            'goal_types': [2, 5],
            'goals': [{
                'campaign_id': 1,
                'conversion_goal': None,
                'id': 2,
                'primary': True,
                'type': 2,
                'values': [],
            }, {
                'campaign_id': 1,
                'conversion_goal': None,
                'id': 1,
                'primary': False,
                'type': 5,
                'values': [],
            }],
            'b1_sources_group': {
                'daily_budget': '10.0000',
                'cpc_cc': '0.0100',
                'enabled': True,
                'state': 2,
            },
            'dayparting': {'monday': [1, 2, 3], 'timezone': 'CET'},
            'max_cpm': '1.6000',
            'whitelist_publisher_groups': [1, 2, 5, 6, 9, 10],
            'blacklist_publisher_groups': [3, 4, 7, 8, 11, 12],
            'delivery_type': 1,
            'click_capping_daily_ad_group_max_clicks': 15,
            'click_capping_daily_click_budget': '5.0000',
            'custom_flags': {'flag_1': True, 'flag_2': True, 'flag_3': True, 'flag_4': True},
            'amplify_review': True,
        })

    def test_get_ad_groups_with_id_with_some_flags(self):
        a = dash.models.AdGroup.objects.get(pk=1)
        a.custom_flags = {}
        a.save(None)
        a.campaign.custom_flags = {}
        a.campaign.save()

        response = self.client.get(
            reverse('k1api.ad_groups'),
            {'ad_group_ids': 1},
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)

        self.assertDictEqual(data[0], {
            'id': 1,
            'name': 'ONE: test account 1 / test campaign 1 / test adgroup 1 / 1',
            'start_date': '2014-06-04',
            'end_date': None,
            'time_zone': 'America/New_York',
            'brand_name': 'brand1',
            'display_url': 'brand1.com',
            'tracking_codes': 'tracking1&tracking2',
            'target_devices': [],
            'target_os': None,
            'target_browsers': None,
            'target_placements': None,
            'iab_category': 'IAB24',
            'campaign_language': 'en',
            'target_regions': [],
            'exclusion_target_regions': [],
            'retargeting': [
                {'event_id': '100', 'event_type': 'redirect_adgroup', 'exclusion': False},
                {'event_id': '200', 'event_type': 'redirect_adgroup', 'exclusion': True},
                {'event_id': '1', 'event_type': 'aud', 'exclusion': False},
                {'event_id': '2', 'event_type': 'aud', 'exclusion': True}],
            'demographic_targeting': ["or", "bluekai:1", "bluekai:2"],
            'interest_targeting': ["tech", "entertainment"],
            'exclusion_interest_targeting': ["politics", "war"],
            'campaign_id': 1,
            'account_id': 1,
            'agency_id': 20,
            'goal_types': [2, 5],
            'goals': [{
                'campaign_id': 1,
                'conversion_goal': None,
                'id': 2,
                'primary': True,
                'type': 2,
                'values': [],
            }, {
                'campaign_id': 1,
                'conversion_goal': None,
                'id': 1,
                'primary': False,
                'type': 5,
                'values': [],
            }],
            'b1_sources_group': {
                'daily_budget': '10.0000',
                'cpc_cc': '0.0100',
                'enabled': True,
                'state': 2,
            },
            'dayparting': {'monday': [1, 2, 3], 'timezone': 'CET'},
            'max_cpm': '1.6000',
            'whitelist_publisher_groups': [1, 2, 5, 6, 9, 10],
            'blacklist_publisher_groups': [3, 4, 7, 8, 11, 12],
            'delivery_type': 1,
            'click_capping_daily_ad_group_max_clicks': 15,
            'click_capping_daily_click_budget': '5.0000',
            'custom_flags': {'flag_1': False, 'flag_2': True, 'flag_3': True, 'flag_4': True},
            'amplify_review': True,
        })

    @patch('utils.redirector_helper.insert_adgroup')
    def test_get_ad_groups(self, mock_redirector):
        n = 10
        source = magic_mixer.blend(dash.models.Source, source_type__type='abc')
        ad_groups = magic_mixer.cycle(n).blend(dash.models.AdGroup, campaign_id=1)
        magic_mixer.cycle(n).blend(dash.models.AdGroupSource, ad_group=(ag for ag in ad_groups), source=source)
        for ad_group in ad_groups:
            ad_group.settings.update_unsafe(None, brand_name='old')
        for ad_group in ad_groups:
            ad_group.settings.update_unsafe(None, brand_name='new')

        # make the first one archived
        request = magic_mixer.blend_request_user()
        ad_groups[0].settings.update(request, archived=True)

        response = self.client.get(
            reverse('k1api.ad_groups'),
            {
                'source_types': 'abc',
            }
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(
            [{'id': obj['id'], 'brand_name': obj['brand_name']} for obj in data],
            [{'id': obj.id, 'brand_name': obj.settings.brand_name} for obj in ad_groups[1:]])

    def test_get_ad_groups_pagination(self):
        n = 10
        source = magic_mixer.blend(dash.models.Source, source_type__type='abc')
        ad_groups = magic_mixer.cycle(n).blend(dash.models.AdGroup, campaign_id=1)
        magic_mixer.cycle(n).blend(dash.models.AdGroupSource, ad_group=(ag for ag in ad_groups), source=source)
        response = self.client.get(
            reverse('k1api.ad_groups'),
            {
                'source_types': 'abc',
                'marker': ad_groups[2].id,
                'limit': 5
            }
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        self.assertEqual([obj['id'] for obj in data], [obj.id for obj in ad_groups[3:8]])
