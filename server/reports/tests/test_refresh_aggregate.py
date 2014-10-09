
from django import test
from django.db.models import Sum

from reports import refresh
from reports import models


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
