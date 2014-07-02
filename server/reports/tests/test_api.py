import datetime

from django import test
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from mock import patch

from dash import models as dashmodels
from reports import api
from reports import exc


class QueryTestCase(test.TestCase):
    fixtures = ['test_article_stats.yaml']

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

    def test_reconcile_article(self):
        ad_group = dashmodels.AdGroup(id=1)
        raw_url = 'http://sd.domain.com/path/to'
        title = 'Five article titles you would never believe to exist'

        with self.assertRaises(exc.ArticleReconciliationException):
            api._reconcile_article(raw_url, title, None)

        with self.assertRaises(exc.ArticleReconciliationException):
            api._reconcile_article(raw_url, None, ad_group)

        cleaned_url = api._clean_url(raw_url)
        with self.assertRaises(ObjectDoesNotExist):
            article = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)

        article = api._reconcile_article(raw_url, title, ad_group)

        db_article = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)
        self.assertEqual(article, db_article)

        same_article = api._reconcile_article(raw_url, title, ad_group)
        self.assertEqual(article, same_article)

        title = 'Five most disturbing article titles you would never dare believe to exist'
        with self.assertRaises(ObjectDoesNotExist):
            article = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)

        article_new = api._reconcile_article(raw_url, title, ad_group)
        self.assertNotEqual(article, article_new)

        db_article_new = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)
        self.assertEqual(article_new, db_article_new)

        article_new_same = api._reconcile_article(None, title, ad_group)
        self.assertEqual(article_new, article_new_same)

        title = 'Ten articles that at one point didn\'t have URL'
        with self.assertRaises(ObjectDoesNotExist):
            article = dashmodels.Article.objects.get(url=None, title=title, ad_group=ad_group)

        article_without_url = api._reconcile_article(None, title, ad_group)
        article_without_url_same = api._reconcile_article(None, title, ad_group)
        self.assertEqual(article_without_url, article_without_url_same)

        article_with_url = api._reconcile_article(raw_url, title, ad_group)
        db_article_with_url = dashmodels.Article.objects.get(url=cleaned_url, title=title, ad_group=ad_group)
        self.assertEqual(article_with_url, db_article_with_url)

        second_article_without_url = api._reconcile_article(None, title, ad_group)
        self.assertEqual(article_with_url, second_article_without_url)

    @patch('dash.models.Article.objects.create', side_effect=IntegrityError)
    def test_retry_reconcile_article(self, mock_create):
        ad_group = dashmodels.AdGroup(id=1)
        raw_url = 'http://sd.domain.com/path/to'
        title = 'Example title'

        with self.assertRaises(exc.ArticleReconciliationException):
            api._reconcile_article(raw_url, title, ad_group)

        self.assertEqual(mock_create.call_count, api.MAX_RECONCILIATION_RETRIES)

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
