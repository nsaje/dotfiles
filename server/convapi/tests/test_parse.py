from django.test import TestCase

from convapi.parse import Keyword


class KeywordTest(TestCase):
    fixtures = ['test_ga_aggregation.yaml']

    def test_init(self):
        keyword_string = 'z11b1_gumgum1z'
        keyword = Keyword(keyword_string)

        self.assertEqual(keyword.id, keyword_string)
        self.assertEqual(keyword.url, 'http://testurl.com')
        self.assertEqual(keyword.ad_group_id, 1)
        self.assertEqual(keyword.source_param, 'b1_gumgum')

    def test_init_nonexistent_content_ad(self):
        keyword_string = 'z12341b1_gumgum1z'
        keyword = Keyword(keyword_string)

        self.assertEqual(keyword.id, keyword_string)
        self.assertIsNone(keyword.url)
        self.assertIsNone(keyword.ad_group_id)
        self.assertEqual(keyword.source_param, 'b1_gumgum')

    def test_init_missing_content_ad_id(self):
        keyword_string = 'z1b1_gumgum1z'
        keyword = Keyword(keyword_string)

        self.assertEqual(keyword.id, keyword_string)
        self.assertIsNone(keyword.url)
        self.assertIsNone(keyword.ad_group_id)
        self.assertEqual(keyword.source_param, 'b1_gumgum')

    def test_init_missing_source_param(self):
        keyword_string = 'z111z'
        keyword = Keyword(keyword_string)

        self.assertEqual(keyword.id, keyword_string)
        self.assertEqual(keyword.url, 'http://testurl.com')
        self.assertEqual(keyword.ad_group_id, 1)
        self.assertEqual(keyword.source_param, '')

    def test_init_corrupted_keyword(self):
        keyword_string = 'zz'
        keyword = Keyword(keyword_string)

        self.assertEqual(keyword.id, keyword_string)
        self.assertIsNone(keyword.url)
        self.assertIsNone(keyword.ad_group_id)
        self.assertEqual(keyword.source_param, '')
