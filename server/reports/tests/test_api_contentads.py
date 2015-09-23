import datetime

from mock import patch
from django.test import TestCase

from reports import api_contentads


@patch('reports.redshift.MyCursor')
class ApiContentAdsTest(TestCase):
    fixtures = ['test_api_contentads']

    def _get_query(self, mock_cursor):
        return mock_cursor().execute.call_args[0][0]

    def _set_results(self, mock_cursor, results):
        mock_cursor().dictfetchall.return_value = results

    def check_breakdown(self, mock_cursor, breakdown):
        query = self._get_query(mock_cursor)

        self.assertEqual(True if breakdown else False, 'GROUP BY' in query)
        if not breakdown:
            return

        breakdown_fields = [api_contentads.RSContentAdStats.by_app_mapping[f]['sql'] for f in breakdown]

        # check group by statement if contains breakdown fields
        group_by_fields = query.split('GROUP BY')[1].split(',')
        self.assertEqual(len(breakdown_fields), len(group_by_fields))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in group_by_fields if bf in x]))

        # check select fields if contains breakdown fields
        select_fields = query.split('FROM')[0].split(',')
        self.assertEqual(len(select_fields), len(breakdown) + len(api_contentads.RSContentAdStats.DEFAULT_RETURNED_FIELDS_APP))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in select_fields if bf in x]))

    def check_constraints(self, mock_cursor, constraints):
        query = self._get_query(mock_cursor)
        where_constraints = query.split('WHERE')[1].split('GROUP BY')[0].split('AND')
        self.assertEqual(len(where_constraints), len(constraints))

        self.assertIn('"date" >= ', query)
        self.assertIn('"date" <= ', query)

    def check_aggregations(self, mock_cursor):
        required_statements = [
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("total_time_on_site" AS FLOAT)) / SUM("visits") ELSE NULL END AS "avg_tos"',
            'SUM("impressions") AS "impressions_sum"',
            'CASE WHEN SUM("impressions") <> 0 THEN SUM(CAST("clicks" AS FLOAT)) / SUM("impressions") ELSE NULL END AS "ctr"',
            'SUM("cost_cc") AS "cost_cc_sum"',
            'CASE WHEN SUM("clicks") <> 0 THEN SUM(CAST("cost_cc" AS FLOAT)) / SUM("clicks") ELSE NULL END AS "cpc_cc"',
            'SUM("pageviews") AS "pageviews_sum"',
            'SUM("new_visits") AS "new_visits_sum"',
            'SUM("visits") AS "visits_sum"',
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("bounced_visits" AS FLOAT)) / SUM("visits") ELSE NULL END AS "bounce_rate"',
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("new_visits" AS FLOAT)) / SUM("visits") ELSE NULL END AS "percent_new_users"',
            'SUM("clicks") AS "clicks_sum"',
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("pageviews" AS FLOAT)) / SUM("visits") ELSE NULL END AS "pv_per_visit"',
            'CASE WHEN SUM("clicks") = 0 THEN NULL WHEN SUM("visits") = 0 THEN 1 WHEN SUM("clicks") < SUM("visits") THEN 0 ELSE (SUM(CAST("clicks" AS FLOAT)) - SUM("visits")) / SUM("clicks") END AS "click_discrepancy"'
        ]
        query = self._get_query(mock_cursor)

        for rs in required_statements:
            self.assertIn(rs, query)

    def test_query_filter_by_ad_group(self, mock_cursor):
        self._set_results(mock_cursor, [{
            'avg_tos': 1.0,
            'impressions_sum': 10560,
            'ctr': 1.0,
            'cpc_cc': 1.0,
            'pageviews_sum': 2821,
            'cost_cc_sum': 26638,
            'click_discrepancy': 0.0,
            'new_visits_sum': 1209,
            'visits_sum': 4030,
            'bounce_rate': 1.0,
            'percent_new_users': 1.0,
            'clicks_sum': 2,
            'pv_per_visit': 1.0
        }])

        constraints = dict(
            ad_group=1
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        breakdown = []

        stats = api_contentads.query(start_date, end_date, breakdown=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})

        self.assertDictEqual(stats, {
            'avg_tos': 1.0,
            'pageviews': 2821,
            'ctr': 100.0,
            'new_visits': 1209,
            'cpc': 0.0001,
            'click_discrepancy': 0.0,
            'visits': 4030,
            'cost': 2.6638,
            'impressions': 10560,
            'percent_new_users': 100.0,
            'clicks': 2,
            'pv_per_visit': 1.0,
            'bounce_rate': 100.0
        })

        self.check_breakdown(mock_cursor, breakdown)
        self.check_constraints(mock_cursor, constraints)
        self.check_aggregations(mock_cursor)

    def test_query_breakdown_by_content_ad(self, mock_cursor):
        constraints = dict(
            ad_group=1
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        breakdown = ['content_ad']

        api_contentads.query(start_date, end_date, breakdown=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        self.check_breakdown(mock_cursor, breakdown)
        self.check_constraints(mock_cursor, constraints)
        self.check_aggregations(mock_cursor)

    def test_query_breakdown_by_date(self, mock_cursor):
        constraints = dict(
            ad_group=1
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        breakdown = ['date']
        api_contentads.query(start_date, end_date, breakdown=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})

        self.check_breakdown(mock_cursor, breakdown)
        self.check_constraints(mock_cursor, constraints)
        self.check_aggregations(mock_cursor)

    def test_query_filter_by_date(self, mock_cursor):
        constraints = dict(
            date=datetime.date(2015, 2, 1),
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        api_contentads.query(start_date, end_date, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})

        self.check_constraints(mock_cursor, constraints)
        self.check_aggregations(mock_cursor)
