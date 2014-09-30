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
                'bounce_rate': 75.1540041067762,
                'date': datetime.date(2014, 6, 4),
                'new_visits': 1291,
                'pageviews': 2822,
                'percent_new_users': 88.3641341546886,
                'pv_per_visit': 1.9315537303217,
                'visits': 1461
            },
            {
                'avg_tos': 10.0,
                'bounce_rate': 90,
                'date': datetime.date(2014, 6, 5),
                'new_visits': 190,
                'pageviews': 500,
                'percent_new_users': 47.5,
                'pv_per_visit': 1.25,
                'visits': 400
            },
            {
                'avg_tos': 7.13409415121255,
                'bounce_rate': 74.3223965763195,
                'date': datetime.date(2014, 6, 6),
                'new_visits': 661,
                'pageviews': 1201,
                'percent_new_users': 94.2938659058489,
                'pv_per_visit': 1.7132667617689,
                'visits': 701
            }
        ]

        self.assertTrue(sequence_of_dicts_match_for_keys(result, expected, expected[0].keys()))

    def test_postclick_metrics_total(self):
        result = api.query(self.start_date, self.end_date)

        expected = {
            'avg_tos': 7.2080405932865,
            'bounce_rate': 77.2443403590945,
            'new_visits': 2142,
            'pageviews': 4523,
            'percent_new_users': 83.6065573770492,
            'pv_per_visit': 1.76541764246682,
            'visits': 2562
        }

        self.assertTrue(dicts_match_for_keys(result, expected, expected.keys()))

    def test_incomplete_metrics(self):
        is_complete = api.has_complete_postclick_metrics_ad_groups(self.start_date, self.end_date, [1])
        self.assertFalse(is_complete)

        is_complete = api.has_complete_postclick_metrics_ad_groups(self.start_date, datetime.date(2014, 6, 5), [1])
        self.assertFalse(is_complete)

        is_complete = api.has_complete_postclick_metrics_ad_groups(datetime.date(2014, 6, 6), datetime.date(2014, 6, 6), [1])
        self.assertTrue(is_complete)

        is_complete = api.has_complete_postclick_metrics_campaigns(self.start_date, self.end_date, [1])
        self.assertFalse(is_complete)

        is_complete = api.has_complete_postclick_metrics_campaigns(self.start_date, datetime.date(2014, 6, 5), [1])
        self.assertFalse(is_complete)

        is_complete = api.has_complete_postclick_metrics_campaigns(datetime.date(2014, 6, 6), datetime.date(2014, 6, 6), [1])
        self.assertTrue(is_complete)

        is_complete = api.has_complete_postclick_metrics_accounts(self.start_date, self.end_date, [1])
        self.assertFalse(is_complete)

        is_complete = api.has_complete_postclick_metrics_accounts(self.start_date, datetime.date(2014, 6, 5), [1])
        self.assertFalse(is_complete)

        is_complete = api.has_complete_postclick_metrics_accounts(datetime.date(2014, 6, 6), datetime.date(2014, 6, 6), [1])
        self.assertTrue(is_complete)

class GoalConversionTestCase(test.TestCase):
    fixtures = [
        'test_reports_base.yaml', 
        'test_article_stats_postclick.yaml',
        'test_conversion_goal_stats.yaml',
    ]

    def setUp(self):
        self.start_date = datetime.date(2014, 6, 4)
        self.end_date = datetime.date(2014, 6, 4)

    def test_conversion_goal_reports(self):
        result = api.query(self.start_date, self.end_date, ad_group=1)

        self.assertEqual(result['goals']['Goal_A']['conversions'], 14)
        self.assertEqual(result['goals']['Goal_B']['conversions'], 17)
        self.assertEqual(result['goals']['Goal_A']['conversion_value'], 0.3)
        self.assertEqual(result['goals']['Goal_B']['conversion_value'], 0.5)
        self.assertEqual(result['visits'], 350)

