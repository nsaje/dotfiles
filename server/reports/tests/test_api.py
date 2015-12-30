import datetime

from django import test
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from mock import patch
from collections import Sequence

from dash import models as dashmodels
from dash import api as dashapi
from dash import exc as dashexc
from reports import api
from reports import models
from reports import refresh
from reports import exc as repsexc
from utils.test_helper import dicts_match_for_keys, sequence_of_dicts_match_for_keys
from utils.url_helper import clean_url

from zweiapi.views import _prepare_report_rows, _remove_content_ad_sources_from_report_rows

import reports.update
import utils.pagination


class QueryTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

        refresh.refresh_adgroup_stats()

    def test_date_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'ctr': 1.65145588874402,
            'cpc': 0.0501,
            'cost': 1.9043,
            'data_cost': 0.04,
            'date': datetime.date(2014, 6, 4),
            'impressions': 2301,
            'clicks': 38
        }, {
            'ctr': 1.14777618364419,
            'cpc': 0.0340,
            'cost': 0.5441,
            'data_cost': 0.02,
            'date': datetime.date(2014, 6, 5),
            'impressions': 1394,
            'clicks': 16
        }, {
            'ctr': 1.04257167680278,
            'cpc': 0.0544,
            'cost': 1.3058,
            'data_cost': 0.115,
            'date': datetime.date(2014, 6, 6),
            'impressions': 2302,
            'clicks': 24
        }]

        result = api.query(start, end, ['date'], ['date'], ad_group=1)

        self.assertTrue(sequence_of_dicts_match_for_keys(result, expected, expected[0].keys()))

    def test_breakdown_copy(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        breakdown = ['date', 'source']
        api.query(start, end, breakdown, ad_group=1)
        self.assertEqual(breakdown, ['date', 'source'])

    def test_non_exisiting_date_breakdown(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        result = api.query(start, end, ['date'], ad_group=1)

        self.assertEqual(result, [])

    def test_non_exisiting_date_totals_breakdown(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        expected = {
            'clicks': None,
            'cost': None,
            'data_cost': None,
            'cpc': None,
            'ctr': None,
            'impressions': None
        }

        result = api.query(start, end, [], ad_group=1)

        self.assertTrue(dicts_match_for_keys(result, expected, expected.keys()))

    def test_source_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = {
            'source': 1,
            'ctr': 1.3006503251625798,
            'cpc': 0.0481,
            'cost': 3.7542,
            'data_cost': 0.175,
            'impressions': 5997,
            'clicks': 78
        }
        result = api.query(start, end, ['source'], ad_group=1)[0]

        self.assertTrue(dicts_match_for_keys(result, expected, expected.keys()))

    def test_totals_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = {
            'impressions': 5997,
            'cost': 3.7542,
            'data_cost': 0.175,
            'clicks': 78,
            'ctr': 1.3006503251625798,
            'cpc': 0.0481
        }

        result = api.query(start, end, [], ad_group=1)
        

        self.assertTrue(dicts_match_for_keys(result, expected, expected.keys()))

    def test_list_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        expected = [{
            'ctr': 1.66139240506329,
            'cpc': 0.0544,
            'cost': 1.1426,
            'data_cost': 0.01,
            'impressions': 1264,
            'date': datetime.date(2014, 6, 4),
            'article': 1,
            'clicks': 21,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }, {
            'ctr': 1.63934426229508,
            'cpc': 0.0448,
            'cost': 0.7617,
            'data_cost': 0.03,
            'impressions': 1037,
            'date': datetime.date(2014, 6, 4),
            'article': 2,
            'clicks': 17,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'data_cost': 0.02,
            'impressions': 178,
            'date': datetime.date(2014, 6, 5),
            'article': 1,
            'clicks': 0,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }, {
            'ctr': 1.31578947368421,
            'cpc': 0.0340,
            'cost': 0.5441,
            'data_cost': 0.0,
            'impressions': 1216,
            'date': datetime.date(2014, 6, 5),
            'article': 2,
            'clicks': 16,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }]

        result = api.query(start, end, ['date', 'article'], ['date', 'article'], ad_group=1)

        self.assertTrue(sequence_of_dicts_match_for_keys(result, expected, expected[0].keys()))

    def test_list_constraints(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'ctr': 1.24204786428355,
            'cpc': 0.0544,
            'cost': 2.2308,
            'data_cost': 0.13,
            'impressions': 3301,
            'article': 1,
            'clicks': 41,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }, {
            'ctr': 1.37240356083086,
            'cpc': 0.0412,
            'cost': 1.5234,
            'data_cost': 0.045,
            'impressions': 2696,
            'article': 2,
            'clicks': 37,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }, {
            'ctr': 1.3417759686416402,
            'cpc': 0.0544,
            'cost': 4.8425,
            'data_cost': 0.32,
            'impressions': 6633,
            'article': 3,
            'clicks': 89,
            'title': 'Test Article 3',
            'url': 'http://test3.com'
        }, {
            'ctr': 1.2448132780083,
            'cpc': 0.0544,
            'cost': 3.2645,
            'data_cost': 0.32,
            'impressions': 4820,
            'article': 4,
            'clicks': 60,
            'title': 'Test Article 4',
            'url': 'http://test4.com'
        }]

        result = api.query(start, end, ['article'], ['article'], article=[1, 2, 3, 4, 5])

        self.assertTrue(sequence_of_dicts_match_for_keys(result, expected, expected[0].keys()))

    def test_invalid_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        self.assertRaises(
            repsexc.ReportsQueryError,
            api.query,
            start,
            end,
            ['impressions'],
            ad_group=1
        )

        self.assertRaises(
            repsexc.ReportsQueryError,
            api.query,
            start,
            end,
            ['date', 'impressions'],
            ad_group=1
        )

    def test_order(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        expected = [{
            'ctr': 1.31578947368421,
            'cpc': 0.0340,
            'cost': 0.5441,
            'data_cost': 0.0,
            'impressions': 1216,
            'date': datetime.date(2014, 6, 5),
            'article': 2,
            'clicks': 16,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }, {
            'ctr': 1.63934426229508,
            'cpc': 0.0448,
            'cost': 0.7617,
            'data_cost': 0.03,
            'impressions': 1037,
            'date': datetime.date(2014, 6, 4),
            'article': 2,
            'clicks': 17,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }, {
            'ctr': 1.66139240506329,
            'cpc': 0.0544,
            'cost': 1.1426,
            'data_cost': 0.01,
            'impressions': 1264,
            'date': datetime.date(2014, 6, 4),
            'article': 1,
            'clicks': 21,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'data_cost': 0.02,
            'impressions': 178,
            'date': datetime.date(2014, 6, 5),
            'article': 1,
            'clicks': 0,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }]

        result = api.query(start, end, ['date', 'article'], order=['cpc'], ad_group=1)
        self.assertTrue(sequence_of_dicts_match_for_keys(result, expected, expected[0].keys()))

        result = api.query(start, end, ['date', 'article'], order=['-cpc'], ad_group=1)

        desc_expected = [expected[2], expected[1], expected[0], expected[3]]
        self.assertTrue(sequence_of_dicts_match_for_keys(result, desc_expected, desc_expected[0].keys()))

    def test_pagination(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        expected = [{
            'ctr': 1.31578947368421,
            'cpc': 0.0340,
            'cost': 0.5441,
            'data_cost': 0.0,
            'impressions': 1216,
            'date': datetime.date(2014, 6, 5),
            'article': 2,
            'clicks': 16,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }, {
            'ctr': 1.63934426229508,
            'cpc': 0.0448,
            'cost': 0.7617,
            'data_cost': 0.03,
            'impressions': 1037,
            'date': datetime.date(2014, 6, 4),
            'article': 2,
            'clicks': 17,
            'title': 'Test Article 2',
            'url': 'http://test2.com'
        }]

        result = utils.pagination.paginate(api.query(
            start,
            end,
            ['date', 'article'],
            order=['cpc'],
            ad_group=1
        ), 1, 2)

        rows = result[0]
        self.assertTrue(sequence_of_dicts_match_for_keys(rows, expected, expected[0].keys()))
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 1)
        self.assertEqual(result[5], 2)

        expected = [{
            'ctr': 1.66139240506329,
            'cpc': 0.0544,
            'cost': 1.1426,
            'data_cost': 0.01,
            'impressions': 1264,
            'date': datetime.date(2014, 6, 4),
            'article': 1,
            'clicks': 21,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'data_cost': 0.02,
            'impressions': 178,
            'date': datetime.date(2014, 6, 5),
            'article': 1,
            'clicks': 0,
            'title': 'Test Article 1',
            'url': 'http://test1.com'
        }]

        result = utils.pagination.paginate(api.query(
            start,
            end,
            ['date', 'article'],
            order=['cpc'],
            ad_group=1
        ), 2, 2)
        rows = result[0]
        self.assertTrue(sequence_of_dicts_match_for_keys(rows, expected, expected[0].keys()))
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 3)
        self.assertEqual(result[5], 4)

        # Should be the same page as page 2
        result = utils.pagination.paginate(api.query(
            start,
            end,
            ['date', 'article'],
            order=['cpc'],
            ad_group=1
        ), 3, 2)
        rows = result[0]
        self.assertTrue(sequence_of_dicts_match_for_keys(rows, expected, expected[0].keys()))
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 3)
        self.assertEqual(result[5], 4)

    def test_return_type(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        result = api.query(start, end, ['article'], ['clicks'], ad_group=1)
        self.assertEqual(isinstance(result, Sequence), True)

        result = api.query(start, end, ['source'], ['clicks'], ad_group=1)
        self.assertEqual(isinstance(result, Sequence), True)


class YesterdayCostTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

        refresh.refresh_adgroup_stats()

    @patch('reports.api.datetime')
    def test_get_yesterday_cost(self, datetime_mock):
        class DatetimeMock(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return datetime.datetime(2014, 6, 5, 13, 22, 23)

        datetime_mock.datetime = DatetimeMock
        datetime_mock.timedelta = datetime.timedelta

        result = api.get_yesterday_cost(dict(ad_group=1))
        self.assertEqual(result, {1: 1.9043})

    @patch('reports.api.datetime')
    def test_non_existing_yesterday_cost(self, datetime_mock):
        class DatetimeMock(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return datetime.datetime(2014, 6, 10, 13, 22, 23)

        datetime_mock.datetime = DatetimeMock
        datetime_mock.timedelta = datetime.timedelta

        result = api.get_yesterday_cost(dict(ad_group=1))
        self.assertEqual(result, {})


class ApiTestCase(test.TestCase):

    def test_clean_url(self):

        url_normal = 'http://sd.domain.com/path/to?attr1=1&attr1=123i&attr2=#uff'
        self.assertEqual(url_normal, clean_url(url_normal)[0])

        url_unsorted = 'http://sd.domain.com/path/to?attr1=1&attr2=&attr1=123i#uff'
        url_unsorted_cleaned = 'http://sd.domain.com/path/to?attr1=1&attr1=123i&attr2=#uff'
        self.assertEqual(url_unsorted_cleaned, clean_url(url_unsorted)[0])

        url_with_utm = 'http://sd.domain.com/path/to?attr1=1&utm_source=abc'
        url_with_utm_cleaned = 'http://sd.domain.com/path/to?attr1=1'
        self.assertEqual(url_with_utm_cleaned, clean_url(url_with_utm)[0])

        url_with_z1 = 'http://sd.domain.com/path/to?attr1=1&_z1_xyz=abc'
        url_with_z1_cleaned = 'http://sd.domain.com/path/to?attr1=1'
        self.assertEqual(url_with_z1_cleaned, clean_url(url_with_z1)[0])

        url_unsorted_with_z1_utm = 'http://sd.domain.com/path/to?attr2=2&attr1=1&_z1_xyz=abc&utm_source=abc#uff'
        url_unsorted_with_z1_utm_cleaned = 'http://sd.domain.com/path/to?attr1=1&attr2=2#uff'
        self.assertEqual(url_unsorted_with_z1_utm_cleaned, clean_url(url_unsorted_with_z1_utm)[0])

        url_with_utf8_param = u'http://sd.domain.com/path/to?attr1=%e2%80%99'
        self.assertEqual(url_with_utf8_param.lower(), clean_url(url_with_utf8_param)[0].lower())


class UpsertReportsTestCase(test.TestCase):

    fixtures = ['test_reports_base.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

    def test_save_reports(self):
        date1 = datetime.date(2014, 7, 1)
        date2 = datetime.date(2014, 7, 2)

        ags1 = dashmodels.AdGroupSource.objects.get(id=1)
        rows_ags1_date1 = [
            {
                'id': 's1',
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
            },
            {
                'id': 's2',
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
            },
        ]
        rows_ags2_date1 = [
            {
                'id': 's4',
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
            },
            {
                'id': 's5',
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
            },
        ]

        ags2 = dashmodels.AdGroupSource.objects.get(id=2)
        rows_ags1_date2 = [
            {
                'id': 's1',
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
            },
            {
                'id': 's2',
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
            },
        ]
        rows_ags2_date2 = [
            {
                'id': 's4',
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
            },
            {
                'id': 's5',
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 1800,
            },
        ]

        self.assertTrue(models.ArticleStats.objects.count() == 0)
        self.assertTrue(models.AdGroupStats.objects.count() == 0)

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date1,
            ad_group=ags1.ad_group,
            source=ags1.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags1.ad_group, ags1, ags1.source, rows_ags1_date1))
        )

        for row in rows_ags1_date1:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'])
            stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags1.ad_group,
                source=ags1.source,
                datetime=date1
            )
            self.assertEqual(stats.impressions, row['impressions'])
            self.assertEqual(stats.clicks, row['clicks'])
            self.assertEqual(stats.cost_cc, row['cost_cc'])

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date1,
            ad_group=ags2.ad_group,
            source=ags2.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags2.ad_group, ags2, ags2.source, rows_ags2_date1))
        )
        for row in rows_ags2_date1:
            article = dashmodels.Article.objects.get(title=row['title'])
            stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags2.ad_group,
                source=ags2.source,
                datetime=date1
            )
            self.assertEqual(stats.impressions, row['impressions'])
            self.assertEqual(stats.clicks, row['clicks'])
            self.assertEqual(stats.cost_cc, row['cost_cc'])

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date2,
            ad_group=ags1.ad_group,
            source=ags1.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags1.ad_group, ags1, ags1.source, rows_ags1_date2))
        )
        reports.update.stats_update_adgroup_source_traffic(
            datetime=date2,
            ad_group=ags2.ad_group,
            source=ags2.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags2.ad_group, ags2, ags2.source, rows_ags2_date2))
        )

        articles_ags1 = dashmodels.Article.objects.order_by('title')
        articles_ags2 = dashmodels.Article.objects.order_by('title')

        self.assertEqual(len(articles_ags1), 2)
        self.assertEqual(len(articles_ags2), 2)

        for article1, article2 in zip(articles_ags1, articles_ags2):
            self.assertEqual(article1, article2)

    def test_save_reports_reinsert(self):
        rows = [
            {
                'id': 's1',
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
            },
            {
                'id': 's2',
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
                'cpc_cc': None
            },
        ]

        rows_new_title = [
            {
                'id': 's1',
                'title': 'Test Article 1 New',
                'url': 'http://example.com/',
                'impressions': 100,
                'clicks': 4,
                'cost_cc': 5600,
                'cpc_cc': None
            },
            {
                'id': 's2',
                'title': 'Test Article 2 New',
                'url': 'http://example.com/',
                'impressions': 80,
                'clicks': 2,
                'cost_cc': 1800,
                'cpc_cc': None
            },
        ]

        rows_new_url = [
            {
                'id': 's1',
                'title': 'Test Article 1 New',
                'url': 'http://example.com/new',
                'impressions': 200,
                'clicks': 8,
                'cost_cc': 11200,
                'cpc_cc': None
            },
            {
                'id': 's2',
                'title': 'Test Article 2 New',
                'url': 'http://example.com/new',
                'impressions': 160,
                'clicks': 4,
                'cost_cc': 3600,
                'cpc_cc': None
            },
        ]

        ags = dashmodels.AdGroupSource.objects.get(id=1)
        date = datetime.date(2014, 7, 10)

        stats = models.ArticleStats.objects.filter(ad_group=ags.ad_group, source=ags.source, datetime=date)
        self.assertEqual(len(stats), 0)

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date,
            ad_group=ags.ad_group,
            source=ags.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags.ad_group, ags, ags.source, rows))
        )
        stats = models.ArticleStats.objects.filter(ad_group=ags.ad_group, source=ags.source, datetime=date)
        self.assertEqual(len(stats), 2)
        for row in rows:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=ags.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags.ad_group,
                source=ags.source,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, row['impressions'])
            self.assertEqual(article_stats.clicks, row['clicks'])
            self.assertEqual(article_stats.cost_cc, row['cost_cc'])
            self.assertEqual(article_stats.has_traffic_metrics, 1)

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date,
            ad_group=ags.ad_group,
            source=ags.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags.ad_group, ags, ags.source, rows_new_title))
        )
        stats = models.ArticleStats.objects.filter(ad_group=ags.ad_group, source=ags.source, datetime=date)
        self.assertEqual(len(stats), 4)
        for row in rows_new_title:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=ags.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags.ad_group,
                source=ags.source,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, row['impressions'])
            self.assertEqual(article_stats.clicks, row['clicks'])
            self.assertEqual(article_stats.cost_cc, row['cost_cc'])
            self.assertEqual(article_stats.has_traffic_metrics, 1)

        # make sure the metrics for the articles inserted before are reset
        for row in rows:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=ags.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags.ad_group,
                source=ags.source,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, 0)
            self.assertEqual(article_stats.clicks, 0)
            self.assertEqual(article_stats.cost_cc, 0)
            self.assertEqual(article_stats.data_cost_cc, 0)
            self.assertEqual(article_stats.has_traffic_metrics, 0)

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date,
            ad_group=ags.ad_group,
            source=ags.source,
            rows=_remove_content_ad_sources_from_report_rows(_prepare_report_rows(
                ags.ad_group, ags, ags.source, rows_new_url))
        )
        stats = models.ArticleStats.objects.filter(ad_group=ags.ad_group, source=ags.source, datetime=date)
        self.assertEqual(len(stats), 6)
        for row in rows_new_url:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=ags.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags.ad_group,
                source=ags.source,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, row['impressions'])
            self.assertEqual(article_stats.clicks, row['clicks'])
            self.assertEqual(article_stats.cost_cc, row['cost_cc'])
            self.assertEqual(article_stats.has_traffic_metrics, 1)

        # make sure the metrics for the articles inserted before are reset
        for row in rows + rows_new_title:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=ags.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=ags.ad_group,
                source=ags.source,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, 0)
            self.assertEqual(article_stats.clicks, 0)
            self.assertEqual(article_stats.cost_cc, 0)
            self.assertEqual(article_stats.has_traffic_metrics, 0)

    def test_save_reports_duplicate(self):
        date1 = datetime.date(2014, 7, 10)

        ags1 = dashmodels.AdGroupSource.objects.get(id=1)

        title, url = 'Test Article 1', 'http://example.com/'
        title_other, url_other = 'Test Article 2', 'http://example.com/'

        rows_duplicate = [
            {
                'id': 's1',
                'title': title,
                'url': url,
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
                'cpc_cc': None
            },
            {
                'id': 's1',
                'title': title,
                'url': url,
                'impressions': 30,
                'clicks': 3,
                'cost_cc': 2200,
                'cpc_cc': None
            },
            {
                'id': 's1',
                'title': title,
                'url': url,
                'impressions': 40,
                'clicks': 7,
                'cost_cc': 3000,
                'cpc_cc': None
            },
        ]

        rows_other = [
            {
                'id': 's2',
                'title': title_other,
                'url': url_other,
                'impressions': 100,
                'clicks': 5,
                'cost_cc': 4444,
                'cpc_cc': None
            }
        ]

        rows = rows_duplicate + rows_other

        reports.update.stats_update_adgroup_source_traffic(
            datetime=date1,
            ad_group=ags1.ad_group,
            source=ags1.source,
            rows=_remove_content_ad_sources_from_report_rows(
                _prepare_report_rows(ags1.ad_group, ags1, ags1.source, rows))
        )

        article = dashmodels.Article.objects.get(title=title, url=url)
        stats = models.ArticleStats.objects.get(
            article=article,
            ad_group=ags1.ad_group,
            source=ags1.source,
            datetime=date1
        )

        article_other = dashmodels.Article.objects.get(title=title_other, url=url_other)
        stats_other = models.ArticleStats.objects.get(
            article=article_other,
            ad_group=ags1.ad_group,
            source=ags1.source,
            datetime=date1
        )

        self.assertEqual(stats.impressions, sum(r['impressions'] for r in rows_duplicate))
        self.assertEqual(stats.clicks, sum(r['clicks'] for r in rows_duplicate))
        self.assertEqual(stats.cost_cc, sum(r['cost_cc'] for r in rows_duplicate))

        self.assertEqual(stats_other.impressions, rows_other[0]['impressions'])
        self.assertEqual(stats_other.clicks, rows_other[0]['clicks'])
        self.assertEqual(stats_other.cost_cc, rows_other[0]['cost_cc'])


class ArticleReconciliationTestCase(test.TestCase):

    def _mocked_create(url, title, ad_group):
        dashmodels.Article(url=url, title=title, ad_group=ad_group).save()
        raise IntegrityError

    @patch('dash.models.Article.objects.create', _mocked_create)
    @patch('dash.api.transaction.atomic')
    def test_retry_on_integrity_error(self, atomic_mock):
        ad_group = dashmodels.AdGroup(id=1)
        raw_url = 'http://sd.domain.com/path/to'
        title = 'Example title'

        self.assertSequenceEqual(dashmodels.Article.objects.all(), [])
        dashapi.reconcile_articles(ad_group, [{'url': raw_url, 'title': title}])

    def test_reconcile_article(self):
        ad_group = dashmodels.AdGroup(id=1)
        raw_url = 'http://sd.domain.com/path/to'
        title = 'Five article titles you would never believe to exist'

        with self.assertRaises(dashexc.ArticleReconciliationException):
            dashapi.reconcile_articles(None, [{'url': raw_url, 'title': title}])

        with self.assertRaises(dashexc.ArticleReconciliationException):
            dashapi.reconcile_articles(ad_group, [{'url': raw_url, 'title': None}])

        with self.assertRaises(dashexc.ArticleReconciliationException):
            dashapi.reconcile_articles(ad_group, [{'url': None, 'title': title}])

        cleaned_url, _ = clean_url(raw_url)
        with self.assertRaises(ObjectDoesNotExist):
            dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)

        articles = dashapi.reconcile_articles(ad_group, [{'url': raw_url, 'title': title}])

        db_article = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)
        self.assertEqual(articles[0], db_article)

        same_articles = dashapi.reconcile_articles(ad_group, [{'url': raw_url, 'title': title}])
        self.assertEqual(articles[0], same_articles[0])


class PrepareReportRowsTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def test_filter_by_content_ad_sources(self):
        data_rows = [
            {
                'title': 'Test Article 1',
                'url': 'http://test1.com',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
                'cpc_cc': None,
                'id': 's1'
            },
            {
                # matching content_ad is archived
                'title': 'Test Article 2',
                'url': 'http://test2.com',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
                'cpc_cc': None,
                'id': 's2'
            },
        ]

        ad_group = dashmodels.AdGroup.objects.get(pk=1)
        source = dashmodels.Source.objects.get(pk=1)
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)
        ad_group_source.can_manage_content_ads = True

        report_rows = _prepare_report_rows(ad_group, ad_group_source, source, data_rows)

        article1 = dashmodels.Article.objects.get(pk=1)
        article2 = dashmodels.Article.objects.get(pk=2)
        content_ad_source1 = dashmodels.ContentAdSource.objects.get(pk=1)
        content_ad_source2 = dashmodels.ContentAdSource.objects.get(pk=2)

        self.assertItemsEqual(report_rows, [{
            'article': article1,
            'content_ad_source': content_ad_source1,
            'id': 's1',
            'clicks': 2,
            'data_cost_cc': 0,
            'impressions': 50,
            'cost_cc': 2800,
        }, {
            'article': article2,
            'content_ad_source': content_ad_source2,
            'impressions': 40,
            'clicks': 1,
            'cost_cc': 900,
            'data_cost_cc': 0,
            'id': 's2'
        }])

        article_rows = _remove_content_ad_sources_from_report_rows(report_rows)
        self.assertItemsEqual(article_rows, [{
            'article': article1,
            'clicks': 2,
            'data_cost_cc': 0,
            'impressions': 50,
            'cost_cc': 2800
        }, {
            'article': article2,
            'impressions': 40,
            'clicks': 1,
            'cost_cc': 900,
            'data_cost_cc': 0,
        }])
