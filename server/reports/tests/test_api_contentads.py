import datetime

from mock import patch
from django.test import TestCase

from reports import api_contentads
from reports import aggregate_fields


@patch('reports.redshift._get_results')
class ApiContentAdsTest(TestCase):
    fixtures = ['test_api_contentads']

    def _get_query(self, mock_get_results):
        return mock_get_results.call_args[0][0]

    def check_breakdown(self, mock_get_results, breakdown):
        query = self._get_query(mock_get_results)

        self.assertEqual(breakdown is not None, 'GROUP BY' in query)
        if not breakdown:
            return

        breakdown_fields = [api_contentads.CONTENTADSTATS_FIELD_MAPPING.get(f, f) for f in breakdown]

        # check group by statement if contains breakdown fields
        group_by_fields = query.split('GROUP BY')[1].split(',')
        self.assertEqual(len(breakdown_fields), len(group_by_fields))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in group_by_fields if bf in x]))

        # check select fields if contains breakdown fields
        select_fields = query.split('FROM')[0].split(',')
        self.assertEqual(len(select_fields), len(breakdown) + len(aggregate_fields.ALL_AGGREGATE_FIELDS) + 1)
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in select_fields if bf in x]))

    def check_constraints(self, mock_get_results, **constraints):
        query = self._get_query(mock_get_results)
        where_constraints = query.split('WHERE')[1].split('GROUP BY')[0].split('AND')
        self.assertEqual(len(where_constraints), len(constraints))

        self.assertIn('"date" >= \'{}\''.format(constraints['start_date']), query)
        self.assertIn('"date" <= \'{}\''.format(constraints['end_date']), query)

    def check_aggregations(self, mock_get_results):
        required_statements = [
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("total_time_on_site" AS FLOAT)) / SUM("visits") ELSE NULL END as "avg_tos"',
            'SUM("impressions") AS "impressions_sum"',
            'CASE WHEN SUM("impressions") <> 0 THEN SUM(CAST("clicks" AS FLOAT)) / SUM("impressions") ELSE NULL END as "ctr"',
            'SUM("cost_cc") AS "cost_cc_sum"',
            'CASE WHEN SUM("clicks") <> 0 THEN SUM(CAST("cost_cc" AS FLOAT)) / SUM("clicks") ELSE NULL END as "cpc_cc"',
            'SUM("pageviews") AS "pageviews_sum"',
            'SUM("new_visits") AS "new_visits_sum"',
            'SUM("visits") AS "visits_sum"',
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("bounced_visits" AS FLOAT)) / SUM("visits") ELSE NULL END as "bounce_rate"',
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("new_visits" AS FLOAT)) / SUM("visits") ELSE NULL END as "percent_new_users"',
            'SUM("clicks") AS "clicks_sum"',
            'CASE WHEN SUM("visits") <> 0 THEN SUM(CAST("pageviews" AS FLOAT)) / SUM("visits") ELSE NULL END as "pv_per_visit"',
            'CASE WHEN SUM("clicks") = 0 THEN NULL WHEN SUM("visits") = 0 THEN 1 WHEN SUM("clicks") < SUM("visits") THEN 0 ELSE (SUM(CAST("clicks" AS FLOAT)) - SUM("visits")) / SUM("clicks") END as "click_discrepancy"'
        ]
        query = self._get_query(mock_get_results)

        for rs in required_statements:
            self.assertIn(rs, query)

    def test_query_filter_by_ad_group(self, _get_results):
        _get_results.return_value = [{
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
        }]

        constraints = dict(
            start_date=datetime.date(2015, 2, 1),
            end_date=datetime.date(2015, 2, 2),
            ad_group=1
        )
        breakdown = None

        stats = api_contentads.query(breakdown=breakdown, **constraints)

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

        self.check_breakdown(_get_results, breakdown)
        self.check_constraints(_get_results, **constraints)
        self.check_aggregations(_get_results)

    def test_query_breakdown_by_content_ad(self, _get_results):
        constraints = dict(
            start_date=datetime.date(2015, 2, 1),
            end_date=datetime.date(2015, 2, 2),
            ad_group=1
        )
        breakdown = ['content_ad']

        api_contentads.query(breakdown=breakdown, constraints=constraints)

        self.check_breakdown(_get_results, breakdown)
        self.check_constraints(_get_results, **constraints)
        self.check_aggregations(_get_results)

    def test_query_breakdown_by_date(self, _get_results):
        constraints = dict(
            start_date=datetime.date(2015, 2, 1),
            end_date=datetime.date(2015, 2, 2),
            ad_group=1
        )
        breakdown = ['date']
        api_contentads.query(breakdown=breakdown, constraints = constraints)

        self.check_breakdown(_get_results, breakdown)
        self.check_constraints(_get_results, **constraints)
        self.check_aggregations(_get_results)

    def test_query_filter_by_date(self, _get_results):
        constraints = dict(
            start_date=datetime.date(2015, 2, 1),
            end_date=datetime.date(2015, 2, 2),
            date=datetime.date(2015, 2, 1),
        )
        api_contentads.query(**constraints)
        self.check_constraints(_get_results, constraints = constraints)
        self.check_aggregations(_get_results)
