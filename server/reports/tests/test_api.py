import datetime

from django import test
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from mock import patch

from dash import models as dashmodels
from reports import api
from reports import exc
from reports import models


class QueryTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def test_date_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'ctr': 1.65145588874402,
            'cpc': 0.0501131578947368,
            'cost': 1.9043,
            'date': datetime.date(2014, 6, 4),
            'impressions': 2301,
            'clicks': 38
        }, {
            'ctr': 1.14777618364419,
            'cpc': 0.03400625,
            'cost': 0.5441,
            'date': datetime.date(2014, 6, 5),
            'impressions': 1394,
            'clicks': 16
        }, {
            'ctr': 1.04257167680278,
            'cpc': 0.0544083333333333,
            'cost': 1.3058,
            'date': datetime.date(2014, 6, 6),
            'impressions': 2302,
            'clicks': 24
        }]

        result = api.query(start, end, ['date'], ad_group=1)[0]

        self.assertEqual(result, expected)

    def test_breakdown_copy(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        breakdown = ['date', 'source']
        api.query(start, end, breakdown, ad_group=1)[0]
        self.assertEqual(breakdown, ['date', 'source'])

    def test_non_exisiting_date_breakdown(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        result = api.query(start, end, ['date'], ad_group=1)[0]

        self.assertEqual(result, [])

    def test_non_exisiting_date_totals_breakdown(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        expected = [{
            'clicks': None,
            'cost': None,
            'cpc': None,
            'ctr': None,
            'impressions': None
        }]

        result = api.query(start, end, [], ad_group=1)[0]

        self.assertEqual(result, expected)

    def test_source_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'source': 1,
            'ctr': 1.3006503251625798,
            'cpc': 0.0481307692307692,
            'cost': 3.7542,
            'impressions': 5997,
            'clicks': 78
        }]

        result = api.query(start, end, ['source'], ad_group=1)[0]

        self.assertEqual(result, expected)

    def test_totals_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'impressions': 5997,
            'cost': 3.7542,
            'clicks': 78,
            'ctr': 1.3006503251625798,
            'cpc': 0.0481307692307692
        }]

        result = api.query(start, end, [], ad_group=1)[0]

        self.assertEqual(result, expected)

    def test_list_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        expected = [{
            'ctr': 1.66139240506329,
            'cpc': 0.054409523809523797,
            'cost': 1.1426,
            'impressions': 1264,
            'date': datetime.date(2014, 6, 4),
            'article': 1,
            'clicks': 21
        }, {
            'ctr': 1.63934426229508,
            'cpc': 0.0448058823529412,
            'cost': 0.7617,
            'impressions': 1037,
            'date': datetime.date(2014, 6, 4),
            'article': 2,
            'clicks': 17
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'impressions': 178,
            'date': datetime.date(2014, 6, 5),
            'article': 1,
            'clicks': 0
        }, {
            'ctr': 1.31578947368421,
            'cpc': 0.03400625,
            'cost': 0.5441,
            'impressions': 1216,
            'date': datetime.date(2014, 6, 5),
            'article': 2,
            'clicks': 16
        }]

        result = api.query(start, end, ['date', 'article'], ad_group=1)[0]

        self.assertEqual(result, expected)

    def test_list_constraints(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'ctr': 1.24204786428355,
            'cpc': 0.054409756097561,
            'cost': 2.2308,
            'impressions': 3301,
            'article': 1,
            'clicks': 41
        }, {
            'ctr': 1.37240356083086,
            'cpc': 0.041172972972973,
            'cost': 1.5234,
            'impressions': 2696,
            'article': 2,
            'clicks': 37
        }, {
            'ctr': 1.3417759686416402,
            'cpc': 0.0544101123595506,
            'cost': 4.8425,
            'impressions': 6633,
            'article': 3,
            'clicks': 89
        }, {
            'ctr': 1.2448132780083,
            'cpc': 0.0544083333333333,
            'cost': 3.2645,
            'impressions': 4820,
            'article': 4,
            'clicks': 60
        }]

        result = api.query(start, end, ['article'], article=[1, 2, 3, 4, 5])[0]

        self.assertEqual(result, expected)

    def test_invalid_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        self.assertRaises(
            exc.ReportsQueryError,
            api.query,
            start,
            end,
            ['impressions'],
            ad_group=1
        )

        self.assertRaises(
            exc.ReportsQueryError,
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
            'cpc': 0.03400625,
            'cost': 0.5441,
            'impressions': 1216,
            'date': datetime.date(2014, 6, 5),
            'article': 2,
            'clicks': 16
        }, {
            'ctr': 1.63934426229508,
            'cpc': 0.0448058823529412,
            'cost': 0.7617,
            'impressions': 1037,
            'date': datetime.date(2014, 6, 4),
            'article': 2,
            'clicks': 17
        }, {
            'ctr': 1.66139240506329,
            'cpc': 0.054409523809523797,
            'cost': 1.1426,
            'impressions': 1264,
            'date': datetime.date(2014, 6, 4),
            'article': 1,
            'clicks': 21
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'impressions': 178,
            'date': datetime.date(2014, 6, 5),
            'article': 1,
            'clicks': 0
        }]

        result = api.query(start, end, ['date', 'article'], order='cpc', ad_group=1)[0]
        self.assertEqual(result, expected)

        result = api.query(start, end, ['date', 'article'], order='-cpc', ad_group=1)[0]

        desc_expected = [expected[2], expected[1], expected[0], expected[3]]
        self.assertEqual(result, desc_expected)

    def test_pagination(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        expected = [{
            'ctr': 1.31578947368421,
            'cpc': 0.03400625,
            'cost': 0.5441,
            'impressions': 1216,
            'date': datetime.date(2014, 6, 5),
            'article': 2,
            'clicks': 16
        }, {
            'ctr': 1.63934426229508,
            'cpc': 0.0448058823529412,
            'cost': 0.7617,
            'impressions': 1037,
            'date': datetime.date(2014, 6, 4),
            'article': 2,
            'clicks': 17
        }]

        result = api.query(
            start,
            end,
            ['date', 'article'],
            order='cpc',
            page=1,
            page_size=2,
            ad_group=1
        )
        self.assertEqual(result[0], expected)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 1)
        self.assertEqual(result[5], 2)

        expected = [{
            'ctr': 1.66139240506329,
            'cpc': 0.054409523809523797,
            'cost': 1.1426,
            'impressions': 1264,
            'date': datetime.date(2014, 6, 4),
            'article': 1,
            'clicks': 21
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'impressions': 178,
            'date': datetime.date(2014, 6, 5),
            'article': 1,
            'clicks': 0
        }]

        result = api.query(
            start,
            end,
            ['date', 'article'],
            order='cpc',
            page=2,
            page_size=2,
            ad_group=1
        )
        self.assertEqual(result[0], expected)
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 3)
        self.assertEqual(result[5], 4)

        # Should be the same page as page 2
        result = api.query(
            start,
            end,
            ['date', 'article'],
            order='cpc',
            page=3,
            page_size=2,
            ad_group=1
        )
        self.assertEqual(result[0], expected)
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[3], 4)
        self.assertEqual(result[4], 3)
        self.assertEqual(result[5], 4)


class ApiTestCase(test.TestCase):

    def test_clean_url(self):

        url_normal = 'http://sd.domain.com/path/to?attr1=1&attr2=&attr1=123i#uff'
        self.assertEqual(url_normal, api._clean_url(url_normal))

        url_with_non_zemanta_utm = 'http://sd.domain.com/path/to?attr1=1&utm_source=nonzemanta'
        self.assertEqual(url_with_non_zemanta_utm, api._clean_url(url_with_non_zemanta_utm))

        url_with_zemanta_but_no_utm = 'http://sd.domain.com/path/to?attr1=1&source=zemantaone'
        self.assertEqual(url_with_zemanta_but_no_utm, api._clean_url(url_with_zemanta_but_no_utm))

        url_with_zemanta_and_utm = 'http://sd.domain.com/path/to?attr1=1&utm_source=zemantaone'
        url_with_zemanta_and_utm_cleaned = 'http://sd.domain.com/path/to?attr1=1'
        self.assertEqual(url_with_zemanta_and_utm_cleaned, api._clean_url(url_with_zemanta_and_utm))


class UpsertReportsTestCase(test.TestCase):

    fixtures = ['test_reports_base.yaml']

    def test_save_reports(self):
        date1 = datetime.date(2014, 7, 1)
        date2 = datetime.date(2014, 7, 2)

        ags1 = dashmodels.AdGroupSource.objects.get(id=1)
        rows_ags1_date1 = [
            {
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
                'cpc_cc': None
            },
            {
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
                'cpc_cc': None
            },
        ]
        rows_ags2_date1 = [
            {
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': None,
                'cpc_cc': 1400
            },
            {
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': None,
                'cpc_cc': 900
            },
        ]

        ags2 = dashmodels.AdGroupSource.objects.get(id=1)
        rows_ags1_date2 = [
            {
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
                'cpc_cc': None
            },
            {
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': 900,
                'cpc_cc': None
            },
        ]
        rows_ags2_date2 = [
            {
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': None,
                'cpc_cc': 1400
            },
            {
                'title': 'Test Article 2',
                'url': 'http://example.com/',
                'impressions': 40,
                'clicks': 1,
                'cost_cc': None,
                'cpc_cc': 900
            },
        ]

        self.assertTrue(len(models.ArticleStats.objects.all()) == 0)

        api.save_report(ags1.ad_group, ags1.source, rows_ags1_date1, date1)
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

        api.save_report(ags2.ad_group, ags2.source, rows_ags2_date1, date1)
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
            self.assertEqual(stats.cost_cc, row['cpc_cc'] * row['clicks'])

        api.save_report(ags1.ad_group, ags1.source, rows_ags1_date2, date2)
        api.save_report(ags2.ad_group, ags2.source, rows_ags2_date2, date2)

        articles_ags1 = dashmodels.Article.objects.order_by('title')
        articles_ags2 = dashmodels.Article.objects.order_by('title')

        self.assertEqual(len(articles_ags1), 2)
        self.assertEqual(len(articles_ags2), 2)

        for article1, article2 in zip(articles_ags1, articles_ags2):
            self.assertEqual(article1, article2)

    def test_save_reports_reinsert(self):
        rows = [
            {
                'title': 'Test Article 1',
                'url': 'http://example.com/',
                'impressions': 50,
                'clicks': 2,
                'cost_cc': 2800,
                'cpc_cc': None
            },
            {
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
                'title': 'Test Article 1 New',
                'url': 'http://example.com/',
                'impressions': 100,
                'clicks': 4,
                'cost_cc': 5600,
                'cpc_cc': None
            },
            {
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
                'title': 'Test Article 1 New',
                'url': 'http://example.com/new',
                'impressions': 200,
                'clicks': 8,
                'cost_cc': 11200,
                'cpc_cc': None
            },
            {
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

        api.save_report(ags.ad_group, ags.source, rows, date)
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

        api.save_report(ags.ad_group, ags.source, rows_new_title, date)
        stats = models.ArticleStats.objects.filter(ad_group=ags.ad_group, source=ags.source, datetime=date)
        self.assertEqual(len(stats), 2)
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

        api.save_report(ags.ad_group, ags.source, rows_new_url, date)
        self.assertEqual(len(stats), 2)
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


class ArticleReconciliationTestCase(test.TestCase):

    def _mocked_create(url, title, ad_group):
        dashmodels.Article(url=url, title=title, ad_group=ad_group).save()
        raise IntegrityError

    @patch('dash.models.Article.objects.create', _mocked_create)
    @patch('reports.api.transaction.atomic')
    def test_retry_on_integrity_error(self, atomic_mock):
        ad_group = dashmodels.AdGroup(id=1)
        raw_url = 'http://sd.domain.com/path/to'
        title = 'Example title'

        self.assertSequenceEqual(dashmodels.Article.objects.all(), [])
        api._reconcile_article(raw_url, title, ad_group)

    def test_reconcile_article(self):
        ad_group = dashmodels.AdGroup(id=1)
        raw_url = 'http://sd.domain.com/path/to'
        title = 'Five article titles you would never believe to exist'

        with self.assertRaises(exc.ArticleReconciliationException):
            api._reconcile_article(raw_url, title, None)

        with self.assertRaises(exc.ArticleReconciliationException):
            api._reconcile_article(raw_url, None, ad_group)

        with self.assertRaises(exc.ArticleReconciliationException):
            api._reconcile_article(None, title, ad_group)

        cleaned_url = api._clean_url(raw_url)
        with self.assertRaises(ObjectDoesNotExist):
            article = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)

        article = api._reconcile_article(raw_url, title, ad_group)

        db_article = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)
        self.assertEqual(article, db_article)

        same_article = api._reconcile_article(raw_url, title, ad_group)
        self.assertEqual(article, same_article)
