import datetime
import re
# import backtosql
import unittest

from django.test import TestCase

from redshiftapi import api_breakdowns
from redshiftapi import queries
from redshiftapi import models


def _stripWhitespace(q):
    return re.sub(r"[\n\r\s]+", '', q)


@unittest.skip("backtosql is currently not included")
class APIBreakdownsTest(TestCase):

    def assertSQLQueriesEqual(self, q1, q2):
        backtosql.printsql(q1)
        q1 = _stripWhitespace(q1).upper()
        q2 = _stripWhitespace(q2).upper()
        self.assertEqual(q1, q2)

    def test_get_default_context_constraints(self):

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
        }

        breakdown_constraints = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
        ]

        context = queries._get_default_context(
            models.RSContentAdStats,
            ['account_id', 'source_id'],
            constraints,
            breakdown_constraints,
            '-clicks',
            2,
            33
        )
        q = context['constraints']
        self.assertEqual(
            q.generate('A'),
            "(A.account_id=%s AND A.campaign_id=%s)")
        self.assertEqual(q.get_params(), [123, 223])

        q = context['breakdown_constraints']
        self.assertEqual(
            q.generate('A'),
            "((A.content_ad_id=%s AND A.source_id=%s) OR (A.content_ad_id=%s AND A.source_id=ANY(%s)))")
        self.assertEqual(q.get_params(), [32, 1, 33, [2, 3]])

        self.assertEqual(context['offset'], 2)
        self.assertEqual(context['limit'], 33)

    def test_prepare_query(self):
        breakdown = ['ad_group_id', 'content_ad_id']
        constraints = {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 1, 31),
            'account_id': [1, 2, 3],
            'campaign_id': 22,
        }
        breakdown_constraints = [
            {'content_ad_id': 112}
        ]
        order = '-campaign_id'

        query, params = api_breakdowns._prepare_query(
            models.RSContentAdStats,
            breakdown, constraints, breakdown_constraints, order, 10, 50)

        self.assertEquals(params,
                          [[1, 2, 3], 22, datetime.date(2016, 1, 1), datetime.date(2016, 1, 31), 112])

        self.assertSQLQueriesEqual(query, """
        SELECT a.ad_group_id,
            a.content_ad_id,
            (CASE
                    WHEN sum(a.visits) <> 0 THEN sum(cast(a.total_time_on_site AS FLOAT)) / sum(a.visits)
                    ELSE NULL
                END) avg_tos,
            (sum(a.effective_cost_nano)+
            sum(a.effective_data_cost_nano)+sum(a.license_fee_nano))/1000000000.0 billing_cost,
            (CASE
                    WHEN sum(a.visits) <> 0 THEN sum(cast(a.bounced_visits AS FLOAT)) / sum(a.visits)
                    ELSE NULL
                END)*100.0 bounce_rate,
            (CASE
                    WHEN sum(a.clicks) = 0 THEN NULL
                    WHEN sum(a.visits) = 0 THEN 1
                    WHEN sum(a.clicks) < sum(a.visits) THEN 0
                    ELSE (sum(cast(a.clicks AS FLOAT)) - sum(a.visits)) / sum(a.clicks)
                END)*100.0 click_discrepancy,
            sum(a.clicks) clicks,
            sum(a.cost_cc)/10000.0 cost,
            (CASE
                    WHEN sum(a.clicks) <> 0 THEN sum(cast(a.cost_cc AS FLOAT)) / sum(a.clicks)
                    ELSE NULL
                END)/10000.0 cpc,
            (CASE
                    WHEN sum(a.impressions) <> 0 THEN sum(cast(a.clicks AS FLOAT)) / sum(a.impressions)
                    ELSE NULL
                END)*100.0 ctr,
            sum(a.data_cost_cc)/10000.0 data_cost,
            sum(a.effective_data_cost_nano)/1000000000.0 e_data_cost,
            sum(a.effective_cost_nano)/1000000000.0 e_media_cost,
            sum(a.impressions) impressions,
            sum(a.license_fee_nano)/1000000000.0 license_fee,
            sum(a.cost_cc)/10000.0 media_cost,
            sum(a.new_visits) new_visits,
            sum(a.pageviews) pageviews,
            (CASE
                    WHEN sum(a.visits) <> 0 THEN sum(cast(a.new_visits AS FLOAT)) / sum(a.visits)
                    ELSE NULL
                END)*100.0 percent_new_users,
            (CASE
                    WHEN sum(a.visits) <> 0 THEN sum(cast(a.pageviews AS FLOAT)) / sum(a.visits)
                    ELSE NULL
                END) pv_per_visit,
            (sum(a.license_fee_nano)+sum(a.cost_cc)*100000+sum(a.data_cost_cc)*100000)/1000000000.0 total_cost,
            sum(a.visits) visits
        FROM
        (SELECT b.adgroup_id AS ad_group_id,
                                b.content_ad_id AS content_ad_id,
                                                    sum(b.clicks) clicks,
                                                    sum(b.impressions) impressions,
                                                    sum(b.cost_cc) cost_cc,
                                                    sum(b.data_cost_cc) data_cost_cc,
                                                    sum(b.effective_cost_nano) effective_cost_nano,
                                                    sum(b.effective_data_cost_nano) effective_data_cost_nano,
                                                    sum(b.license_fee_nano) license_fee_nano,
                                                    sum(b.visits) visits,
                                                    sum(b.new_visits) new_visits,
                                                    sum(b.bounced_visits) bounced_visits,
                                                    sum(b.pageviews) pageviews,
                                                    sum(b.total_time_on_site) total_time_on_site,
                                                    row_number() over (partition BY b.adgroup_id
                                                                    ORDER BY b.campaign_id DESC) AS r
        FROM contentadstats b
        WHERE (b.account_id=any(%s)
                AND b.campaign_id=%s
                AND trunc(b.date)>=%s
                AND trunc(b.date)<=%s)
        AND (b.content_ad_id=%s)
        GROUP BY ad_group_id,
                content_ad_id) a
        WHERE r >= 10 AND r <= 50
        GROUP BY 1,
                2
        """)
