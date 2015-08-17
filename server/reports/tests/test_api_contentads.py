import datetime
import reports.models

from django.test import TestCase, TransactionTestCase

from convapi import parse_v2
from reports import api_contentads
from reports import constants


class ApiContentAdsTest(TestCase):
    fixtures = ['test_api_contentads']

    def test_query_filter_by_ad_group(self):
        stats = api_contentads.query(
            datetime.date(2015, 2, 1),
            datetime.date(2015, 2, 2),
            ad_group=1
        )

        self.assertItemsEqual(stats, {
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

        self.assertItemsEqual(stats, [{
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

        self.assertItemsEqual(stats, [{
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

        self.assertItemsEqual(stats, {
            'clicks': 300,
            'cost': 40.0,
            'cpc': 0.1333,
            'ctr': 0.01,
            'impressions': 3000000
        })


class GaContentAdReportTest(TransactionTestCase):
    fixtures = ['test_api_contentads']

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
            datetime.datetime(2015, 4, 16),
            1,
            "gravity",
            {
                "Goal 1": {
                    "conversion_rate": "0.00%",
                    "conversions": "0",
                    "value": "\u00a30.00"
                }
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
            datetime.datetime(2015, 4, 16),
            12345,
            "gravity",
            {
                "Goal 1": {
                    "conversion_rate": "0.00%",
                    "conversions": "0",
                    "value": "\u00a30.00"
                }
            }
        )
    ]

    def test_correct_row(self):
        self.assertEqual(0, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(0, reports.models.ContentAdGoalConversionStats.objects.count())

        api_contentads.process_report(self.sample_data, constants.ReportType.GOOGLE_ANALYTICS)

        self.assertEqual(1, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(1, reports.models.ContentAdGoalConversionStats.objects.count())

    def test_double_correct_row(self):
        self.assertEqual(0, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(0, reports.models.ContentAdGoalConversionStats.objects.count())

        api_contentads.process_report(self.sample_data, constants.ReportType.GOOGLE_ANALYTICS)
        api_contentads.process_report(self.sample_data, constants.ReportType.GOOGLE_ANALYTICS)

        self.assertEqual(1, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(1, reports.models.ContentAdGoalConversionStats.objects.count())

    def test_invalid_caid(self):
        self.assertEqual(0, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(0, reports.models.ContentAdGoalConversionStats.objects.count())

        with self.assertRaises(Exception):
            api_contentads.process_report(self.sample_invalid_data_1, constants.ReportType.GOOGLE_ANALYTICS)

        self.assertEqual(0, reports.models.ContentAdPostclickStats.objects.count())
        self.assertEqual(0, reports.models.ContentAdGoalConversionStats.objects.count())
