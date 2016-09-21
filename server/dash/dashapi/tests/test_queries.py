import datetime
from decimal import Decimal

from django.test import TestCase, override_settings

from utils.sort_helper import dissect_order

from dash import models
from dash.dashapi import queries


START_DATE, END_DATE = datetime.date(2016, 7, 1), datetime.date(2016, 8, 31)


def extract_keys(keys, rows):
    if isinstance(keys, str):
        return [x[keys] for x in rows]
    return [[x[k] for k in keys] for x in rows]


@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryContentAdsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_order(self):
        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows, _ = queries.query_content_ads(
            content_ads, filtered_sources, START_DATE, END_DATE, True, '-name', None, None)

        self.assertEqual(extract_keys('name', rows), [
            'Title 3', 'Title 2', 'Title 1'
        ])

    def test_order_by_pk(self):
        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows, _ = queries.query_content_ads(
            content_ads, filtered_sources, START_DATE, END_DATE, True, 'batch_name', None, None)

        self.assertEqual(extract_keys(['content_ad_id', 'batch_name'], rows), [
            [1, 'batch 1'], [2, 'batch 1'], [3, 'batch 2']
        ])

        rows, _ = queries.query_content_ads(
            content_ads, filtered_sources, START_DATE, END_DATE, True, '-batch_name', None, None)

        self.assertEqual(extract_keys(['content_ad_id', 'batch_name'], rows), [
            [3, 'batch 2'], [2, 'batch 1'], [1, 'batch 1']
        ])

    def test_offset_limit(self):
        content_ads = models.ContentAd.objects.all()
        filtered_sources = models.Source.objects.all()

        rows, _ = queries.query_content_ads(
            content_ads, filtered_sources, START_DATE, END_DATE, True, 'name', 1, 2)

        self.assertEqual(extract_keys('content_ad_id', rows), [
            2, 3
        ])


class QueryAdGroupsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_ad_groups(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_ad_groups(ad_groups, sources, START_DATE, END_DATE, True, '-name', None, None)

        self.assertEqual(extract_keys(['ad_group_id', 'name'], rows), [
            [3, 'test adgroup 3'], [2, 'test adgroup 2'], [1, 'test adgroup 1'],
        ])

    def test_order(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_ad_groups(ad_groups, sources, START_DATE, END_DATE, True, 'name', None, None)

        self.assertEqual(extract_keys(['ad_group_id', 'name'], rows), [
            [1, 'test adgroup 1'], [2, 'test adgroup 2'], [3, 'test adgroup 3'],
        ])

        rows, _ = queries.query_ad_groups(ad_groups, sources, START_DATE, END_DATE, True, '-status', None, None)

        self.assertEqual(extract_keys(['ad_group_id', 'name', 'status', 'archived'], rows), [
            [2, 'test adgroup 2', 2, False],
            [1, 'test adgroup 1', 1, False],
            [3, 'test adgroup 3', 2, True],  # archived at the end
        ])

        rows, _ = queries.query_ad_groups(ad_groups, sources, START_DATE, END_DATE, True, 'status', None, None)

        self.assertEqual(extract_keys(['ad_group_id', 'name', 'status', 'archived'], rows), [
            [1, 'test adgroup 1', 1, False],
            [2, 'test adgroup 2', 2, False],
            [3, 'test adgroup 3', 2, True],  # archived at the end
        ])

    def test_offset_limit(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_ad_groups(ad_groups, sources, START_DATE, END_DATE, True, 'name', 1, 1)

        self.assertEqual(extract_keys(['ad_group_id', 'name'], rows), [
            [2, 'test adgroup 2'],
        ])


class QueryCampaignsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_campaigns(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, '-name', None, None)

        self.assertEqual(extract_keys(['campaign_id', 'name'], rows), [
            [2, 'test campaign 2'],
            [1, 'test campaign 1'],
        ])

    def test_order(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        for c in campaigns:
            # archived is always last, modify this to get proper ordering
            # not based on archived flag
            c.restore(None)

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, 'name', None, None)

        self.assertEqual(extract_keys(['campaign_id', 'name'], rows), [
            [1, 'test campaign 1'],
            [2, 'test campaign 2'],
        ])

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, 'campaign_manager', None, None)

        self.assertEqual(extract_keys(['campaign_id', 'name', 'campaign_manager'], rows), [
            [2, 'test campaign 2', 'mad.max@zemanta.com'],
            [1, 'test campaign 1', 'supertestuser@test.com'],
        ])

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, '-campaign_manager', None, None)

        self.assertEqual(extract_keys(['campaign_id', 'name', 'campaign_manager'], rows), [
            [1, 'test campaign 1', 'supertestuser@test.com'],
            [2, 'test campaign 2', 'mad.max@zemanta.com'],
        ])

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, '-status', None, None)

        self.assertEqual(extract_keys(['campaign_id', 'name', 'status'], rows), [
            [2, 'test campaign 2', 2],
            [1, 'test campaign 1', 1],
        ])

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, 'status', None, None)

        self.assertEqual(extract_keys(['campaign_id', 'name', 'status'], rows), [
            [1, 'test campaign 1', 1],
            [2, 'test campaign 2', 2],
        ])

    def test_offset_limit(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_campaigns(campaigns, sources, START_DATE, END_DATE, True, 'name', 1, 1)

        self.assertEqual(extract_keys(['campaign_id', 'name'], rows), [
            [2, 'test campaign 2'],
        ])


class QueryAccountsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_accounts(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, '-name', None, None)

        self.assertEqual(extract_keys(['account_id', 'name'], rows), [
            [1, 'test account 1'],
        ])

    def test_order(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, 'name', None, None)
        self.assertEqual(extract_keys(['account_id', 'name'], rows), [
            [1, 'test account 1'],
        ])

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, 'agency', None, None)
        self.assertEqual(extract_keys(['account_id', 'name', 'agency'], rows), [
            [1, 'test account 1', ''],
        ])

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, '-account_type', None, None)
        self.assertEqual(extract_keys(['account_id', 'name', 'account_type'], rows), [
            [1, 'test account 1', 'Self-managed'],
        ])

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, 'default_account_manager',
                                         None, None)
        self.assertEqual(extract_keys(['account_id', 'name', 'default_account_manager'], rows), [
            [1, 'test account 1', 'mad.max@zemanta.com'],
        ])

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, 'default_sales_representative',
                                         None, None)
        self.assertEqual(extract_keys(['account_id', 'name', 'default_sales_representative'], rows), [
            [1, 'test account 1', 'supertestuser@test.com'],
        ])

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, '-status', None, None)
        self.assertEqual(extract_keys(['account_id', 'name', 'status'], rows), [
            [1, 'test account 1', 1],
        ])

    def test_offset_limit(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.all()

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, 'name', 0, 1)

        self.assertEqual(extract_keys(['account_id', 'name'], rows), [
            [1, 'test account 1'],
        ])

        rows, _ = queries.query_accounts(accounts, sources, START_DATE, END_DATE, True, 'name', 1, 1)

        self.assertEqual(rows, [])


class QuerySourcesTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_sources(self):
        sources = models.Source.objects.all()
        ad_group_sources = models.AdGroupSource.objects.all()

        rows, _ = queries.query_sources(sources, ad_group_sources, START_DATE, END_DATE, True, '-name', None, None)

        self.assertEqual(extract_keys(['source_id', 'name', 'archived', 'maintenance'], rows), [
            [2, 'Gravity', False, False],
            [1, 'AdsNative', False, False],
        ])

    def test_order(self):
        sources = models.Source.objects.all()
        ad_group_sources = models.AdGroupSource.objects.all()

        rows, _ = queries.query_sources(sources, ad_group_sources, START_DATE, END_DATE, True, 'name', None, None)

        self.assertEqual(extract_keys(['source_id', 'name'], rows), [
            [1, 'AdsNative'],
            [2, 'Gravity'],
        ])

        rows, _ = queries.query_sources(sources, ad_group_sources, START_DATE, END_DATE, True, '-status', None, None)

        self.assertEqual(extract_keys(['source_id', 'name', 'status'], rows), [
            [2, 'Gravity', 2],
            [1, 'AdsNative', 1],
        ])

        rows, _ = queries.query_sources(sources, ad_group_sources, START_DATE, END_DATE, True, 'status', None, None)

        self.assertEqual(extract_keys(['source_id', 'name', 'status'], rows), [
            [1, 'AdsNative', 1],
            [2, 'Gravity', 2],
        ])

    def test_offset_limit(self):
        sources = models.Source.objects.all()
        ad_group_sources = models.AdGroupSource.objects.all()

        rows, _ = queries.query_sources(sources, ad_group_sources, START_DATE, END_DATE, True, 'name', 0, 1)

        self.assertEqual(extract_keys(['source_id', 'name'], rows), [
            [1, 'AdsNative'],
        ])
