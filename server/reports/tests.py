from django.test import TestCase

from . import api


class ApiTestCase(TestCase):

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
