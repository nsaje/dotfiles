import datetime
import time

import mock
from django.test import TestCase

import dash.models
from reports import api_publishers


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
            'CASE WHEN SUM("clicks") <> 0 THEN SUM(CAST("cost_nano" AS FLOAT)) / SUM("clicks") ELSE NULL END AS "cpc_nano"',
            'SUM("cost_nano") AS "cost_nano_sum"',
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
            'cpc_nano': 1.0,
            'cost_nano_sum': 26638,
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
        self.assertIn("SUM(clicks) = 0, sum(cost_nano) IS NULL, cpc_nano DESC", query)

    def test_query_active(self):
        # this doesn't really test blacklisting but runs the functions to make
        # sure blacklisting condition creation executes
        # setup some test data
        self.get_cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'ctr': 0.0,
            'exchange': 'gumgum',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
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
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
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

    def test_query_blacklisted_joined(self):
        # this doesn't really test blacklisting but runs the functions to make
        # sure blacklisting condition creation executes
        # setup some test data
        self.get_cursor().dictfetchall.return_value = [
        {
            'domain': u'zemanta.com',
            'ctr': 0.0,
            'exchange': 'gumgum',
            'cpc_nano': 0,
            'cost_nano_sum': 1e-05,
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
                'exchange': 'triplelift',
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

        self.assertIn('(domain IN (%s,%s) AND adgroup_id=%s AND exchange=%s)', self._get_query())


class ApiPublishersMapperTest(TestCase):
    def test_map_rowdict_to_output_nones(self):
        input = {'impressions_sum': None,
                'domain': None,
                'exchange': None,
                'date': None,
                'clicks_sum': None,
                'cost_nano_sum': None,
                'cpc_nano': None,
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
        input = {'cpc_nano': 100000,
                 'cost_nano_sum': 200000,
                 'ctr': 0.2}
        result = api_publishers.rs_pub.map_result_to_app(input, json_fields=[])
        self.assertEqual(result, {'cost': 0.0002,
                                  'cpc': 0.0001,
                                  'ctr': 20.0
                                  })

    def test_map_unknown_row(self):
        input = {'bah': 100000}
        self.assertRaises(KeyError, api_publishers.rs_pub.map_result_to_app, input, json_fields=[])


class ApiPublishersObToS3TestCase(TestCase):

    fixtures = ['test_reports_base.yaml']

    @mock.patch('utils.s3helpers.S3Helper')
    @mock.patch('reports.api_publishers.time')
    def test_put_ob_data_to_s3(self, mock_time, mock_s3helper):
        mock_time.time.return_value = time.mktime(datetime.datetime(2016, 1, 1).timetuple())
        ad_group = dash.models.AdGroup.objects.get(id=1)
        date = datetime.date(2016, 1, 1)

        test_rows = [{
            "ob_id": "AAAABBBBB",
            "clicks": 20,
            "name": "CNN money",
        }, {
            "ob_id": "AAAABBBBB",
            "clicks": 80,
            "name": "How Stuff Works (Blucora)",
        }]

        api_publishers.put_ob_data_to_s3(date, ad_group, test_rows)

        expected_key = 'ob_publishers_raw/2016/01/01/1/1451606400000.json'
        expected_json = '[{"ob_id": "AAAABBBBB", "clicks": 20, "name": "CNN money"}, '\
                        '{"ob_id": "AAAABBBBB", "clicks": 80, "name": "How Stuff Works (Blucora)"}]'

        mock_s3helper.return_value.put.assert_called_once_with(expected_key, expected_json)
