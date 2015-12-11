from mock import patch
import datetime

from django import test
from django.db.models import Sum

from reports import refresh
import reports.models
import reports.update
from reports import constants
from reports import update

import dash.models

from convapi import parse_v2


class StatsUpdateTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

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
                       cost_cc=Sum('cost_cc'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'))
        self.assertEqual(article_stats_totals, adgroup_stats_totals)

        reports.update.stats_update_adgroup_source_traffic(
            datetime=dt,
            ad_group=ad_group,
            source=source,
            rows=[{
                'article': dash.models.Article.objects.get(pk=1),
                'impressions': 1000,
                'clicks': 11,
                'cost_cc': 9999
            }]
        )

        article_stats_totals = reports.models.ArticleStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'))
        expected = {'impressions': 1000, 'clicks': 11, 'cost_cc': 9999}
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
                       cost_cc=Sum('cost_cc'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group, source=source) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'))

        # Nothing changes
        expected = {'impressions': 1000, 'clicks': 11, 'cost_cc': 9999}
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
                       duration=Sum('duration'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration'))
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
                       duration=Sum('duration'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration'))
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
                       duration=Sum('duration'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration'))

        # Nothing changes
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
                       duration=Sum('duration'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration'))

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
                       duration=Sum('duration'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration'))
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
                       duration=Sum('duration'))
        adgroup_stats_totals = reports.models.AdGroupStats.objects \
            .filter(datetime=dt, ad_group=ad_group) \
            .aggregate(impressions=Sum('impressions'),
                       clicks=Sum('clicks'),
                       cost_cc=Sum('cost_cc'),
                       visits=Sum('visits'),
                       new_visits=Sum('new_visits'),
                       bounced_visits=Sum('bounced_visits'),
                       pageviews=Sum('pageviews'),
                       duration=Sum('duration'))

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


class DeleteOnEmptyReportTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats_empty_report.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

    def test_empty_with_flag(self):
        dt1 = datetime.datetime(2015, 4, 19)
        dt2 = datetime.datetime(2015, 4, 20)
        ad_group = dash.models.AdGroup.objects.get(id=1)
        source = dash.models.Source.objects.get(id=1)

        refresh.refresh_adgroup_stats(ad_group=ad_group, source=source)

        article_stats1 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in article_stats1), 8)
        self.assertEqual(sum(stat.impressions for stat in article_stats1), 6636)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats1), 16000)

        ad_group_stats1 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats1), 8)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats1), 6636)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats1), 16000)

        article_stats2 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in article_stats2), 12)
        self.assertEqual(sum(stat.impressions for stat in article_stats2), 5471)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats2), 36000)

        ad_group_stats2 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats2), 12)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats2), 5471)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats2), 36000)

        reports.update.stats_update_adgroup_source_traffic(dt1, ad_group, source, [])
        reports.update.stats_update_adgroup_source_traffic(dt2, ad_group, source, [])

        article_stats1 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in article_stats1), 0)
        self.assertEqual(sum(stat.impressions for stat in article_stats1), 0)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats1), 0)

        ad_group_stats1 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats1), 0)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats1), 0)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats1), 0)

        article_stats2 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in article_stats2), 12)
        self.assertEqual(sum(stat.impressions for stat in article_stats2), 5471)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats2), 36000)

        ad_group_stats2 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats2), 12)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats2), 5471)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats2), 36000)

    def test_empty_without_flag(self):
        dt1 = datetime.datetime(2015, 4, 19)
        dt2 = datetime.datetime(2015, 4, 20)
        ad_group = dash.models.AdGroup.objects.get(id=1)
        source = dash.models.Source.objects.get(id=2)

        refresh.refresh_adgroup_stats(ad_group=ad_group, source=source)

        article_stats1 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in article_stats1), 5)
        self.assertEqual(sum(stat.impressions for stat in article_stats1), 1530)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats1), 9500)

        ad_group_stats1 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats1), 5)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats1), 1530)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats1), 9500)

        article_stats2 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in article_stats2), 11)
        self.assertEqual(sum(stat.impressions for stat in article_stats2), 11361)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats2), 25000)

        ad_group_stats2 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats2), 11)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats2), 11361)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats2), 25000)

        reports.update.stats_update_adgroup_source_traffic(dt1, ad_group, source, [])
        reports.update.stats_update_adgroup_source_traffic(dt2, ad_group, source, [])

        article_stats1 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in article_stats1), 5)
        self.assertEqual(sum(stat.impressions for stat in article_stats1), 1530)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats1), 9500)

        ad_group_stats1 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt1)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats1), 5)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats1), 1530)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats1), 9500)

        article_stats2 = reports.models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in article_stats2), 11)
        self.assertEqual(sum(stat.impressions for stat in article_stats2), 11361)
        self.assertEqual(sum(stat.cost_cc for stat in article_stats2), 25000)

        ad_group_stats2 = reports.models.AdGroupStats.objects.filter(ad_group=ad_group, source=source, datetime=dt2)
        self.assertEqual(sum(stat.clicks for stat in ad_group_stats2), 11)
        self.assertEqual(sum(stat.impressions for stat in ad_group_stats2), 11361)
        self.assertEqual(sum(stat.cost_cc for stat in ad_group_stats2), 25000)


class ContentAdStatsUpdateTest(test.TestCase):
    fixtures = ['test_api.yaml']

    @patch('reports.refresh.notify_contentadstats_change')
    def test_update_content_ads_source_traffic_stats(self, mock_notify_contentadstats_change):
        date = datetime.date(2015, 4, 1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source.objects.get(pk=1)
        content_ad_source = dash.models.ContentAdSource.objects.get(pk=1)

        rows = [{
            'content_ad_source': content_ad_source,
            'id': 1,
            'impressions': 10000,
            'clicks': 100,
            'cost_cc': 300,
            'data_cost_cc': 200
        }]

        reports.update.update_content_ads_source_traffic_stats(date.isoformat(), ad_group, source, rows)

        stats = reports.models.ContentAdStats.objects.filter(content_ad_source=1, date=date)
        self.assertEqual(len(stats), 1)

        self.assertEqual(stats[0].impressions, 10000)
        self.assertEqual(stats[0].clicks, 100)
        self.assertEqual(stats[0].cost_cc, 300)
        self.assertEqual(stats[0].data_cost_cc, 200)
        mock_notify_contentadstats_change.assert_called_once_with(date, ad_group.campaign_id)


class GaContentAdReportTest(test.TransactionTestCase):
    fixtures = ['test_api_contentads']

    date = datetime.date(2015, 4, 16)

    sample_data = [
        parse_v2.GaReportRow(
            {
                "% New Sessions": "96.02%",
                "Avg. Session Duration": "00:00:12",
                "Bounce Rate": "92.41%",
                "Device Category": "mobile",
                "Landing Page": "/lasko?_z1_caid=1&_z1_msid=gravity",
                "New Users": "531",
                "Pages / Session": "1.12",
                "Sessions": "553",
                "Yell Free Listings (Goal 1 Completions)": "0",
                "Yell Free Listings (Goal 1 Conversion Rate)": "0.00%",
                "Yell Free Listings (Goal 1 Value)": "\u00a30.00",
            },
            datetime.date(2015, 4, 16),
            1,
            "gravity",
            {
                "Goal 1": 0,
            }
        ),
        parse_v2.GaReportRow(
            {
                "% New Sessions": "96.02%",
                "Avg. Session Duration": "00:00:12",
                "Bounce Rate": "92.41%",
                "Device Category": "mobile",
                "Landing Page": "/lasko?_z1_caid=1&_z1_msid=gravity",
                "New Users": "531",
                "Pages / Session": "1.12",
                "Sessions": "553",
                "Yell Free Listings (Goal 1 Completions)": "0",
                "Yell Free Listings (Goal 1 Conversion Rate)": "0.00%",
                "Yell Free Listings (Goal 1 Value)": "\u00a30.00",
            },
            datetime.date(2015, 4, 16),
            3,
            "gravity",
            {
                "Goal 1": 0,
            }
        )
    ]

    sample_invalid_data_1 = [
        parse_v2.GaReportRow(
            {
                "% New Sessions": "96.02%",
                "Avg. Session Duration": "00:00:12",
                "Bounce Rate": "92.41%",
                "Device Category": "mobile",
                "Landing Page": "/lasko?_z1_caid=12345&_z1_msid=gravity",
                "New Users": "531",
                "Pages / Session": "1.12",
                "Sessions": "553",
                "Yell Free Listings (Goal 1 Completions)": "0",
                "Yell Free Listings (Goal 1 Conversion Rate)": "0.00%",
                "Yell Free Listings (Goal 1 Value)": "\u00a30.00",
            },
            datetime.date(2015, 4, 16),
            12345,
            "gravity",
            {
                "Goal 1": 0,
            }
        )
    ]

    @patch('reports.refresh.notify_contentadstats_change')
    def test_correct_row(self, mock_notify_contentadstats_change):
        self.assertEqual(6, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(3, reports.models.ContentAdGoalConversionStats.objects.count())

        update.process_report(self.date, self.sample_data, constants.ReportType.GOOGLE_ANALYTICS)

        self.assertEqual(8, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(5, reports.models.ContentAdGoalConversionStats.objects.count())
        self.assertTrue(mock_notify_contentadstats_change.called)

    @patch('reports.refresh.notify_contentadstats_change')
    def test_double_correct_row(self, mock_notify_contentadstats_change):
        self.assertEqual(6, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(3, reports.models.ContentAdGoalConversionStats.objects.count())

        update.process_report(self.date, self.sample_data, constants.ReportType.GOOGLE_ANALYTICS)
        update.process_report(self.date, self.sample_data, constants.ReportType.GOOGLE_ANALYTICS)

        self.assertEqual(8, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(5, reports.models.ContentAdGoalConversionStats.objects.count())
        self.assertTrue(mock_notify_contentadstats_change.called)

    def test_invalid_caid(self):
        self.assertEqual(6, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(3, reports.models.ContentAdGoalConversionStats.objects.count())

        with self.assertRaises(Exception):
            update.process_report(self.date, self.sample_invalid_data_1, constants.ReportType.GOOGLE_ANALYTICS)

        self.assertEqual(6, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(3, reports.models.ContentAdGoalConversionStats.objects.count())
