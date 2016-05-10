import datetime
import re
import backtosql.helpers

from django.test import TestCase

from redshiftapi import api_breakdowns
from redshiftapi import models


def _stripWhitespace(q):
    return re.sub(r"\s+", '', q)


class APIBreakdownsTest(TestCase):

    def assertSQLQueriesEqual(self, q1, q2):
        q1 = _stripWhitespace(q1)
        q2 = _stripWhitespace(q2)
        self.assertEqual(q1, q2)

    def test_prepare_constraints(self):

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
        }
        breakdown_constraints = [
            {'content_ad_id': 132, 'source_id': 1},
            {'content_ad_id': 133, 'source_id': [2, 3]},
        ]
        q = api_breakdowns._prepare_constraints(models.RSContentAdStats, constraints, breakdown_constraints)
        self.assertEqual(
            q.g('A'),
            "((A.account_id=%s AND A.campaign_id=%s) AND ((A.content_ad_id=%s AND A.source_id=%s) OR (A.content_ad_id=%s AND A.source_id IN %s)))")
        self.assertEqual(q.get_params(), [123, 223, 132, 1, 133, [2, 3]])


    def test_prepare_query(self):
        breakdown = ['ad_group_id']
        constraints = {
            'dt__gte': datetime.date(2016, 1, 1),
            'dt__lte': datetime.date(2016, 1, 31),
            'account_id': [1, 2, 3],
            'campaign_id': 22,
        }
        breakdown_constraints = [
            {'content_ad_id': 112, 'source_id': [1, 2, 4]}
        ]
        order = ['-campaign_id']

        page = 1
        page_size = 50

        query, params = api_breakdowns._prepare_query(
            models.RSContentAdStats,
            breakdown, constraints, breakdown_constraints, order, page, page_size)

        self.assertEquals(params,
                          [[1, 2, 3], 22, datetime.date(2016, 1, 1), datetime.date(2016, 1, 31), 112, [1, 2, 4]])

        self.assertSQLQueriesEqual(query, """SELECT a.adgroup_id AS ad_group_id,
            (CASE
                    WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.total_time_on_site AS FLOAT)) / SUM(a.visits)
                    ELSE NULL
                END) avg_tos,
            (SUM(a.effective_cost_nano)+SUM(a.effective_data_cost_nano)+SUM(a.license_fee_nano))/1000000000.0 billing_cost,
            (CASE
                    WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.bounced_visits AS FLOAT)) / SUM(a.visits)
                    ELSE NULL
                END)*100.0 bounce_rate,
            (CASE
                    WHEN SUM(a.clicks) = 0 THEN NULL
                    WHEN SUM(a.visits) = 0 THEN 1
                    WHEN SUM(a.clicks) < SUM(a.visits) THEN 0
                    ELSE (SUM(CAST(a.clicks AS FLOAT)) - SUM(a.visits)) / SUM(a.clicks)
                END)*100.0 click_discrepancy,
            SUM(a.clicks) clicks,
            SUM(a.cost_cc)/10000.0 cost,
            (CASE
                    WHEN SUM(a.clicks) <> 0 THEN SUM(CAST(a.cost_cc AS FLOAT)) / SUM(a.clicks)
                    ELSE NULL
                END)/10000.0 cpc,
            (CASE
                    WHEN SUM(a.impressions) <> 0 THEN SUM(CAST(a.clicks AS FLOAT)) / SUM(a.impressions)
                    ELSE NULL
                END)*100.0 ctr,
            SUM(a.data_cost_cc)/10000.0 data_cost,
            SUM(a.effective_data_cost_nano)/1000000000.0 e_data_cost,
            SUM(a.effective_cost_nano)/1000000000.0 e_media_cost,
            SUM(a.impressions) impressions,
            SUM(a.license_fee_nano)/1000000000.0 license_fee,
            SUM(a.cost_cc)/10000.0 media_cost,
            SUM(a.new_visits) new_visits,
            SUM(a.pageviews) pageviews,
            (CASE
                    WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.new_visits AS FLOAT)) / SUM(a.visits)
                    ELSE NULL
                END)*100.0 percent_new_users,
            (CASE
                    WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.pageviews AS FLOAT)) / SUM(a.visits)
                    ELSE NULL
                END) pv_per_visit,
            (SUM(a.license_fee_nano)+SUM(a.cost_cc)*100000+SUM(a.data_cost_cc)*100000)/1000000000.0 total_cost,
            SUM(a.visits) visits
        FROM contentadstats a
        WHERE ((a.account_id IN %s
                AND a.campaign_id=%s
                AND TRUNC(a.dt)>=%s
                AND TRUNC(a.dt)<=%s)
            AND (a.content_ad_id=%s
                    AND a.source_id IN %s))
        ORDER BY a.campaign_id DESC LIMIT 50 ;
        """)
