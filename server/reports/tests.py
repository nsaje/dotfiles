from django.db import IntegrityError
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from mock import patch, Mock

from . import api
from . import exc
from dash import models as dashmodels


class ApiTestCase(TestCase):

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
