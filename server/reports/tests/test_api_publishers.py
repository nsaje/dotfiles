import datetime

import mock
from django.test import TestCase

from reports import api_publishers
import dash.models


class ApiPublishersTest(TestCase):

    def setUp(self):
        self.patcher = mock.patch('reports.redshift.get_cursor')
        self.get_cursor = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def _get_query(self):
        return self.get_cursor().execute.call_args[0][0]

    def check_breakdown(self, breakdown):
        query = self._get_query()

        if not breakdown:
            self.assertFalse('GROUP BY' in query)
            return
        self.assertTrue('GROUP BY' in query)

        breakdown_fields = [api_publishers.rs_pub.by_app_mapping[f]['sql'] for f in breakdown]

        # check group by statement if contains breakdown fields
        group_by_fields = query.split('GROUP BY')[1].split('ORDER BY')[0].split(',')
        self.assertEqual(len(breakdown_fields), len(group_by_fields))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in group_by_fields if bf in x]))

        # check select fields if contains breakdown fields
        select_fields = query.split('FROM')[0].split(',')
        self.assertEqual(len(select_fields), len(breakdown) + len(api_publishers.rs_pub.DEFAULT_RETURNED_FIELDS_APP))
        for bf in breakdown_fields:
            self.assertEqual(1, len([x for x in select_fields if bf in x]))

    def check_constraints(self, constraints):
        query = self._get_query()
        where_constraints = query.split('WHERE')[1].split('GROUP BY')[0].split('AND')
        self.assertEqual(len(where_constraints), len(constraints))

        self.assertIn('"date">=', query)
        self.assertIn('"date"<=', query)
        # TODO: we need to test parameters here too

    def check_aggregations(self):
        required_statements = [
            '"date"',
            'CASE WHEN SUM("clicks") <> 0 THEN SUM(CAST("cost_micro" AS FLOAT)) / SUM("clicks") ELSE NULL END AS "cpc_micro"',
            'SUM("cost_micro") AS "cost_micro_sum"',
            'SUM("impressions") AS "impressions_sum"',
            'CASE WHEN SUM("impressions") <> 0 THEN SUM(CAST("clicks" AS FLOAT)) / SUM("impressions") ELSE NULL END AS "ctr"',
            'SUM("clicks") AS "clicks_sum"',
        ]
        query = self._get_query()

        for rs in required_statements:
            self.assertIn(rs, query)

    def test_query_filter_by_ad_group(self):
        self.get_cursor().dictfetchall.return_value = [{
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
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        breakdown = []

        stats = api_publishers.query(start_date, end_date, breakdown_fields=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        self.assertDictEqual(stats, {
                                        'clicks': 123,
                                        'cost': 2.6638e-05,
                                        'cpc': 1e-09,
                                        'ctr': 100.0,
                                        'impressions': 10560,
                                        'date': '2015-01-01',
                                    })

        self.check_breakdown(breakdown)
        self.check_constraints(constraints)
        self.check_aggregations()

    def test_query_breakdown_by_domain(self):
        constraints = dict(
            ad_group=1
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        breakdown = ['domain']

        api_publishers.query(start_date, end_date, breakdown_fields=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        self.check_breakdown(breakdown)
        self.check_constraints(constraints)
        self.check_aggregations()

    def test_query_breakdown_by_date(self):
        self.maxDiff = None
        constraints = dict(
            ad_group=1
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        breakdown = ['date']
        api_publishers.query(start_date, end_date, breakdown_fields=breakdown, constraints = constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})

        self.check_breakdown(breakdown)
        self.check_constraints(constraints)
        self.check_aggregations()

    def test_query_filter_by_date(self):
        constraints = dict(
            date=datetime.date(2015, 2, 1),
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        api_publishers.query(start_date, end_date, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})

        self.check_constraints(constraints)
        self.check_aggregations()

    def test_query_order_by_cpc(self):
        constraints = dict(
            ad_group=1
        )
        start_date=datetime.date(2015, 2, 1)
        end_date=datetime.date(2015, 2, 2)
        breakdown = ['domain']

        api_publishers.query(start_date, end_date, order_fields = ['-cpc'], breakdown_fields=breakdown, constraints=constraints)
        constraints.update({'start_date': start_date, 'end_date': end_date})
        self.check_breakdown(breakdown)
        self.check_constraints(constraints)
        self.check_aggregations()
        query = self._get_query()
        self.assertIn("SUM(clicks) = 0, sum(cost_micro) IS NULL, cpc_micro DESC", query)

    def test_query_active(self):
        # this doesn't really test blacklisting but runs the functions to make
        # sure blacklisting condition creation executes
        # setup some test data
        self.get_cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'ctr': 0.0,
            'exchange': 'gumgum',
            'cpc_micro': 0,
            'cost_micro_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]

        # setup some blacklisted publisher entries
        blacklist = [
            {
                'domain': 'test.com',
                'adgroup_id': 1,
                'exchange': 'triplelift'
            },
            {
                'domain': 'test1.com',
                'adgroup_id': 1,
                'exchange': 'gumgum',
            },
        ]

        constraints = {'ad_group': 1}

        start_date = datetime.datetime.utcnow()
        end_date = start_date = datetime.timedelta(days=31)

        publishers_data = api_publishers.query_active_publishers(
            start_date, end_date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=['-cost'],
            constraints=constraints,
            blacklist=blacklist
        )

        self.assertIn(' AND '.join(['NOT (domain=%s AND adgroup_id=%s AND exchange=%s)'] * 2), self._get_query())

    def test_query_blacklisted(self):
        # this doesn't really test blacklisting but runs the functions to make
        # sure blacklisting condition creation executes
        # setup some test data
        self.get_cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'ctr': 0.0,
            'exchange': 'gumgum',
            'cpc_micro': 0,
            'cost_micro_sum': 1e-05,
            'impressions_sum': 1000L,
            'clicks_sum': 0L,
        },
        ]

        # setup some blacklisted publisher entries
        blacklist = [
            {
                'domain': 'test.com',
                'adgroup_id': 1,
                'exchange': 'triplelift'
            },
            {
                'domain': 'test1.com',
                'adgroup_id': 1,
                'exchange': 'gumgum',
            },
        ]

        constraints = {'ad_group': 1}

        start_date = datetime.datetime.utcnow()
        end_date = start_date = datetime.timedelta(days=31)

        publishers_data = api_publishers.query_blacklisted_publishers(
            start_date, end_date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=['-cost'],
            constraints=constraints,
            blacklist=blacklist
        )

        self.assertIn(' OR '.join(['(domain=%s AND adgroup_id=%s AND exchange=%s)'] * 2), self._get_query())


@mock.patch('reports.redshift.get_cursor')
class ApiPublishersInsertTest(TestCase):
    def test_ob_insert_adgroup_date(self, mock_get_cursor):
        mock_cursor = mock.Mock()
        mock_get_cursor.return_value = mock_cursor

        api_publishers.ob_insert_adgroup_date(datetime.date(2015,2,1),
                                              3,
                                              "outbrain",
                                              [
                                                  {
                                                      "ob_section_id": "AAAABBBBB",
                                                      "clicks": 20,
                                                      "name": "CNN money",
                                                      "url": "http://money.cnn.com",
                                                  },
                                                  {
                                                      "ob_section_id": "AAAABBBBB",
                                                      "clicks": 80,
                                                      "name": "CNN money",
                                                      "url": "http://money.cnn.com",
                                                  }
                                              ],
                                              200
                                              )

        mock_cursor.execute.assert_has_calls([
            mock.call('DELETE FROM "ob_publishers_1" WHERE (adgroup_id=%s AND date=%s AND exchange=%s)', [3, datetime.date(2015, 2, 1), 'outbrain']),
            mock.call('INSERT INTO ob_publishers_1 (date,adgroup_id,exchange,domain,name,clicks,cost_micro,ob_section_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s),(%s,%s,%s,%s,%s,%s,%s,%s)',
                      [datetime.date(2015, 2, 1), 3, 'outbrain', 'money.cnn.com', 'CNN money', 20, 40000000000.0, 'AAAABBBBB', datetime.date(2015, 2, 1), 3, 'outbrain', 'money.cnn.com', 'CNN money', 80, 160000000000.0, 'AAAABBBBB'])
        ])


class ApiPublishersMapperTest(TestCase):
    def test_map_rowdict_to_output_nones(self):
        input = {'impressions_sum': None,
                'domain': None,
                'exchange': None,
                'date': None,
                'clicks_sum': None,
                'cost_micro_sum': None,
                'cpc_micro': None,
                'ctr': None,
                'adgroup_id': None,
                'exchange': None}
        result = api_publishers.rs_pub.map_result_to_app(input, json_fields=[])
        self.assertEqual(result, {   'ad_group': None,
                                     'clicks': None,
                                     'cost': None,
                                     'cpc': None,
                                     'ctr': None,
                                     'date': None,
                                     'domain': None,
                                     'exchange': None,
                                     'impressions': None})

    def test_map_rowdict_to_output_transforms(self):
        input = {'cpc_micro': 100000,
                 'cost_micro_sum': 200000,
                 'ctr': 0.2,
                }
        result = api_publishers.rs_pub.map_result_to_app(input, json_fields=[])
        self.assertEqual(result, {'cost': 0.0002,
                                  'cpc': 0.0001,
                                  'ctr': 20.0
                                  })

    def test_map_unknown_row(self):
        input = {'bah': 100000,}
        self.assertRaises(KeyError, api_publishers.rs_pub.map_result_to_app, input, json_fields=[])

