import datetime

from django.test import TestCase, override_settings

from utils.sort_helper import dissect_order

from dash import models
from dash.dashapi import queries


def extract_keys(key, rows):
    return [x[key] for x in rows]


@override_settings(R1_BLANK_REDIRECT_URL, 'http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryContentAdsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_content_ads(self):

        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows = queries.query_content_ads(
            content_ads, filtered_sources, True, '-name', None, None)

        self.assertEqual(rows, [{
            'image_hash': '300',
            'description': 'Example description',
            'content_ad_id': 3,
            'redirector_url': 'http://r1.zemanta.com/b/None/z1/1/3/',
            'brand_name': 'Example',
            'image_urls': {
                'square': '/300.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                'landscape': '/300.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
            },
            'batch_name': 'batch 2',
            'archived': True,
            'name': 'Title 3',
            'display_url': 'example.com',
            'url': 'http://testurl3.com',
            'call_to_action': 'Call to action',
            'label': '',
            'state': 2,
            'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
            'batch_id': 2,
            'title': 'Title 3'
        }, {
            'image_hash': '200',
            'description': 'Example description',
            'content_ad_id': 2,
            'redirector_url': 'http://r1.zemanta.com/b/r2/z1/1/2/',
            'brand_name': 'Example',
            'image_urls': {
                'square': '/200.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                'landscape': '/200.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
            },
            'batch_name': 'batch 1',
            'archived': False,
            'name': 'Title 2',
            'display_url': 'example.com',
            'url': 'http://testurl2.com',
            'call_to_action': 'Call to action',
            'label': '',
            'state': 2,
            'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
            'batch_id': 1,
            'title': 'Title 2'
        }, {
            'image_hash': '100',
            'description': 'Example description',
            'content_ad_id': 1,
            'redirector_url': 'http://r1.zemanta.com/b/r1/z1/1/1/',
            'brand_name': 'Example',
            'image_urls': {
                'square': '/100.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                'landscape': '/100.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
            },
            'batch_name': 'batch 1',
            'archived': False,
            'name': 'Title 1',
            'display_url': 'example.com',
            'url': 'http://testurl1.com',
            'call_to_action': 'Call to action',
            'label': '',
            'state': 1,
            'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
            'batch_id': 1,
            'title': 'Title 1'
        }])

    def test_order(self):
        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows = queries.query_content_ads(
            content_ads, filtered_sources, True, '-name', None, None)

        self.assertEqual(extract_keys('name', rows), [
            'Title 3', 'Title 2', 'Title 1'
        ])

        rows = queries.query_content_ads(
            content_ads, filtered_sources, True, 'batch_name', None, None)

        self.assertEqual(extract_keys('batch_name', rows), [
            'batch 1', 'batch 1', 'batch 2'
        ])

    def test_offset_limit(self):
        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows = queries.query_content_ads(
            content_ads, filtered_sources, True, 'name', 1, 2)

        self.assertEqual(extract_keys('content_ad_id', rows), [
            2, 3
        ])

    def test_archived(self):
        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows = queries.query_content_ads(
            content_ads, filtered_sources, False, '-name', None, None)

        self.assertEqual(extract_keys('content_ad_id', rows), [
            2, 1
        ])


class QueryAdGroupsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_ad_groups(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_ad_groups(ad_groups, sources, True, '-name', None, None)

        self.assertEqual(rows, [
            {'ad_group_id': 3, 'archived': True, 'name': 'test adgroup 3', 'status': 2},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2},
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1},
        ])

    def test_order(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_ad_groups(ad_groups, sources, True, 'name', None, None)

        self.assertEqual(rows, [
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2},
            {'ad_group_id': 3, 'archived': True, 'name': 'test adgroup 3', 'status': 2},
        ])

        rows = queries.query_ad_groups(ad_groups, sources, True, '-status', None, None)

        self.assertEqual(rows, [
            {'ad_group_id': 3, 'archived': True, 'name': 'test adgroup 3', 'status': 2},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2},
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1},
        ])

        rows = queries.query_ad_groups(ad_groups, sources, True, 'status', None, None)

        self.assertEqual(rows, [
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2},
            {'ad_group_id': 3, 'archived': True, 'name': 'test adgroup 3', 'status': 2},
        ])

    def test_archived(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_ad_groups(ad_groups, sources, False, 'name', None, None)

        self.assertEqual(rows, [
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2},
        ])

    def test_offset_limit(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_ad_groups(ad_groups, sources, True, 'name', 1, 1)

        self.assertEqual(rows, [
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2},
        ])


class QueryCampaignsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_campaigns(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_campaigns(campaigns, sources, True, '-name', None, None)

        self.assertEqual(rows, [
            {'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
            {'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
        ])

    def test_order(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_campaigns(campaigns, sources, True, 'name', None, None)

        self.assertEqual(rows, [
            {'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
            {'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
        ])

        rows = queries.query_campaigns(campaigns, sources, True, '-status', None, None)

        self.assertEqual(rows, [
            {'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
            {'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
        ])

        rows = queries.query_campaigns(campaigns, sources, True, 'status', None, None)

        self.assertEqual(rows, [
            {'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
            {'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
        ])

    def test_archived(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_campaigns(campaigns, sources, False, 'name', None, None)

        self.assertEqual(rows, [
            {'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
        ])

    def test_offset_limit(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_campaigns(campaigns, sources, True, 'name', 1, 1)

        self.assertEqual(rows, [
            {'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
        ])


class QueryAccountsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_accounts(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_accounts(accounts, sources, True, '-name', None, None)

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
        ])

    def test_order(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_accounts(accounts, sources, True, 'name', None, None)

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
        ])

        rows = queries.query_accounts(accounts, sources, True, '-status', None, None)

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
        ])

    def test_archived(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_accounts(accounts, sources, False, 'name', None, None)

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
        ])

    def test_offset_limit(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows = queries.query_accounts(accounts, sources, True, 'name', 0, 1)

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
        ])

        rows = queries.query_accounts(accounts, sources, True, 'name', 1, 1)

        self.assertEqual(rows, [])


class QuerySourcesTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_souces(self):
        sources = models.Source.objects.all()
        ad_group_sources = models.AdGroupSource.objects.all()

        rows = queries.query_sources(sources, ad_group_sources, '-name', None, None)

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2},
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1},
        ])

    def test_order(self):
        sources = models.Source.objects.all()
        ad_group_sources = models.AdGroupSource.objects.all()

        rows = queries.query_sources(sources, ad_group_sources, 'name', None, None)

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2},
        ])

        rows = queries.query_sources(sources, ad_group_sources, '-status', None, None)

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2},
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1},
        ])

    def test_offset_limit(self):
        sources = models.Source.objects.all()
        ad_group_sources = models.AdGroupSource.objects.all()

        rows = queries.query_sources(sources, ad_group_sources, 'name', 0, 1)

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1},
        ])
