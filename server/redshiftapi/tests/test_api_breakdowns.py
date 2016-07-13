import backtosql
import datetime
import re
import unittest

from django.test import TestCase

from redshiftapi import api_breakdowns
from redshiftapi import queries
from redshiftapi import models


class APIBreakdownsTest(TestCase, backtosql.TestSQLMixin):

    def test_prepare_query(self):
        breakdown = ['ad_group_id', 'content_ad_id']
        constraints = {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 1, 31),
            'account_id': [1, 2, 3],
            'campaign_id': 22,
        }
        breakdown_constraints = [
            {'content_ad_id': 112, 'source_id': 55},
            {'content_ad_id': 12, 'source_id': [2, 1]},
        ]
        order = '-campaign_id'

        query, params = api_breakdowns._prepare_query(
            models.MVMaster(),
            breakdown, constraints, breakdown_constraints, order, 10, 50)

        self.assertEquals(params,
                          [
                              [1, 2, 3], 22, datetime.date(2016, 1, 1), datetime.date(2016, 1, 31),
                              112, 55, 12, [2, 1]
                          ])

        self.assertSQLEquals(query, """
        WITH temp_base AS
            (SELECT a.ad_group_id AS ad_group_id,
                    a.content_ad_id AS content_ad_id,
                    (CASE WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.total_time_on_site AS FLOAT)) / SUM(a.visits) ELSE NULL END) avg_tos,
                    (SUM(a.effective_cost_nano)+SUM(a.effective_data_cost_nano)+SUM(a.license_fee_nano))/1000000000.0 billing_cost,
                    (CASE WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.bounced_visits AS FLOAT)) / SUM(a.visits) ELSE NULL END)*100.0 bounce_rate,
                    (CASE WHEN SUM(a.clicks) = 0 THEN NULL WHEN SUM(a.visits) = 0 THEN 1 WHEN SUM(a.clicks) < SUM(a.visits) THEN 0 ELSE (SUM(CAST(a.clicks AS FLOAT)) - SUM(a.visits)) / SUM(a.clicks) END)*100.0 click_discrepancy,
                    SUM(a.clicks) clicks,
                    SUM(a.cost_nano)/1000000000.0 cost,
                    (CASE WHEN SUM(a.clicks) <> 0 THEN SUM(CAST(a.cost_nano AS FLOAT)) / SUM(a.clicks) ELSE NULL END)/1000000000.0 cpc,
                    (CASE WHEN SUM(a.impressions) <> 0 THEN SUM(CAST(a.clicks AS FLOAT)) / SUM(a.impressions) ELSE NULL END)*100.0 ctr,
                    SUM(a.data_cost_nano)/1000000000.0 data_cost,
                    SUM(a.effective_data_cost_nano)/1000000000.0 e_data_cost,
                    SUM(a.effective_cost_nano)/1000000000.0 e_media_cost,
                    SUM(a.impressions) impressions,
                    SUM(a.license_fee_nano)/1000000000.0 license_fee,
                    SUM(a.cost_nano)/1000000000.0 media_cost,
                    SUM(a.new_visits) new_visits,
                    SUM(a.pageviews) pageviews,
                    (CASE WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.new_visits AS FLOAT)) / SUM(a.visits) ELSE NULL END)*100.0 percent_new_users,
                    (CASE WHEN SUM(a.visits) <> 0 THEN SUM(CAST(a.pageviews AS FLOAT)) / SUM(a.visits) ELSE NULL END) pv_per_visit,
                    (SUM(a.license_fee_nano)+SUM(a.cost_nano)+SUM(a.data_cost_nano))/1000000000.0 total_cost,
                    SUM(a.visits) visits
            FROM mv_content_ad a
            WHERE (a.account_id=ANY(%s)
                    AND a.campaign_id=%s
                    AND a.date>=%s
                    AND a.date<=%s)
                AND ((a.content_ad_id=%s
                    AND a.source_id=%s)
                    OR (a.content_ad_id=%s
                        AND a.source_id=ANY(%s)))
            GROUP BY ad_group_id,
                        content_ad_id)

            SELECT b.ad_group_id,
                b.content_ad_id,
                b.avg_tos,
                b.billing_cost,
                b.bounce_rate,
                b.click_discrepancy,
                b.clicks,
                b.cost,
                b.cpc,
                b.ctr,
                b.data_cost,
                b.e_data_cost,
                b.e_media_cost,
                b.impressions,
                b.license_fee,
                b.media_cost,
                b.new_visits,
                b.pageviews,
                b.percent_new_users,
                b.pv_per_visit,
                b.total_cost,
                b.visits
            FROM
            (SELECT temp_base.ad_group_id,
                    temp_base.content_ad_id,
                    temp_base.avg_tos,
                    temp_base.billing_cost,
                    temp_base.bounce_rate,
                    temp_base.click_discrepancy,
                    temp_base.clicks,
                    temp_base.cost,
                    temp_base.cpc,
                    temp_base.ctr,
                    temp_base.data_cost,
                    temp_base.e_data_cost,
                    temp_base.e_media_cost,
                    temp_base.impressions,
                    temp_base.license_fee,
                    temp_base.media_cost,
                    temp_base.new_visits,
                    temp_base.pageviews,
                    temp_base.percent_new_users,
                    temp_base.pv_per_visit,
                    temp_base.total_cost,
                    temp_base.visits,
                    ROW_NUMBER() OVER (PARTITION BY temp_base.ad_group_id
                                                ORDER BY temp_base.campaign_id DESC) AS r
            FROM temp_base) b
            WHERE r >= 10 + 1
            AND r <= 50
            """)
