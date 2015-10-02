from mock import patch
import datetime

from django import test
from django.db.models import Sum

from reports import refresh
from reports import models

import dash.models

from utils import test_helper


@patch('reports.refresh.redshift')
class RefreshContentAdStats(test.TestCase):
    fixtures = ['test_api_contentads.yaml']

    def test_refresh_contentadstats(self, mock_redshift):
        date = datetime.datetime(2015, 2, 1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source.objects.get(pk=1)

        refresh.refresh_contentadstats(date, ad_group, source)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, ad_group.id, source.id)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 20, "ga__Goal 1": 10}',
            'cost_cc': 150000,
            'pageviews': 1500,
            'content_ad_id': 1,
            'new_visits': 100,
            'clicks': 100,
            'total_time_on_site': 60,
            'bounced_visits': 150,
            'visits': 1000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 1000000,
            'data_cost_cc': 150000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1
        }, {
            'conversions': '{}',
            'cost_cc': 250000,
            'pageviews': 2500,
            'content_ad_id': 2,
            'new_visits': 200,
            'clicks': 200,
            'total_time_on_site': 70,
            'bounced_visits': 250,
            'visits': 2000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 2000000,
            'data_cost_cc': 250000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1
        }]

        diff_rows = [{
            'cost_cc': -400000,
            'pageviews': -4000,
            'account_id': 1,
            'content_ad_id': -1,
            'new_visits': -300,
            'total_time_on_site': -130,
            'campaign_id': 1,
            'visits': -3000,
            'data_cost_cc': -400000,
            'bounced_visits': -400,
            'source_id': 1,
            'date': '2015-02-01',
            'impressions': -3000000,
            'clicks': -300,
            'adgroup_id': 1
        }]


        mock_redshift.insert_contentadstats.assert_has_call(test_helper.ListMatcher(rows))
        mock_redshift.insert_contentadstats.assert_any_call(diff_rows)

    def test_refresh_contentadstats_no_source_id(self, mock_redshift):
        date = datetime.datetime(2015, 2, 2)
        ad_group = dash.models.AdGroup.objects.get(pk=2)

        refresh.refresh_contentadstats(date, ad_group)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, ad_group.id, None)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 30}',
            'cost_cc': 550000,
            'pageviews': 4500,
            'content_ad_id': 3,
            'new_visits': 400,
            'clicks': 500,
            'total_time_on_site': 90,
            'bounced_visits': 450,
            'visits': 4000,
            'source_id': 2,
            'date': datetime.date(2015, 2, 2),
            'impressions': 5000000,
            'data_cost_cc': 550000,
            'adgroup_id': 2,
            'campaign_id': 1,
            'account_id': 1
        }, {
            'conversions': '{}',
            'cost_cc': 650000,
            'pageviews': None,
            'content_ad_id': 3,
            'new_visits': None,
            'clicks': 600,
            'total_time_on_site': None,
            'bounced_visits': None,
            'visits': None,
            'source_id': 1,
            'date': datetime.date(2015, 2, 2),
            'impressions': 6000000,
            'data_cost_cc': 650000,
            'adgroup_id': 2,
            'campaign_id': 1,
            'account_id': 1
        }]

        mock_redshift.insert_contentadstats.assert_called_with(test_helper.ListMatcher(rows))

    def test_refresh_contentadstats_missing_contentad_stats(self, mock_redshift):
        date = datetime.datetime(2015, 2, 2)
        ad_group = dash.models.AdGroup.objects.get(pk=3)
        source = dash.models.Source.objects.get(pk=1)

        refresh.refresh_contentadstats(date, ad_group, source)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, ad_group.id, source.id)

        rows = [{
            'conversions': '{}',
            'cost_cc': None,
            'pageviews': 5500,
            'content_ad_id': 4,
            'new_visits': 500,
            'clicks': None,
            'total_time_on_site': 90,
            'bounced_visits': 550,
            'visits': 5000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 2),
            'impressions': None,
            'data_cost_cc': None,
            'adgroup_id': 3,
            'campaign_id': 1,
            'account_id': 1
        }]

        mock_redshift.insert_contentadstats.assert_called_with(test_helper.ListMatcher(rows))


class RefreshAdGroupStatsTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def test_refresh_all(self):
        refresh.refresh_adgroup_stats()

        # totals are correct
        article_stats_totals = models.ArticleStats.objects.aggregate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        )
        adgroup_stats_totals = models.AdGroupStats.objects.aggregate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        )
        self.assertEqual(article_stats_totals, adgroup_stats_totals)

        # stats by ad_group are correct
        article_stats_by_adgroup = models.ArticleStats.objects.values(
            'ad_group'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('ad_group')
        adgroup_stats_by_adgroup = models.AdGroupStats.objects.values(
            'ad_group'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('ad_group')
        self.assertEqual(len(article_stats_by_adgroup), len(adgroup_stats_by_adgroup))
        for x, y in zip(article_stats_by_adgroup, adgroup_stats_by_adgroup):
            self.assertEqual(x, y)

        # stats by date are correct
        article_stats_by_date = models.ArticleStats.objects.values(
            'datetime'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('datetime')
        adgroup_stats_by_date = models.AdGroupStats.objects.values(
            'datetime'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('datetime')
        self.assertEqual(len(article_stats_by_date), len(adgroup_stats_by_date))
        for x, y in zip(article_stats_by_date, adgroup_stats_by_date):
            self.assertEqual(x, y)

    def test_refresh_subset(self):
        refresh.refresh_adgroup_stats()

        astat = models.ArticleStats.objects.get(pk=1)
        astat.impressions += 1
        astat.clicks += 1
        astat.cost_cc += 1
        astat.save()

        astat_other = models.ArticleStats.objects.get(pk=7)
        self.assertTrue(astat_other.ad_group.id != astat.ad_group.id)

        # not yet refreshed, there are some differences
        imps_article_stats = models.ArticleStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        imps_adgroup_stats = models.AdGroupStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        self.assertEqual(imps_adgroup_stats + 1, imps_article_stats)

        # refresh for a single ad group
        refresh.refresh_adgroup_stats(ad_group=astat.ad_group)

        # now there are no differences anymore
        imps_article_stats = models.ArticleStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        imps_adgroup_stats = models.AdGroupStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        self.assertEqual(imps_adgroup_stats, imps_article_stats)

    def test_cannot_refresh_invalid_constraints(self):
        with self.assertRaises(AssertionError):
            refresh.refresh_adgroup_stats(invalid_field='invalid value')
