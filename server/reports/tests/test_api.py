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
            'ctr': 1.6514558887440245,
            'cpc': 0.050113157894736846,
            'cost': 1.9043,
            'date': datetime.date(2014, 6, 4),
            'impressions': 2301,
            'clicks': 38
        }, {
            'ctr': 1.1477761836441895,
            'cpc': 0.03400625,
            'cost': 0.5441,
            'date': datetime.date(2014, 6, 5),
            'impressions': 1394,
            'clicks': 16
        }, {
            'ctr': 1.0425716768027802,
            'cpc': 0.054408333333333336,
            'cost': 1.3058,
            'date': datetime.date(2014, 6, 6),
            'impressions': 2302,
            'clicks': 24
        }]

        result = api.query(start, end, ['date'], ad_group=1)

        self.assertEqual(result, expected)

    def test_non_exisiting_date_breakdown(self):
        start = datetime.date(2014, 6, 10)
        end = datetime.date(2014, 6, 12)

        result = api.query(start, end, ['date'], ad_group=1)

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

        result = api.query(start, end, [], ad_group=1)

        self.assertEqual(result, expected)

    def test_network_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'network': 1,
            'ctr': 1.3006503251625814,
            'cpc': 0.048130769230769234,
            'cost': 3.7542,
            'impressions': 5997,
            'clicks': 78
        }]

        result = api.query(start, end, ['network'], ad_group=1)

        self.assertEqual(result, expected)

    def test_totals_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'impressions': 5997,
            'cost': 3.7542,
            'clicks': 78,
            'ctr': 1.3006503251625814,
            'cpc': 0.048130769230769234
        }]

        result = api.query(start, end, [], ad_group=1)

        self.assertEqual(result, expected)

    def test_list_breakdown(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 5)

        expected = [{
            'ctr': 1.661392405063291,
            'cpc': 0.05440952380952381,
            'cost': 1.1426,
            'article': 1,
            'date': datetime.date(2014, 6, 4),
            'impressions': 1264,
            'clicks': 21
        }, {
            'ctr': 1.639344262295082,
            'cpc': 0.044805882352941175,
            'cost': 0.7617,
            'article': 2,
            'date': datetime.date(2014, 6, 4),
            'impressions': 1037,
            'clicks': 17
        }, {
            'ctr': 0.0,
            'cpc': None,
            'cost': 0.0,
            'article': 1,
            'date': datetime.date(2014, 6, 5),
            'impressions': 178,
            'clicks': 0
        }, {
            'ctr': 1.3157894736842104,
            'cpc': 0.03400625,
            'cost': 0.5441,
            'article': 2,
            'date': datetime.date(2014, 6, 5),
            'impressions': 1216,
            'clicks': 16
        }]

        result = api.query(start, end, ['date', 'article'], ad_group=1)

        self.assertEqual(result, expected)

    def test_list_constraints(self):
        start = datetime.date(2014, 6, 4)
        end = datetime.date(2014, 6, 8)

        expected = [{
            'ctr': 1.2420478642835504,
            'cpc': 0.05440975609756098,
            'cost': 2.2308,
            'impressions': 3301,
            'article': 1,
            'clicks': 41
        }, {
            'ctr': 1.3724035608308605,
            'cpc': 0.041172972972972975,
            'cost': 1.5234,
            'impressions': 2696,
            'article': 2,
            'clicks': 37
        }, {
            'ctr': 1.3417759686416402,
            'cpc': 0.05441011235955056,
            'cost': 4.8425,
            'impressions': 6633,
            'article': 3,
            'clicks': 89
        }, {
            'ctr': 1.2448132780082988,
            'cpc': 0.054408333333333336,
            'cost': 3.2645,
            'impressions': 4820,
            'article': 4,
            'clicks': 60
        }]

        result = api.query(start, end, ['article'], article=[1, 2, 3, 4, 5])

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

        agn1 = dashmodels.AdGroupNetwork.objects.get(id=1)
        rows_agn1_date1 = [
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
        rows_agn2_date1 = [
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

        agn2 = dashmodels.AdGroupNetwork.objects.get(id=1)
        rows_agn1_date2 = [
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
        rows_agn2_date2 = [
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

        api.save_report(agn1.ad_group, agn1.network, rows_agn1_date1, date1)
        for row in rows_agn1_date1:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'])
            stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=agn1.ad_group,
                network=agn1.network,
                datetime=date1
            )
            self.assertEqual(stats.impressions, row['impressions'])
            self.assertEqual(stats.clicks, row['clicks'])
            self.assertEqual(stats.cost_cc, row['cost_cc'])

        api.save_report(agn2.ad_group, agn2.network, rows_agn2_date1, date1)
        for row in rows_agn2_date1:
            article = dashmodels.Article.objects.get(title=row['title'])
            stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=agn2.ad_group,
                network=agn2.network,
                datetime=date1
            )
            self.assertEqual(stats.impressions, row['impressions'])
            self.assertEqual(stats.clicks, row['clicks'])
            self.assertEqual(stats.cost_cc, row['cpc_cc'] * row['clicks'])

        api.save_report(agn1.ad_group, agn1.network, rows_agn1_date2, date2)
        api.save_report(agn2.ad_group, agn2.network, rows_agn2_date2, date2)

        articles_agn1 = dashmodels.Article.objects.order_by('title')
        articles_agn2 = dashmodels.Article.objects.order_by('title')

        self.assertEqual(len(articles_agn1), 2)
        self.assertEqual(len(articles_agn2), 2)

        for article1, article2 in zip(articles_agn1, articles_agn2):
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

        agn = dashmodels.AdGroupNetwork.objects.get(id=1)
        date = datetime.date(2014, 7, 10)

        stats = models.ArticleStats.objects.filter(ad_group=agn.ad_group, network=agn.network, datetime=date)
        self.assertEqual(len(stats), 0)

        api.save_report(agn.ad_group, agn.network, rows, date)
        stats = models.ArticleStats.objects.filter(ad_group=agn.ad_group, network=agn.network, datetime=date)
        self.assertEqual(len(stats), 2)
        for row in rows:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=agn.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=agn.ad_group,
                network=agn.network,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, row['impressions'])
            self.assertEqual(article_stats.clicks, row['clicks'])
            self.assertEqual(article_stats.cost_cc, row['cost_cc'])

        api.save_report(agn.ad_group, agn.network, rows_new_title, date)
        stats = models.ArticleStats.objects.filter(ad_group=agn.ad_group, network=agn.network, datetime=date)
        self.assertEqual(len(stats), 2)
        for row in rows_new_title:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=agn.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=agn.ad_group,
                network=agn.network,
                datetime=date
            )
            self.assertEqual(article_stats.impressions, row['impressions'])
            self.assertEqual(article_stats.clicks, row['clicks'])
            self.assertEqual(article_stats.cost_cc, row['cost_cc'])

        api.save_report(agn.ad_group, agn.network, rows_new_url, date)
        self.assertEqual(len(stats), 2)
        for row in rows_new_url:
            article = dashmodels.Article.objects.get(title=row['title'], url=row['url'], ad_group=agn.ad_group)
            article_stats = models.ArticleStats.objects.get(
                article=article,
                ad_group=agn.ad_group,
                network=agn.network,
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
