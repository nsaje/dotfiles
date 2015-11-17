import datetime
from mock import patch

from django.test import TestCase
from django.http import HttpRequest
from utils.test_helper import RedshiftTestCase

import dash.models
from reports import api_contentads
from reports import redshift

from zemauth.models import User


@patch('reports.redshift.get_cursor')
class ApiContentAdsQueryTest(TestCase):
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

        for constraint in constraints:
            self.assertIn(constraint, query)

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

        stats = api_contentads.query(start_date, end_date, breakdown=breakdown, **constraints)

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

        sql_constraints = ['adgroup_id=', '"date"<=', '"date">=']

        self.check_breakdown(mock_cursor, breakdown)
        self.check_constraints(mock_cursor, sql_constraints)
        self.check_aggregations(mock_cursor)

    def test_query_breakdown_by_content_ad(self, mock_cursor):
        constraints = dict(
            ad_group=1
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        breakdown = ['content_ad']

        api_contentads.query(start_date, end_date, breakdown=breakdown, **constraints)
        sql_constraints = ['adgroup_id=', '"date"<=', '"date">=']

        self.check_breakdown(mock_cursor, breakdown)
        self.check_constraints(mock_cursor, sql_constraints)
        self.check_aggregations(mock_cursor)

    def test_query_breakdown_by_date(self, mock_cursor):
        constraints = dict(
            ad_group=1
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        breakdown = ['date']
        api_contentads.query(start_date, end_date, breakdown=breakdown, **constraints)
        sql_constraints = ['adgroup_id=', '"date"<=', '"date">=']

        self.check_breakdown(mock_cursor, breakdown)
        self.check_constraints(mock_cursor, sql_constraints)
        self.check_aggregations(mock_cursor)

    def test_query_filter_by_date(self, mock_cursor):
        constraints = dict(
            date=datetime.date(2015, 2, 1),
        )
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        api_contentads.query(start_date, end_date, breakdown=[], **constraints)
        sql_constraints = ['date=', '"date"<=', '"date">=']

        self.check_constraints(mock_cursor, sql_constraints)
        self.check_aggregations(mock_cursor)

    def test_query_ignore_diff_rows(self, mock_cursor):
        constraints = dict()
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        api_contentads.query(start_date, end_date, breakdown=[], ignore_diff_rows=True, **constraints)
        sql_constraints = ['"date"<=', '"date">=', 'content_ad_id!=']

        self.check_constraints(mock_cursor, sql_constraints)
        self.check_aggregations(mock_cursor)

    def test_remove_contentadstats(self, mock_cursor):
        api_contentads.remove_contentadstats([1, 2, 3])
        query = self._get_query(mock_cursor)
        self.assertEqual(query, 'DELETE FROM "contentadstats" WHERE (content_ad_id IN (%s,%s,%s))')


class ApiContentAdsPostclickRedshiftTest(RedshiftTestCase):
    fixtures = ['test_api_contentads.stats.yaml', 'test_api_contentads.yaml']

    def setUp(self):
        self.request = HttpRequest()
        user = User.objects.get(pk=1)
        self.request.user = user

        super(ApiContentAdsPostclickRedshiftTest, self).setUp()

    def test_has_complete_postclick_metrics(self):
        ad_groups = dash.models.AdGroup.objects.filter(pk__in=[1])
        sources = dash.models.Source.objects.filter(pk__in=[1])
        self.assertEqual(len(ad_groups), 1)
        self.assertEqual(len(sources), 1)

        result = api_contentads.has_complete_postclick_metrics_ad_groups(
            start_date=datetime.datetime(2014, 6, 15),
            end_date=datetime.datetime(2014, 6, 17),
            ad_groups=ad_groups,
            sources=sources)
        self.assertTrue(result)

        result = api_contentads.has_complete_postclick_metrics_ad_groups(
            start_date=datetime.datetime(2014, 6, 15),
            end_date=datetime.datetime(2014, 6, 18),  # no metrics on this date
            ad_groups=ad_groups,
            sources=sources)
        self.assertFalse(result)

        # archived ad group
        ad_group_1 = dash.models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group_1.get_current_settings()
        ad_group_settings.archived = True
        ad_group_settings.save(self.request)

        cursor = redshift.get_cursor()

        ad_groups = dash.models.AdGroup.objects.filter(pk__in=[1, 2, 3])
        result = api_contentads._get_ad_group_ids_with_postclick_data(
            cursor,
            level_constraints_ids={'ad_group': [x.pk for x in ad_groups]},
            exclude_archived=True)
        self.assertEqual(result, [])

        # account level archived ad group
        accounts = dash.models.Account.objects.filter(pk__in=[1])
        result = api_contentads._get_ad_group_ids_with_postclick_data(
            cursor,
            level_constraints_ids={'account': [x.pk for x in accounts]},
            exclude_archived=True)
        self.assertEqual(result, [])

        # ad group is not archived
        ad_group_settings.archived = False
        ad_group_settings.save(self.request)

        ad_groups = dash.models.AdGroup.objects.filter(pk__in=[1, 2, 3])
        result = api_contentads._get_ad_group_ids_with_postclick_data(
            cursor,
            level_constraints_ids={'ad_group': [x.pk for x in ad_groups]},
            exclude_archived=False)
        self.assertEqual(result, [1])

        # account level not archived
        accounts = dash.models.Account.objects.filter(pk__in=[1])
        result = api_contentads._get_ad_group_ids_with_postclick_data(
            cursor,
            level_constraints_ids={'account': [x.pk for x in accounts]},
            exclude_archived=False)
        self.assertEqual(result, [1])

        result = api_contentads.has_complete_postclick_metrics_accounts(
            start_date=datetime.datetime(2014, 6, 15),
            end_date=datetime.datetime(2014, 6, 17),
            accounts=accounts,
            sources=sources)
        self.assertTrue(result)

        result = api_contentads.has_complete_postclick_metrics_accounts(
            start_date=datetime.datetime(2014, 6, 15),
            end_date=datetime.datetime(2014, 6, 18),
            accounts=accounts,
            sources=sources)
        self.assertFalse(result)

