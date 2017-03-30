import itertools
import time
import json
import datetime

import mock
from mock import patch, ANY
import urllib

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import F

import dash.constants
import dash.models

import logging

from utils.test_helper import ListMatcher
from utils import request_signer
from utils import email_helper

from redshiftapi import quickstats

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class K1ApiTest(TestCase):

    fixtures = ['test_publishers.yaml', 'test_k1_api.yaml']

    def setUp(self):
        self.test_signature = True
        settings.K1_API_SIGN_KEY = 'test_api_key'
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()

        self.maxDiff = None

    def tearDown(self):
        if self.test_signature:
            self.mock_verify_wsgi_request.assert_called_with(ANY, 'test_api_key')
        self.verify_patcher.stop()

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

    def test_404_without_signature(self):
        self.test_signature = False
        self.mock_verify_wsgi_request.side_effect = request_signer.SignatureError
        test_paths = [
            'k1api.ad_groups',
            'k1api.ad_groups.sources',
            'k1api.content_ads',
            'k1api.content_ads.sources',
            'k1api.accounts',
            'k1api.sources',
            'k1api.source_pixels',
            'k1api.ga_accounts',
            'k1api.facebook_accounts',
            'k1api.publisher_groups',
        ]
        for path in test_paths:
            self._test_signature(path)

    def _assert_response_ok(self, response, data):
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', data)
        self.assertEqual(data['error'], None)
        self.assertIn('response', data)
        self.assertNotEqual(data['response'], None)

    def test_get_accounts(self):
        response = self.client.get(
            reverse('k1api.accounts'),
        )
        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']
        self.assertEqual(len(data), dash.models.Account.objects.count())

    def test_get_accounts_with_id(self):
        response = self.client.get(
            reverse('k1api.accounts'), {'account_ids': 1},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], {
            u'id': 1,
            u'name': u'test account 1',
            u'outbrain_marketer_id': u'abcde',
            u'custom_audiences': ListMatcher([
                {u'pixel_id': 1,
                 u'rules': [
                     {u'type': 1, u'values': u'dummy', u'id': 1},
                     {u'type': 2, u'values': u'dummy2', u'id': 2}],
                 u'name': 'Audience 1',
                 u'id': 1,
                 u'ttl': 90},
                {u'pixel_id': 2,
                 u'rules': [
                     {u'type': 1, u'values': u'dummy3', u'id': 3},
                     {u'type': 2, u'values': u'dummy4', u'id': 4}],
                 u'name': 'Audience 2',
                 u'id': 2,
                 u'ttl': 60}]),
            u'pixels': ListMatcher([
                {u'id': 1,
                 u'name': u'Pixel 1',
                 u'slug': u'testslug1',
                 u'audience_enabled': False,
                 u'additional_pixel': False,
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
                 u'name': u'Pixel 2',
                 u'slug': u'testslug2',
                 u'audience_enabled': True,
                 u'additional_pixel': False,
                 u'source_pixels': ListMatcher([
                     {u'url': u'http://www.xy.com/pixelendpoint',
                      u'source_pixel_id': u'xy_zem2',
                      u'source_type': u'taboola',
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
            ])})

    def test_get_default_source_credentials(self):
        response = self.client.get(
            reverse('k1api.sources'),
            {'source_slugs': 'facebook'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        data = data['response']
        self.assertEqual(data[0]['credentials']['credentials'], u'h')

    def test_get_custom_audience(self):
        response = self.client.get(
            reverse('k1api.accounts'),
            {'account_ids': 1},
        )

        json_data = json.loads(response.content)
        self._assert_response_ok(response, json_data)
        accounts_data = json_data['response']
        self.assertEqual(1, len(accounts_data))
        data = accounts_data[0]['custom_audiences']

        self.assertEqual(2, len(data))
        self.assertEqual(data, ListMatcher([{
            u'id': 1,
            u'name': u'Audience 1',
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
        }, {
            u'id': 2,
            u'name': u'Audience 2',
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
        }]))

    @patch('utils.redirector_helper.upsert_audience')
    def test_update_source_pixel_with_existing(self, redirector_mock):
        body = {
            'pixel_id': 1,
            'source_type': 'facebook',
            'url': 'http://www.dummy_fb.com/pixie_endpoint',
            'source_pixel_id': 'fb_dummy_id',
        }
        response = self.client.put(
            reverse('k1api.source_pixels'), json.dumps(body), 'application/json',
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        self.assertDictEqual(body, data['response'])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=3)
        self.assertEqual(updated_pixel.url, 'http://www.dummy_fb.com/pixie_endpoint')
        self.assertEqual(updated_pixel.source_pixel_id, 'fb_dummy_id')

        audience = dash.models.Audience.objects.get(pixel_id=1)
        redirector_mock.assert_called_once_with(audience)

    @patch('utils.redirector_helper.upsert_audience')
    def test_update_source_pixel_with_existing_for_outbrain(self, redirector_mock):
        body = {
            'pixel_id': 2,
            'source_type': 'outbrain',
            'url': 'http://www.dummy_ob.com/pixie_endpoint',
            'source_pixel_id': 'ob_dummy_id',
        }
        response = self.client.put(
            reverse('k1api.source_pixels'), json.dumps(body), 'application/json',
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        self.assertDictEqual(body, data['response'])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=1)
        self.assertEqual(updated_pixel.pixel.id, 2)

        audiences = dash.models.Audience.objects.filter(pixel_id__in=[2, 1])
        redirector_mock.assert_has_calls([
            mock.call(audiences[0]),
            mock.call(audiences[1]),
        ], any_order=True)

    @patch('utils.redirector_helper.upsert_audience')
    def test_update_source_pixel_create_new(self, redirector_mock):
        body = {
            'pixel_id': 3,
            'source_type': 'facebook',
            'url': 'http://www.dummy_fb.com/pixie_endpoint',
            'source_pixel_id': 'fb_dummy_id',
        }
        response = self.client.put(
            reverse('k1api.source_pixels'), json.dumps(body), 'application/json',
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        self.assertDictEqual(body, data['response'])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=7)
        self.assertEqual(updated_pixel.url, 'http://www.dummy_fb.com/pixie_endpoint')
        self.assertEqual(updated_pixel.source_pixel_id, 'fb_dummy_id')

        self.assertFalse(redirector_mock.called)

    @patch('utils.redirector_helper.upsert_audience')
    def test_update_source_pixel_create_new_for_outbrain(self, redirector_mock):
        body = {
            'pixel_id': 3,
            'source_type': 'outbrain',
            'url': 'http://www.dummy_ob.com/pixie_endpoint',
            'source_pixel_id': 'ob_dummy_id',
        }
        response = self.client.put(
            reverse('k1api.source_pixels'), json.dumps(body), 'application/json',
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        self.assertDictEqual(body, data['response'])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=8)
        self.assertEqual(updated_pixel.url, 'http://www.dummy_ob.com/pixie_endpoint')
        self.assertEqual(updated_pixel.source_pixel_id, 'ob_dummy_id')

        self.assertFalse(redirector_mock.called)

    def _test_source_credentials_filter(self, source_slugs=None):
        response = self.client.get(
            reverse('k1api.sources'),
            {'source_slugs': ','.join(source_slugs)},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        for source in data:
            sc = dash.models.SourceCredentials.objects.get(pk=source['credentials']['id'])
            self.assertEqual(sc.credentials, source['credentials']['credentials'])

        scs = dash.models.Source.objects.all()
        if source_slugs:
            scs = scs.filter(bidder_slug__in=source_slugs)
        self.assertEqual(len(data), scs.count())

    def test_get_source_credentials(self):
        test_cases = [
            ['adblade'],
            ['adblade', 'outbrain', 'yahoo'],
        ]
        for source_types in test_cases:
            self._test_source_credentials_filter(source_types)

    def _test_content_ad_source_ids_filters(self, source_types=None,
                                            source_content_ad_ids=None):
        response = self.client.get(
            reverse('k1api.content_ads.sources'),
            data=dict(source_slugs=','.join(source_types), source_content_ad_ids=','.join(source_content_ad_ids))
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        expected_count = dash.models.ContentAdSource.objects.filter(
            source__bidder_slug__in=source_types,
            source_content_ad_id__in=source_content_ad_ids).count()
        self.assertEqual(expected_count, len(data))
        self.assertGreater(len(data), 0)
        for content_ad_source in data:
            db_cas = dash.models.ContentAdSource.objects.get(
                id=content_ad_source['id'])
            self.assertEqual(content_ad_source['source_content_ad_id'], db_cas.source_content_ad_id)
            self.assertEqual(content_ad_source['content_ad_id'], db_cas.content_ad_id)
            self.assertEqual(content_ad_source['ad_group_id'], db_cas.content_ad.ad_group_id)
            self.assertEqual(content_ad_source['source_slug'], db_cas.source.bidder_slug)

        contentadsources = dash.models.ContentAdSource.objects
        if source_content_ad_ids:
            contentadsources = contentadsources.filter(
                source_content_ad_id__in=source_content_ad_ids)
        if source_types:
            contentadsources = contentadsources.filter(
                source__source_type__type__in=source_types)
        self.assertEqual(len(data), contentadsources.count())

    def test_get_content_ad_source_mapping(self):
        test_source_filters = [
            ['adblade'],
            ['adblade', 'outbrain', 'yahoo'],
        ]
        test_source_content_ads = [
            ['987654321'],
            ['987654321', '123456789'],
        ]
        test_cases = itertools.product(test_source_filters, test_source_content_ads)
        for source_types, source_content_ad_ids in test_cases:
            self._test_content_ad_source_ids_filters(
                source_types, source_content_ad_ids)

    def test_get_ga_accounts(self):
        response = self.client.get(
            reverse('k1api.ga_accounts'),
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data['ga_accounts']), 2)
        self.assertEqual(data['ga_accounts'][0]['account_id'], 1)
        self.assertEqual(data['ga_accounts'][0]['ga_account_id'], '123')
        self.assertEqual(data['ga_accounts'][0]['ga_web_property_id'], 'UA-123-2')
        self.assertEqual(data['ga_accounts'][1]['account_id'], 2)
        self.assertEqual(data['ga_accounts'][1]['ga_account_id'], '123')
        self.assertEqual(data['ga_accounts'][1]['ga_web_property_id'], 'UA-123-3')

    def _test_get_content_ad_sources_for_ad_group(self, ad_group_id, content_ad_id):
        response = self.client.get(
            reverse('k1api.content_ads.sources'),
            {'source_type': 'adblade',
             'ad_group_id': 1},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        required_fields = {
            u'id',
            u'content_ad_id',
            u'ad_group_id',
            u'source_content_ad_id',
            u'submission_status',
            u'tracking_slug',
            u'source_slug',
            u'state',
        }

        db_ags = dash.models.ContentAdSource.objects.filter(content_ad__ad_group_id=ad_group_id)
        if content_ad_id:
            db_ags = db_ags.filter(content_ad_id=content_ad_id)

        for cas in data:
            self.assertLessEqual(required_fields, set(cas.keys()))

    def test_get_content_ad_sources_for_ad_group(self):
        test_cases = [
            (1, None),
            (1, 1),
        ]
        for ad_group_id, content_ad_id in test_cases:
            self._test_get_content_ad_sources_for_ad_group(ad_group_id, content_ad_id)

    def test_get_content_ad_sources_for_ad_group_no_adgroupsource(self):
        response = self.client.get(
            reverse('k1api.content_ads.sources'),
            {'source_types': 'outbrain',
             'ad_group_ids': 1},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']
        self.assertEqual(data, [])

    def test_get_sources_by_tracking_slug(self):
        response = self.client.get(
            reverse('k1api.sources')
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertGreater(len(data), 0)
        for source in data:
            self.assertIn('id', source)

    def test_get_publisher_groups(self):
        account_id = 1

        response = self.client.get(
            reverse('k1api.publisher_groups'),
            {'account_id': account_id}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        pubgroups = dash.models.PublisherGroup.objects.filter(account_id=account_id)

        self.assertEqual(data, [
            {'id': pubgroup.id, 'account_id': 1} for pubgroup in pubgroups
        ])

    def test_get_publisher_groups_entries(self):
        account_id = 1

        response = self.client.get(
            reverse('k1api.publisher_groups_entries'),
            {'account_id': account_id, 'offset': 0, 'limit': 2}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(data, [
            {'outbrain_publisher_id': '', 'publisher': 'pub1', 'include_subdomains': True,
             'publisher_group_id': 1, 'source_slug': 'adblade', 'account_id': 1},
            {'outbrain_publisher_id': 'asd123', 'publisher': 'pub2', 'include_subdomains': True,
             'publisher_group_id': 1, 'source_slug': None, 'account_id': 1},
        ])

    def test_get_publisher_groups_entries_source_slug(self):
        account_id = 1
        source_slug = 'adblade'

        response = self.client.get(
            reverse('k1api.publisher_groups_entries'),
            {'account_id': account_id, 'source_slug': source_slug, 'offset': 0, 'limit': 2}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(data, [
            {'outbrain_publisher_id': '', 'publisher': 'pub1', 'include_subdomains': True,
             'publisher_group_id': 1, 'source_slug': 'adblade', 'account_id': 1},
        ])

    def test_get_publisher_groups_entries_limit(self):
        account_id = 1

        response = self.client.get(
            reverse('k1api.publisher_groups_entries'),
            {'account_id': account_id, 'offset': 1, 'limit': 1}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(data, [
            {'outbrain_publisher_id': 'asd123', 'publisher': 'pub2', 'include_subdomains': True,
             'publisher_group_id': 1, 'source_slug': None, 'account_id': 1},
        ])

    def test_get_publisher_groups_entries_no_limit_error(self):
        account_id = 1

        response = self.client.get(
            reverse('k1api.publisher_groups_entries'),
            {'account_id': account_id}
        )

        self.assertEqual(response.status_code, 400)

    def test_get_accounts_slugs_ad_groups(self):
        accounts = (1, 2)
        response = self.client.get(
            reverse('k1api.r1_mapping'),
            {'account': accounts},
        )

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

    def test_get_publishers_blacklist_outbrain(self):
        response = self.client.get(
            reverse('k1api.outbrain_publishers_blacklist'),
            {'marketer_id': 'cdefg'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        expected = (
            dash.models.PublisherGroupEntry.objects
                .filter(publisher_group_id__in=[1000, 11, 12])
                .filter(source__bidder_slug='outbrain')
                .annotate(name=F('publisher'))
                .values(u'name')
        )
        self.assertGreater(len(expected), 0)
        self.assertEqual(data, {
            u'blacklist': list(expected),
            u'account': {
                u'id': 1000,
                u'name': u'test outbrain account',
                u'outbrain_marketer_id': u'cdefg'
            }
        })

    def test_get_ad_groups_with_id(self):
        response = self.client.get(
            reverse('k1api.ad_groups'),
            {'ad_group_ids': 1},
        )

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
            u'target_devices': [],
            u'target_os': [],
            u'target_placements': [],
            u'iab_category': u'IAB24',
            u'target_regions': [],
            u'exclusion_target_regions': [],
            u'retargeting': [
                             {u'event_id': u'100', u'event_type': u'redirect_adgroup', u'exclusion': False},
                             {u'event_id': u'200', u'event_type': u'redirect_adgroup', u'exclusion': True},
                             {u'event_id': u'1', u'event_type': u'aud', u'exclusion': False},
                             {u'event_id': u'2', u'event_type': u'aud', u'exclusion': True}],
            u'demographic_targeting': [u"or", u"bluekai:1", u"bluekai:2"],
            u'interest_targeting': [u"tech", u"entertainment"],
            u'exclusion_interest_targeting': [u"politics", u"war"],
            u'campaign_id': 1,
            u'account_id': 1,
            u'agency_id': 20,
            u'goal_types': [2, 5],
            u'b1_sources_group': {
                u'daily_budget': u'10.0000',
                u'enabled': True,
                u'state': 2,
            },
            u'dayparting': {u'monday': [1, 2, 3], u'timezone': u'CET'},
            u'max_cpm': u'1.6000',
            u'whitelist_publisher_groups': ListMatcher([1, 2, 5, 6, 9, 10]),
            u'blacklist_publisher_groups': ListMatcher([3, 4, 7, 8, 11, 12]),
        })

    def test_get_ad_groups(self):
        response = self.client.get(
            reverse('k1api.ad_groups'),
        )

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
            u'target_devices',
            u'iab_category',
            u'target_regions',
            u'exclusion_target_regions',
            u'retargeting',
            u'campaign_id',
            u'account_id',
            u'agency_id',
            u'goal_types',
            u'demographic_targeting',
            u'interest_targeting',
            u'exclusion_interest_targeting',
        }

        for item in data:
            self.assertEqual(len(required_fields - set(item.keys())), 0)

    @patch.object(quickstats, 'query_adgroup', autospec=True)
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
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(data, mock_stats)

    def test_get_ad_group_stats_false_source(self):
        response = self.client.get(
            reverse('k1api.ad_groups.stats'),
            {'ad_group_id': 1, 'source_slug': 'doesnotexist'}
        )

        self.assertEqual(response.status_code, 400)

    def test_get_ad_groups_sources(self):
        response = self.client.get(
            reverse('k1api.ad_groups.sources'),
            {'source_types': 'b1'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 2)

        self.assertDictEqual(data[0], {
            u'ad_group_id': 1,
            u'slug': u'b1_adiant',
            u'state': 2,
            u'cpc_cc': u'0.1200',
            u'daily_budget_cc': u'1.5000',
            u'source_campaign_key': [u'fake'],
            u'tracking_code': u'tracking1&tracking2',
        })

        self.assertDictEqual(data[1], {
            u'ad_group_id': 2,
            u'slug': u'b1_google',
            u'state': 1,
            u'cpc_cc': u'0.1300',
            u'daily_budget_cc': u'1.6000',
            u'source_campaign_key': [u'fake'],
            u'tracking_code': u'tracking1&tracking2',
        })

    def test_get_ad_groups_exchanges_with_id(self):
        response = self.client.get(
            reverse('k1api.ad_groups.sources'),
            {'ad_group_ids': 1,
             'source_types': 'b1'},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)

        self.assertDictEqual(data[0], {
            u'ad_group_id': 1,
            u'slug': u'b1_adiant',
            u'state': 2,
            u'cpc_cc': u'0.1200',
            u'daily_budget_cc': u'1.5000',
            u'source_campaign_key': [u'fake'],
            u'tracking_code': u'tracking1&tracking2',
        })

    def test_get_content_ads_by_id(self):
        response = self.client.get(
            reverse('k1api.content_ads'),
            {'content_ad_ids': 1,
             'ad_group_ids': 1},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        expected = [{
            "image_crop": "center",
            "image_hash": None,
            "description": "",
            "ad_group_id": 1,
            "call_to_action": "",
            "url": "http://testurl.com",
            "title": "Test Article 1",
            "brand_name": "",
            "image_width": None,
            "image_id": "123456789",
            "image_height": None,
            "display_url": "",
            "redirect_id": None,
            "id": 1,
            "tracker_urls": None
        }]
        self.assertEqual(data, expected)

    def test_get_content_ads(self):
        response = self.client.get(
            reverse('k1api.content_ads'),
            {'include_archived': False}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data_without_archived = data['response']

        response = self.client.get(
            reverse('k1api.content_ads'),
            {'include_archived': True}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data_with_archived = data['response']

        self.assertEqual(5, len(data_without_archived))
        self.assertEqual(6, len(data_with_archived))

    def test_get_content_ads_sources(self):
        response = self.client.get(
            reverse('k1api.content_ads.sources'),
            {'content_ad_ids': 1,
             'ad_group_ids': 1,
             'source_slugs': 'adblade'},
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        data = data['response']

        expected = [
            {
                "id": 1,
                "content_ad_id": 1,
                "ad_group_id": 1,
                "submission_status": 1,
                "source_content_ad_id": "987654321",
                "tracking_slug": "adblade",
                "state": 1,
                "source_slug": "adblade"
            }
        ]

        self.assertEqual(data, expected)

    def test_update_content_ad_status(self):
        cas = dash.models.ContentAdSource.objects.get(pk=1)
        cas.source_content_ad_id = None
        cas.save()
        response = self.client.generic(
            'PUT',
            reverse('k1api.content_ads.sources'),
            json.dumps({
                'submission_status': 2, 'submission_errors': 'my-errors',
                'source_content_ad_id': 123
            }),
            'application/json',
            QUERY_STRING=urllib.urlencode({'content_ad_id': 1, 'source_slug': 'adblade'})
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        cas = dash.models.ContentAdSource.objects.filter(content_ad_id=1, source__bidder_slug='adblade')[0]
        self.assertEqual(cas.submission_status, 2)
        self.assertEqual(cas.submission_errors, 'my-errors')
        self.assertEqual(cas.source_content_ad_id, '123')

        response = self.client.put(
            reverse('k1api.content_ads.sources'),
            json.dumps({'content_ad_id': 1000, 'source_slug': 'adblade',
                        'submission_status': 2, 'submission_errors': 'my-errors',
                        'source_content_ad_id': 123}),
            'application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_update_content_ad_status_refuse_delete(self):
        response = self.client.generic(
            'PUT',
            reverse('k1api.content_ads.sources'),
            json.dumps({
                'submission_status': 2, 'submission_errors': 'my-errors',
                'source_content_ad_id': ''
            }),
            'application/json',
            QUERY_STRING=urllib.urlencode({'content_ad_id': 1, 'source_slug': 'adblade'})
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Cannot change', data['error'])

    def test_set_source_campaign_key(self):
        ags = dash.models.AdGroupSource.objects.get(pk=1)
        ags.source_campaign_key = None
        ags.save()

        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources'),
            json.dumps({'source_campaign_key': ['abc']}),
            'application/json',
            QUERY_STRING=urllib.urlencode({'ad_group_id': 1, 'source_slug': 'adblade'})
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        ags = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ags.source_campaign_key, ['abc'])

    def test_get_outbrain_marketer_id(self):
        response = self.client.get(
            reverse('k1api.outbrain_marketer_id'),
            {'ad_group_id': '1'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        ag = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(ag.campaign.account.outbrain_marketer_id, data['response'])

    def test_sync_outbrain_marketer_new(self):
        self.assertFalse(
            dash.models.OutbrainAccount.objects.filter(
                marketer_id='abc-456',
                marketer_name='Abc 456'
            ).exists()
        )
        response = self.client.generic(
            'PUT',
            reverse('k1api.outbrain_marketer_sync'),
            QUERY_STRING=urllib.urlencode({'marketer_id': 'abc-456', 'marketer_name': 'Abc 456'})
        )
        self.assertEqual(
            json.loads(response.content)['response'],
            {
                'created': True,
                'marketer_id': 'abc-456',
                'marketer_name': 'Abc 456',
                'used': False,
            }
        )
        self.assertTrue(
            dash.models.OutbrainAccount.objects.filter(
                marketer_id='abc-456',
                marketer_name='Abc 456'
            ).exists()
        )

    def test_sync_outbrain_marketer_existing(self):
        dash.models.OutbrainAccount.objects.create(
            marketer_id='abc-123',
            marketer_name='Abc 123',
            used=True
        )
        response = self.client.generic(
            'PUT',
            reverse('k1api.outbrain_marketer_sync'),
            QUERY_STRING=urllib.urlencode({'marketer_id': 'abc-123', 'marketer_name': 'Abc 123'})
        )
        self.assertEqual(
            json.loads(response.content)['response'],
            {
                'created': False,
                'marketer_id': 'abc-123',
                'marketer_name': 'Abc 123',
                'used': True,
            }
        )
        self.assertTrue(
            dash.models.OutbrainAccount.objects.filter(
                marketer_id='abc-123',
                marketer_name='Abc 123'
            ).exists()
        )

    def test_sync_outbrain_marketer_existing_update_name(self):
        dash.models.OutbrainAccount.objects.create(
            marketer_id='abc-123',
            marketer_name='Abc 123',
            used=True
        )
        response = self.client.generic(
            'PUT',
            reverse('k1api.outbrain_marketer_sync'),
            QUERY_STRING=urllib.urlencode({'marketer_id': 'abc-123', 'marketer_name': 'New 123'})
        )
        self.assertEqual(
            json.loads(response.content)['response'],
            {
                'created': False,
                'marketer_id': 'abc-123',
                'marketer_name': 'New 123',
                'used': True,
            }
        )
        self.assertTrue(
            dash.models.OutbrainAccount.objects.filter(
                marketer_id='abc-123',
                marketer_name='New 123'
            ).exists()
        )

    @patch.object(email_helper, 'send_outbrain_accounts_running_out_email')
    def test_get_outbrain_marketer_id_assign_new(self, mock_sendmail):
        response = self.client.get(
            reverse('k1api.outbrain_marketer_id'),
            {'ad_group_id': '3'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        ag = dash.models.AdGroup.objects.get(pk=3)
        self.assertEqual(ag.campaign.account.outbrain_marketer_id, data['response'])
        mock_sendmail.assert_called_with(3)

    def test_get_facebook_accounts(self):
        response = self.client.get(
            reverse('k1api.facebook_accounts'),
        )

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

    def test_get_facebook_accounts_with_ad_group(self):
        response = self.client.get(
            reverse('k1api.facebook_accounts'),
            {'ad_group_id': '1'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        fb_account = dash.models.FacebookAccount.objects.get(pk=1)
        self.assertEqual(fb_account.ad_account_id, data['response']['ad_account_id'])

    def test_get_facebook_accounts_with_account(self):
        response = self.client.get(
            reverse('k1api.facebook_accounts'),
            {'account_id': '1'}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        fb_account = dash.models.FacebookAccount.objects.get(pk=1)
        self.assertEqual(fb_account.ad_account_id, data['response']['ad_account_id'])

    def test_update_ad_group_source(self):
        params = {'ad_group_id': 1,
                  'source_slug': 'adblade'}
        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources'),
            json.dumps({'state': 2}),
            'application/json',
            QUERY_STRING=urllib.urlencode(params)
        )
        data = json.loads(response.content)
        self._assert_response_ok(response, data)

        a = dash.models.AdGroupSource.objects.get(ad_group__id=1,
                                                  source__bidder_slug='adblade')

        self.assertEqual(a.get_current_settings().state, 2)

    def test_update_ad_group_source_refuse_change(self):
        params = {'ad_group_id': 1,
                  'source_slug': 'adblade'}
        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources'),
            json.dumps({'source_campaign_key': ''}),
            'application/json',
            QUERY_STRING=urllib.urlencode(params)
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Cannot change', data['error'])

    def test_update_ad_group_source_state_no_ad_group(self):
        params = {'ad_group_id': 12345,
                  'source_slug': 'adblade'}
        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources'),
            json.dumps({'state': 2}),
            'application/json',
            QUERY_STRING=urllib.urlencode(params)
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'No AdGroupSource exists for ad_group_id: 12345 with bidder_slug adblade')

    def test_update_ad_group_source_state_incorrect_body(self):
        params = {'slug': 'adblade'}
        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources'),
            json.dumps({'state': 2}),
            'application/json',
            QUERY_STRING=urllib.urlencode(params)
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Must provide ad_group_id, source_slug and conf')

    def test_update_ad_group_source_blockers(self):
        params = {'source_slug': 'adblade', 'ad_group_id': 1}
        put_body = {'interest-targeting': 'Waiting for interest targeting to be set manually.'}
        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources.blockers'),
            json.dumps(put_body),
            'application/json',
            QUERY_STRING=urllib.urlencode(params)
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['response'], put_body)

        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=1, source__bidder_slug='adblade')
        self.assertEqual(ad_group_source.blockers, put_body)

    def test_update_ad_group_source_blockers_remove(self):
        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=1, source__bidder_slug='adblade')
        ad_group_source.blockers = {'interest-targeting': 'Waiting for interest targeting to be set manually.'}
        ad_group_source.save()

        params = {'source_slug': 'adblade', 'ad_group_id': 1}
        put_body = {'interest-targeting': None}
        response = self.client.generic(
            'PUT',
            reverse('k1api.ad_groups.sources.blockers'),
            json.dumps(put_body),
            'application/json',
            QUERY_STRING=urllib.urlencode(params)
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['response'], {})

        ad_group_source.refresh_from_db()
        self.assertEqual(ad_group_source.blockers, {})

    def test_update_facebook_account(self):
        response = self.client.put(
            reverse('k1api.facebook_accounts'),
            json.dumps({'status': 5, 'ad_account_id': 'act_555', 'account_id': 1}),
            'application/json'
        )
        fb_account = dash.models.FacebookAccount.objects.get(account__id=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fb_account.status, 5)
        self.assertEqual(fb_account.ad_account_id, 'act_555')

    def test_update_facebook_account_error(self):
        response = self.client.put(
            reverse('k1api.facebook_accounts'),
            json.dumps({'status': 5, 'ad_account_id': 'act_555'}),
            'application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'account id must be specified')
        self.assertEqual(response.status_code, 400)


class GeolocationsTest(K1ApiTest):

    def setUp(self):
        self.locs = [{'key': 'US', 'name': 'america', 'outbrain_id': 'abcdef', 'woeid': '123'},
                     {'key': 'US-NY', 'name': 'new york', 'outbrain_id': 'bbcdef', 'woeid': '124'}]

        for loc in self.locs:
            dash.geolocation.Geolocation.objects.create(**loc)
        super(GeolocationsTest, self).setUp()

    def test_get_geolocations(self):
        response = self.client.get(
            reverse('k1api.geolocations'),
            {'keys': 'US,US-NY,US:10000'}  # ZIPs can be ignored since we don't keep them all in DB
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        locations = data['response']

        self.assertEqual(self.locs, locations)

    def test_get_geolocations_empty_keys(self):
        response = self.client.get(
            reverse('k1api.geolocations'),
            {'keys': ''}
        )

        data = json.loads(response.content)
        self._assert_response_ok(response, data)
        locations = data['response']

        self.assertEqual([], locations)
