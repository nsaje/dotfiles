import datetime

from django import test
from mock import patch
from collections import Sequence

from reports import api
from reports import refresh
from reports import exc as repsexc
from utils.test_helper import dicts_match_for_keys, sequence_of_dicts_match_for_keys
from utils.url_helper import clean_url

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
