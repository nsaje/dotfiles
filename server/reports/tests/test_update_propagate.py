import datetime

from django import test
from django.db.models import Sum

from reports import refresh

import reports.models
import dash.models
import reports.update


class StatsUpdateTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    def test_update_adgroup_source_traffic(self):
        dt = datetime.date(2014, 6, 4)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source.objects.get(pk=1)

        # before update
        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc')
            )
        self.assertEqual(article_stats_totals, adgroup_stats_totals)

        reports.update.stats_update_adgroup_source_traffic(
            datetime=dt,
            ad_group=ad_group,
            source=source,
            rows=[{
                'article': dash.models.Article.objects.get(pk=1),
                'impressions': 1000,
                'clicks': 10,
                'cost_cc': 9999
            }]
        )

        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc')
            )
        expected = {'impressions': 1000, 'clicks': 10, 'cost_cc': 9999}
        self.assertEqual(article_stats_totals, expected)
        self.assertEqual(adgroup_stats_totals, expected)

        # update with empty rows
        reports.update.stats_update_adgroup_source_traffic(
            datetime=dt,
            ad_group=ad_group,
            source=source,
            rows=[]
        )
        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc')
            )

        # Nothing changes
        expected = {'impressions': 1000, 'clicks': 10, 'cost_cc': 9999}
        self.assertEqual(article_stats_totals, expected)
        self.assertEqual(adgroup_stats_totals, expected)

    def test_update_adgroup_postclick(self):
        dt = datetime.date(2014, 6, 4)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source.objects.get(pk=1)

        # before update
        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        self.assertEqual(article_stats_totals, adgroup_stats_totals)

        reports.update.stats_update_adgroup_postclick(
            datetime=dt,
            ad_group=ad_group,
            rows=[{
                'article': dash.models.Article.objects.get(pk=1),
                'source': source,
                'visits': 1000,
                'new_visits': 900,
                'bounced_visits': 800,
                'pageviews': 2000,
                'duration': 1234
            }]
        )

        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        expected = {
            'visits': 1000,
            'new_visits': 900,
            'bounced_visits': 800,
            'pageviews': 2000,
            'duration': 1234
        }
        self.assertEqual(article_stats_totals, expected)
        self.assertEqual(adgroup_stats_totals, expected)

        # Update with empty rows
        reports.update.stats_update_adgroup_postclick(
            datetime=dt,
            ad_group=ad_group,
            rows=[]
        )

        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )

        #Nothing changes
        expected = {
            'visits': 1000,
            'new_visits': 900,
            'bounced_visits': 800,
            'pageviews': 2000,
            'duration': 1234
        }
        self.assertEqual(article_stats_totals, expected)
        self.assertEqual(adgroup_stats_totals, expected)

    def test_update_adgroup_all(self):
        dt = datetime.date(2014, 6, 4)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source.objects.get(pk=1)

        # before update
        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )

        self.assertEqual(article_stats_totals, adgroup_stats_totals)

        reports.update.stats_update_adgroup_all(
            datetime=dt,
            ad_group=ad_group,
            rows=[{
                'article': dash.models.Article.objects.get(pk=1),
                'source': source,
                'impressions': 20000,
                'clicks': 1500,
                'cost_cc': 7654321,
                'visits': 1000,
                'new_visits': 900,
                'bounced_visits': 800,
                'pageviews': 2000,
                'duration': 1234
            }]
        )

        # after update
        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        expected = {
            'impressions': 20000,
            'clicks': 1500,
            'cost_cc': 7654321,
            'visits': 1000,
            'new_visits': 900,
            'bounced_visits': 800,
            'pageviews': 2000,
            'duration': 1234
        }
        self.assertEqual(article_stats_totals, expected)
        self.assertEqual(adgroup_stats_totals, expected)

        # update with empty rows
        reports.update.stats_update_adgroup_all(
            datetime=dt,
            ad_group=ad_group,
            rows=[]
        )

        # after update
        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration')
            )

        # Nothing changes
        expected = {
            'impressions': 20000,
            'clicks': 1500,
            'cost_cc': 7654321,
            'visits': 1000,
            'new_visits': 900,
            'bounced_visits': 800,
            'pageviews': 2000,
            'duration': 1234
        }
        self.assertEqual(article_stats_totals, expected)
        self.assertEqual(adgroup_stats_totals, expected)


class ContentAdStatsUpdateTest(test.TestCase):
    fixtures = ['test_api.yaml']

    def test_update_content_ads_source_traffic_stats(self):
        date = datetime.date(2015, 4, 1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source.objects.get(pk=1)

        rows = [{
            'id': 1,
            'impressions': 10000,
            'clicks': 100,
            'cost_cc': 300,
            'data_cost_cc': 200
        }]

        reports.update.update_content_ads_source_traffic_stats(date, ad_group, source, rows)

        stats = reports.models.ContentAdStats.objects.filter(content_ad_source=1, date=date)
        self.assertEqual(len(stats), 1)

        self.assertEqual(stats[0].impressions, 10000)
        self.assertEqual(stats[0].clicks, 100)
        self.assertEqual(stats[0].cost_cc, 300)
        self.assertEqual(stats[0].data_cost_cc, 200)
