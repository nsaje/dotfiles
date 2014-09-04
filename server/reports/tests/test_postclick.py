import datetime

from django import test

from reports import api
from utils.test_helper import dicts_match_for_keys, sequence_of_dicts_match_for_keys



class PostclickTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats_postclick.yaml']

    def setUp(self):
        self.start_date = datetime.date(2014, 6, 1)
        self.end_date = datetime.date(2014, 7, 1)

    def test_postclick_metrics_aggregation(self):
        result = api.query(self.start_date, self.end_date, ['date'], ['date'])

        expected = [
            {
                'avg_tos': 6.47912388774812,
                'bounce_rate': 0.751540041067762,
                'date': datetime.date(2014, 6, 4),
                'new_visits': 1291,
                'pageviews': 2822,
                'percent_new_users': 0.883641341546886,
                'pv_per_visit': 1.9315537303217,
                'visits': 1461
            },
            {
                'avg_tos': 10.0,
                'bounce_rate': 0.9,
                'date': datetime.date(2014, 6, 5),
                'new_visits': 190,
                'pageviews': 500,
                'percent_new_users': 0.475,
                'pv_per_visit': 1.25,
                'visits': 400
            },
            {
                'avg_tos': 7.13409415121255,
                'bounce_rate': 0.743223965763195,
                'date': datetime.date(2014, 6, 6),
                'new_visits': 661,
                'pageviews': 1201,
                'percent_new_users': 0.942938659058488,
                'pv_per_visit': 1.7132667617689,
                'visits': 701
            }
        ]

        self.assertTrue(sequence_of_dicts_match_for_keys(result, expected, expected[0].keys()))

    def test_postclick_metrics_total(self):
        result = api.query(self.start_date, self.end_date)

        expected = {
            'avg_tos': 7.2080405932865,
            'bounce_rate': 0.772443403590945,
            'new_visits': 2142,
            'pageviews': 4523,
            'percent_new_users': 0.836065573770492,
            'pv_per_visit': 1.76541764246682,
            'visits': 2562
        }

        self.assertTrue(dicts_match_for_keys(result, expected, expected.keys()))

    def test_incomplete_metrics(self):
        result = api.query(self.start_date, self.end_date)
        self.assertTrue(result['incomplete_postclick_metrics'])

        result = api.query(self.start_date, datetime.date(2014, 6, 5))
        self.assertFalse(result['incomplete_postclick_metrics'])

        result = api.query(datetime.date(2014, 6, 6), datetime.date(2014, 6, 6))
        self.assertFalse(result['incomplete_postclick_metrics'])