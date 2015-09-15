import datetime

from mock import patch
from django.test import TestCase

from reports import api_publishers


@patch('reports.redshift._get_results')
class ApiPublishersTest(TestCase):

    def _get_query(self, mock_get_results):
        return mock_get_results.call_args[0][0]

    def check_breakdown(self, mock_get_results, breakdown):
        query = self._get_query(mock_get_results)

        if not breakdown:
            self.assertFalse('GROUP BY' in query)
            return
        self.assertTrue('GROUP BY' in query)

        breakdown_fields = [api_publishers.OUTPUT_FIELDS_REVERSE_MAPPING.get(f, f) for f in breakdown]

        # check group by statement if contains breakdown fields
        group_by_fields = query.split('GROUP BY')[1].split(',')
        self.assertEqual(len(breakdown_fields), len(group_by_fields))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in group_by_fields if bf in x]))

        # check select fields if contains breakdown fields
        select_fields = query.split('FROM')[0].split(',')
        self.assertEqual(len(select_fields), len(breakdown) + len(api_publishers.PUBLISHERS_AGGREGATE_FIELDS))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in select_fields if bf in x]))

    def check_constraints(self, mock_get_results, constraints):
        query = self._get_query(mock_get_results)
        where_constraints = query.split('WHERE')[1].split('GROUP BY')[0].split('AND')
        self.assertEqual(len(where_constraints), len(constraints))

        self.assertIn('"date" >= \'{}\''.format(constraints['start_date']), query)
        self.assertIn('"date" <= \'{}\''.format(constraints['end_date']), query)

    def check_aggregations(self, mock_get_results):
        required_statements = [
            '"date"',
            'CASE WHEN SUM("clicks") <> 0 THEN SUM(CAST("cost_micro" AS FLOAT)) / SUM("clicks") ELSE NULL END as "cpc_micro"',
            'SUM("cost_micro") AS "cost_micro_sum",SUM("impressions") AS "impressions_sum"',
            'CASE WHEN SUM("impressions") <> 0 THEN SUM(CAST("clicks" AS FLOAT)) / SUM("impressions") ELSE NULL END as "ctr"',
            'SUM("clicks") AS "clicks_sum"',
        ]
        query = self._get_query(mock_get_results)

        for rs in required_statements:
            self.assertIn(rs, query)

    def test_query_filter_by_ad_group(self, _get_results):
        _get_results.return_value = [{
            'impressions_sum': 10560,
            'clicks_sum': 123,
            'ctr': 1.0,
            'cpc_micro': 1.0,
            'cost_micro_sum': 26638,
            'date': '2015-01-01',
        }]

        constraints = dict(
            ad_group=1
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        breakdown = []

        stats = api_publishers.query(start_date, end_date, breakdown_fields=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        self.assertDictEqual(stats, 
        {'clicks': 123,
         'cost': 2.6638e-05,
         'cpc': 1e-09,
         'ctr': 100.0,
         'impressions': 10560,
         'date': '2015-01-01',
         }
        )

        self.check_breakdown(_get_results, breakdown)
        self.check_constraints(_get_results, constraints)
        self.check_aggregations(_get_results)

    def test_query_breakdown_by_domain(self, _get_results):
        constraints = dict(
            ad_group=1
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        breakdown = ['domain']

        api_publishers.query(start_date, end_date, breakdown_fields=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        self.check_breakdown(_get_results, breakdown)
        self.check_constraints(_get_results, constraints)
        self.check_aggregations(_get_results)

    def test_query_breakdown_by_date(self, _get_results):
        self.maxDiff = None
        constraints = dict(
            ad_group=1
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        breakdown = ['date']
        api_publishers.query(start_date, end_date, breakdown_fields=breakdown, constraints = constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})

        self.check_breakdown(_get_results, breakdown)
        self.check_constraints(_get_results, constraints)
        self.check_aggregations(_get_results)

    def test_query_filter_by_date(self, _get_results):
        constraints = dict(
            date=datetime.date(2015, 2, 1),
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        api_publishers.query(start_date, end_date, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        
        self.check_constraints(_get_results, constraints)
        self.check_aggregations(_get_results)
