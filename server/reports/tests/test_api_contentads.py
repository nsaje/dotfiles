import datetime

from django.test import TestCase

from reports import api_contentads


class ApiContentAdsTest(TestCase):
    fixtures = ['test_api_contentads']

    def test_query_filter_by_ad_group(self):
        stats = api_contentads.query(
            datetime.date(2015, 2, 1),
            datetime.date(2015, 2, 2),
            ad_group=1
        )

        self.assertEqual(stats, {
            'clicks': 1000,
            'cost': 120.0,
            'cpc': 0.12,
            'ctr': 0.01,
            'impressions': 10000000
        })

    def test_query_breakdown_by_content_ad(self):
        stats = api_contentads.query(
            datetime.date(2015, 2, 1),
            datetime.date(2015, 2, 2),
            breakdown=['content_ad'],
            ad_group=1
        )

        self.assertEqual(stats, [{
            'content_ad': 2,
            'ctr': 0.01,
            'cpc': 0.1167,
            'cost': 70.0,
            'impressions': 6000000,
            'clicks': 600
        }, {
            'content_ad': 1,
            'ctr': 0.01,
            'cpc': 0.125,
            'cost': 50.0,
            'impressions': 4000000,
            'clicks': 400
        }])

    def test_query_breakdown_by_date(self):
        stats = api_contentads.query(
            datetime.date(2015, 2, 1),
            datetime.date(2015, 2, 2),
            breakdown=['date'],
            ad_group=1
        )

        self.assertEqual(stats, [{
            'ctr': 0.01,
            'cpc': 0.1333,
            'cost': 40.0,
            'date': datetime.date(2015, 2, 1),
            'impressions': 3000000,
            'clicks': 300
        }, {
            'ctr': 0.01,
            'cpc': 0.1143,
            'cost': 80.0,
            'date': datetime.date(2015, 2, 2),
            'impressions': 7000000,
            'clicks': 700
        }])

    def test_query_filter_by_date(self):
        stats = api_contentads.query(
            datetime.date(2015, 2, 1),
            datetime.date(2015, 2, 2),
            date=datetime.date(2015, 2, 1)
        )

        self.assertEqual(stats, {
            'clicks': 300,
            'cost': 40.0,
            'cpc': 0.1333,
            'ctr': 0.01,
            'impressions': 3000000
        })
