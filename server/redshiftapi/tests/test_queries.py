import backtosql
import copy
import datetime
import mock

from django.test import TestCase

from stats import constants
from stats.helpers import Goals
from utils import exc

import dash.models

from redshiftapi import queries
from redshiftapi import models


class PrepareQueryAllTest(TestCase, backtosql.TestSQLMixin):

    @mock.patch.object(models.MVMaster, 'get_aggregates', return_value=[models.MVMaster.clicks])
    def test_query_all_base(self, _):
        sql, params = queries.prepare_query_all_base(
            ['account_id', 'source_id', 'dma'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            False
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.dma AS dma,
            SUM(base_table.clicks) clicks
        FROM mv_account_delivery_geo base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
            AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY clicks DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, dma ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    @mock.patch.object(models.MVMaster, 'get_aggregates', return_value=[models.MVMaster.clicks])
    def test_query_all_base_totals(self, _):
        sql, params = queries.prepare_query_all_base(
            [],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            None,
            False
        )

        self.assertSQLEquals(sql, """
        SELECT
            SUM(base_table.clicks) clicks
        FROM mv_account base_table
        WHERE ( base_table.date >=%s AND base_table.date <=%s)
        ORDER BY clicks DESC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8)])

    @mock.patch.object(models.MVMaster, 'get_aggregates', return_value=[
        models.MVMasterPublishers.clicks, models.MVMasterPublishers.external_id, models.MVMasterPublishers.publisher_id])
    def test_query_all_base_publishers(self, _):
        sql, params = queries.prepare_query_all_base(
            ['publisher_id', 'dma'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            None,
            True
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.dma AS dma,
            SUM(base_table.clicks) clicks,
            MAX(base_table.external_id) AS external_id,
            MAX(base_table.publisher || '__' || base_table.source_id) publisher_id
        FROM mv_pubs_master base_table
        WHERE ( base_table.date >=%s AND base_table.date <=%s)
        GROUP BY 1, 2, 3
        ORDER BY clicks DESC NULLS LAST, publisher_id ASC NULLS LAST, dma ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8)])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 10, 3))
    def test_query_all_yesterday(self, _):
        sql, params = queries.prepare_query_all_yesterday(
            ['account_id', 'source_id', 'dma'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            False
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.dma AS dma,
            (NVL(SUM(base_table.cost_nano), 0) + NVL(SUM(base_table.data_cost_nano), 0))/1000000000.0 yesterday_cost,
            (NVL(SUM(base_table.effective_cost_nano), 0) + NVL(SUM(base_table.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost
        FROM mv_account_delivery_geo base_table
        WHERE (( base_table.date = %s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY yesterday_cost DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, dma ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 10, 2), 1, 2])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 10, 3))
    def test_query_all_yesterday_publishers(self, _):
        sql, params = queries.prepare_query_all_yesterday(
            ['publisher_id', 'day'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            True
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.date AS day,
            (NVL(SUM(base_table.cost_nano), 0) + NVL(SUM(base_table.data_cost_nano), 0))/1000000000.0 yesterday_cost,
            (NVL(SUM(base_table.effective_cost_nano), 0) + NVL(SUM(base_table.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
            MAX(base_table.publisher || '__' || base_table.source_id) publisher_id
        FROM mv_pubs_ad_group base_table
        WHERE (( base_table.date = %s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY yesterday_cost DESC NULLS LAST, publisher_id ASC NULLS LAST, day ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 10, 2), 1, 2])

    def test_query_all_conversions(self):
        sql, params = queries.prepare_query_all_conversions(
            ['account_id', 'source_id', 'slug'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            False
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.slug AS slug,
            SUM(base_table.conversion_count) count
        FROM mv_conversions_account base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY count DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, slug ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_all_conversions_publishers(self):
        sql, params = queries.prepare_query_all_conversions(
            ['publisher_id', 'day'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            True
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.date AS day,
            SUM(base_table.conversion_count) count,
            MAX(base_table.publisher || '__' || base_table.source_id) publisher_id
        FROM mv_conversions base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY count DESC NULLS LAST, publisher_id ASC NULLS LAST, day ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_all_touchpoints(self):
        sql, params = queries.prepare_query_all_touchpoints(
            ['account_id', 'source_id', 'slug', 'window'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            False
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.slug AS slug,
            base_table.conversion_window AS window,
            SUM(base_table.conversion_count) count
        FROM mv_touch_account base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3, 4
        ORDER BY count DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, slug ASC NULLS LAST, window ASC NULLS LAST
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_all_touchpoints_publishers(self):
        sql, params = queries.prepare_query_all_touchpoints(
            ['publisher_id', 'day', 'slug', 'window'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            True
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.date AS day,
            base_table.slug AS slug,
            base_table.conversion_window AS window,
            SUM(base_table.conversion_count) count,
            MAX(base_table.publisher || '__' || base_table.source_id) publisher_id
        FROM mv_touchpointconversions base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY count DESC NULLS LAST, publisher_id ASC NULLS LAST, day ASC NULLS LAST, slug ASC NULLS LAST, window ASC NULLS LAST""")

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_structure_with_stats(self):
        sql, params = queries.prepare_query_structure_with_stats(
            ['account_id', 'source_id', 'dma'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            False
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.dma AS dma
        FROM mv_account_delivery_geo base_table
        WHERE ( base_table.date >=%s AND base_table.date <=%s)
        GROUP BY 1, 2, 3;
        """)

        self.assertEquals(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8)])


class PrepareQueryJointTest(TestCase, backtosql.TestSQLMixin):

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMaster, 'get_aggregates',
                       return_value=[models.MVJointMaster.clicks, models.MVJointMaster.total_seconds])
    def test_query_joint_base(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        goals = Goals(None, None, None, None, None)

        sql, params = queries.prepare_query_joint_base(['account_id'], constraints, None, [
                                                       'total_seconds'], 5, 10, goals, False)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.account_id AS account_id,
                    (NVL(SUM(a.effective_cost_nano), 0) + NVL(SUM(a.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
                    (NVL(SUM(a.cost_nano), 0) + NVL(SUM(a.data_cost_nano), 0))/1000000000.0 yesterday_cost
                FROM mv_account a
                WHERE (a.date=%s)
                GROUP BY 1
            ),
            temp_base AS (
                SELECT
                    a.account_id AS account_id,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_account a
                WHERE (a.date>=%s AND a.date<=%s)
                GROUP BY 1
            )
        SELECT
            temp_base.account_id,
            temp_base.clicks,
            temp_base.total_seconds,
            temp_yesterday.e_yesterday_cost,
            temp_yesterday.yesterday_cost
        FROM temp_base NATURAL LEFT JOIN temp_yesterday
        ORDER BY total_seconds ASC NULLS LAST
        LIMIT 10
        OFFSET 5
        """)

        self.assertEquals(params, [
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMasterPublishers, 'get_aggregates',
                       return_value=[models.MVJointMasterPublishers.clicks, models.MVJointMasterPublishers.total_seconds])
    def test_query_joint_base_publishers(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        goals = Goals(None, None, None, None, None)

        sql, params = queries.prepare_query_joint_base(['publisher_id'], constraints, None, [
                                                       'total_seconds'], 5, 10, goals, True)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    (NVL(SUM(a.effective_cost_nano), 0) + NVL(SUM(a.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
                    (NVL(SUM(a.cost_nano), 0) + NVL(SUM(a.data_cost_nano), 0))/1000000000.0 yesterday_cost
                FROM mv_pubs_ad_group a
                WHERE (a.date=%s)
                GROUP BY 1, 2
            ),
            temp_base AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_pubs_ad_group a
                WHERE (a.date>=%s AND a.date<=%s)
                GROUP BY 1, 2
            )
        SELECT
            temp_base.publisher,
            temp_base.source_id,
            temp_base.clicks,
            temp_base.total_seconds,
            temp_yesterday.e_yesterday_cost,
            temp_yesterday.yesterday_cost
        FROM temp_base NATURAL LEFT JOIN temp_yesterday
        ORDER BY total_seconds ASC NULLS LAST
        LIMIT 10
        OFFSET 5
        """)

        self.assertEquals(params, [
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMaster, 'get_aggregates',
                       return_value=[models.MVJointMaster.clicks, models.MVJointMaster.total_seconds])
    def test_query_joint_levels(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        goals = Goals(None, None, None, None, None)

        sql, params = queries.prepare_query_joint_levels(
            ['account_id', 'campaign_id'], constraints, None, ['total_seconds', 'account_id', 'campaign_id'], 5, 10, goals, False)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    (NVL(SUM(a.effective_cost_nano), 0) + NVL(SUM(a.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
                    (NVL(SUM(a.cost_nano), 0) + NVL(SUM(a.data_cost_nano), 0))/1000000000.0 yesterday_cost
                FROM mv_campaign a
                WHERE (a.date=%s)
                GROUP BY 1, 2
            ),
            temp_base AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_campaign a
                WHERE (a.date>=%s AND a.date<=%s)
                GROUP BY 1, 2
            )
        SELECT
            b.account_id,
            b.campaign_id,
            b.clicks,
            b.total_seconds,
            b.e_yesterday_cost,
            b.yesterday_cost
        FROM
            (SELECT a.account_id,
                    a.campaign_id,
                    a.clicks,
                    a.total_seconds,
                    a.e_yesterday_cost,
                    a.yesterday_cost,
                    ROW_NUMBER() OVER (PARTITION BY a.account_id
                                        ORDER BY a.total_seconds ASC NULLS LAST,
                                                 a.account_id ASC NULLS LAST,
                                                 a.campaign_id ASC NULLS LAST) AS r
            FROM
                (SELECT temp_base.account_id,
                        temp_base.campaign_id,
                        temp_base.clicks,
                        temp_base.total_seconds,
                        temp_yesterday.e_yesterday_cost,
                        temp_yesterday.yesterday_cost
                FROM temp_base NATURAL
                LEFT OUTER JOIN temp_yesterday
                ) a
            ) b
        WHERE r >= 5+1 AND r <= 10
        """)

        self.assertEquals(params, [
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMasterPublishers, 'get_aggregates',
                       return_value=[models.MVJointMasterPublishers.clicks, models.MVJointMasterPublishers.total_seconds])
    def test_query_joint_levels_publishers(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        goals = Goals(None, None, None, None, None)

        sql, params = queries.prepare_query_joint_levels(
            ['publisher_id', 'dma'], constraints, None, ['total_seconds'], 5, 10, goals, True)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    a.dma AS dma,
                    (NVL(SUM(a.effective_cost_nano), 0) + NVL(SUM(a.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
                    (NVL(SUM(a.cost_nano), 0) + NVL(SUM(a.data_cost_nano), 0))/1000000000.0 yesterday_cost
                FROM mv_pubs_master a
                WHERE (a.date=%s)
                GROUP BY 1, 2, 3
            ),
            temp_base AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    a.dma AS dma,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_pubs_master a
                WHERE (a.date>=%s AND a.date<=%s)
                GROUP BY 1, 2, 3
            )
        SELECT
            b.publisher,
            b.source_id,
            b.dma,
            b.clicks,
            b.total_seconds,
            b.e_yesterday_cost,
            b.yesterday_cost
        FROM
            (SELECT a.publisher,
                    a.source_id,
                    a.dma,
                    a.clicks,
                    a.total_seconds,
                    a.e_yesterday_cost,
                    a.yesterday_cost ,
                    ROW_NUMBER() OVER (PARTITION BY a.publisher, a.source_id
                                        ORDER BY a.total_seconds ASC NULLS LAST ) AS r
            FROM
                (SELECT temp_base.publisher,
                        temp_base.source_id,
                        temp_base.dma,
                        temp_base.clicks,
                        temp_base.total_seconds,
                        temp_yesterday.e_yesterday_cost,
                        temp_yesterday.yesterday_cost
                FROM temp_base NATURAL LEFT OUTER JOIN temp_yesterday
                ) a
            ) b
        WHERE r >= 5+1 AND r <= 10
        """)

        self.assertEquals(params, [
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])


class PrepareQueryJointConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_augmenter.yaml']

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMaster, 'get_aggregates',
                       return_value=[models.MVJointMaster.clicks, models.MVJointMaster.total_seconds])
    def test_query_joint_base(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        campaign = dash.models.Campaign.objects.get(id=1)
        campaign_goals = dash.models.CampaignGoal.objects.filter(campaign_id=campaign.id)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)
        campaign_goal_values = dash.models.CampaignGoalValue.objects.all()

        goals = Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, None)

        sql, params = queries.prepare_query_joint_base(['account_id'], constraints, None, [
                                                       'total_seconds'], 5, 10, goals, False)

        self.assertSQLEquals(sql, """
        WITH temp_conversions AS (
         SELECT   a.account_id AS account_id ,
                  SUM (CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2,
                  SUM (CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3,
                  SUM (CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4,
                  SUM (CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5
         FROM     mv_conversions_account a
         WHERE    (a.DATE >=%s AND a.DATE <=%s)
         GROUP BY 1 ),
        temp_touchpoints AS (
         SELECT   a.account_id AS account_id ,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24 THEN conversion_count ELSE 0 END) pixel_1_24,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168 THEN conversion_count ELSE 0 END) pixel_1_168,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720 THEN conversion_count ELSE 0 END) pixel_1_720,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=2160 THEN conversion_count ELSE 0 END) pixel_1_2160
         FROM     mv_touch_account a
         WHERE    (a.DATE >=%s AND a.DATE <=%s)
         GROUP BY 1 ),
        temp_yesterday AS (
         SELECT   a.account_id AS account_id ,
                  (NVL(SUM(a.effective_cost_nano), 0) + NVL(SUM(a.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
                  (NVL(SUM(a.cost_nano), 0) + NVL(SUM(a.data_cost_nano), 0))/1000000000.0 yesterday_cost
         FROM     mv_account a
         WHERE    (a.DATE =%s)
         GROUP BY 1 ),
        temp_base AS (
         SELECT   a.account_id AS account_id ,
                  SUM(a.clicks) clicks,
                  SUM(a.total_time_on_site) total_seconds
         FROM     mv_account a
         WHERE    (a.DATE >=%s AND a.DATE <=%s)
         GROUP BY 1 )
        SELECT  temp_base.account_id,
                temp_base.clicks,
                temp_base.total_seconds,
                temp_yesterday.e_yesterday_cost,
                temp_yesterday.yesterday_cost ,
                temp_conversions.conversion_goal_2,
                temp_conversions.conversion_goal_3,
                temp_conversions.conversion_goal_4,
                temp_conversions.conversion_goal_5 ,
                temp_touchpoints.pixel_1_24,
                temp_touchpoints.pixel_1_168,
                temp_touchpoints.pixel_1_720,
                temp_touchpoints.pixel_1_2160 ,
                e_media_cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2 ,
                e_media_cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3 ,
                e_media_cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4 ,
                e_media_cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5 ,
                e_media_cost / NULLIF(pixel_1_24, 0)        avg_cost_per_pixel_1_24 ,
                e_media_cost / NULLIF(pixel_1_168, 0)       avg_cost_per_pixel_1_168 ,
                e_media_cost / NULLIF(pixel_1_720, 0)       avg_cost_per_pixel_1_720 ,
                e_media_cost / NULLIF(pixel_1_2160, 0)      avg_cost_per_pixel_1_2160 ,
                CASE
                    WHEN TRUE AND TRUNC(NVL(e_media_cost, 0), 2) > 0
                            AND NVL(TRUNC(CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END, 2), 0) = 0
                         THEN 0
                    WHEN (CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END) IS NULL
                            OR 0.50000 IS NULL
                         THEN NULL
                    WHEN TRUE THEN
                         (2 * 0.50000 - TRUNC((CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END), 2)) / NULLIF(0.50000, 0)
                    ELSE TRUNC(CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END, 2) / NULLIF(0.50000, 0)
                    END performance_campaign_goal_1,
                CASE
                        WHEN TRUE AND TRUNC(NVL(e_media_cost, 0), 2) > 0
                                AND NVL(TRUNC(CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END, 2), 0) = 0
                             THEN 0
                        WHEN (CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END) IS NULL
                                OR 3.80000 IS NULL
                             THEN NULL
                        WHEN TRUE THEN
                             (2 * 3.80000 - TRUNC((CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END), 2)) / NULLIF(3.80000, 0)
                        ELSE TRUNC(CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END, 2) / NULLIF(3.80000, 0)
                        END performance_campaign_goal_2
        FROM temp_base NATURAL LEFT JOIN temp_yesterday NATURAL LEFT OUTER JOIN temp_conversions NATURAL LEFT OUTER JOIN temp_touchpoints
        ORDER BY total_seconds ASC NULLS LAST
        LIMIT 10
        OFFSET 5
        """)

        self.assertEquals(params, [
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMaster, 'get_aggregates',
                       return_value=[models.MVJointMaster.clicks, models.MVJointMaster.total_seconds])
    def test_query_joint_levels(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        campaign = dash.models.Campaign.objects.get(id=1)
        campaign_goals = dash.models.CampaignGoal.objects.filter(campaign_id=campaign.id)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)
        campaign_goal_values = dash.models.CampaignGoalValue.objects.all()

        goals = Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, None)

        sql, params = queries.prepare_query_joint_levels(['account_id', 'campaign_id'],
                                                         constraints, None, ['total_seconds'], 5, 10, goals, False)

        self.assertSQLEquals(sql, """
        WITH temp_conversions AS (
         SELECT   a.account_id AS account_id ,
                  a.campaign_id AS campaign_id,
                  SUM (CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2,
                  SUM (CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3,
                  SUM (CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4,
                  SUM (CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5
         FROM     mv_conversions_campaign a
         WHERE    (a.DATE >=%s AND a.DATE <=%s)
         GROUP BY 1, 2 ),
        temp_touchpoints AS (
         SELECT   a.account_id AS account_id ,
                  a.campaign_id AS campaign_id,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24 THEN conversion_count ELSE 0 END) pixel_1_24,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168 THEN conversion_count ELSE 0 END) pixel_1_168,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720 THEN conversion_count ELSE 0 END) pixel_1_720,
                  SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=2160 THEN conversion_count ELSE 0 END) pixel_1_2160
         FROM     mv_touch_campaign a
         WHERE    (a.DATE >=%s AND a.DATE <=%s)
         GROUP BY 1, 2 ),
        temp_yesterday AS (
         SELECT   a.account_id AS account_id ,
                  a.campaign_id AS campaign_id,
                  (NVL(SUM(a.effective_cost_nano), 0) + NVL(SUM(a.effective_data_cost_nano), 0))/1000000000.0 e_yesterday_cost,
                  (NVL(SUM(a.cost_nano), 0) + NVL(SUM(a.data_cost_nano), 0))/1000000000.0 yesterday_cost
         FROM     mv_campaign a
         WHERE    (a.DATE =%s)
         GROUP BY 1, 2 ),
        temp_base AS (
         SELECT   a.account_id AS account_id ,
                  a.campaign_id AS campaign_id,
                  SUM(a.clicks) clicks,
                  SUM(a.total_time_on_site) total_seconds
         FROM     mv_campaign a
         WHERE    (a.DATE >=%s AND a.DATE <=%s)
         GROUP BY 1, 2 )
        SELECT
             b.account_id,
             b.campaign_id,
             b.clicks,
             b.total_seconds,
             b.e_yesterday_cost,
             b.yesterday_cost ,
             b.conversion_goal_2,
             b.conversion_goal_3,
             b.conversion_goal_4,
             b.conversion_goal_5 ,
             b.pixel_1_24,
             b.pixel_1_168,
             b.pixel_1_720,
             b.pixel_1_2160 ,
             b.avg_cost_per_conversion_goal_2,
             b.avg_cost_per_conversion_goal_3,
             b.avg_cost_per_conversion_goal_4,
             b.avg_cost_per_conversion_goal_5,
             b.avg_cost_per_pixel_1_24,
             b.avg_cost_per_pixel_1_168,
             b.avg_cost_per_pixel_1_720,
             b.avg_cost_per_pixel_1_2160,
             b.performance_campaign_goal_1,
             b.performance_campaign_goal_2
        FROM
             (SELECT
                    a.account_id,
                    a.campaign_id,
                    a.clicks,
                    a.total_seconds,
                    a.e_yesterday_cost,
                    a.yesterday_cost ,
                    a.conversion_goal_2,
                    a.conversion_goal_3,
                    a.conversion_goal_4,
                    a.conversion_goal_5 ,
                    a.pixel_1_24,
                    a.pixel_1_168,
                    a.pixel_1_720,
                    a.pixel_1_2160 ,
                    a.avg_cost_per_conversion_goal_2,
                    a.avg_cost_per_conversion_goal_3,
                    a.avg_cost_per_conversion_goal_4,
                    a.avg_cost_per_conversion_goal_5,
                    a.avg_cost_per_pixel_1_24,
                    a.avg_cost_per_pixel_1_168,
                    a.avg_cost_per_pixel_1_720,
                    a.avg_cost_per_pixel_1_2160,
                    a.performance_campaign_goal_1,
                    a.performance_campaign_goal_2,
                    ROW_NUMBER() OVER (PARTITION BY a.account_id ORDER BY a.total_seconds ASC NULLS LAST) AS r
              FROM
                    (SELECT
                        temp_base.account_id,
                        temp_base.campaign_id,
                        temp_base.clicks,
                        temp_base.total_seconds,
                        temp_yesterday.e_yesterday_cost,
                        temp_yesterday.yesterday_cost ,
                        temp_conversions.conversion_goal_2,
                        temp_conversions.conversion_goal_3,
                        temp_conversions.conversion_goal_4,
                        temp_conversions.conversion_goal_5 ,
                        temp_touchpoints.pixel_1_24,
                        temp_touchpoints.pixel_1_168,
                        temp_touchpoints.pixel_1_720,
                        temp_touchpoints.pixel_1_2160 ,
                        e_media_cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2 ,
                        e_media_cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3 ,
                        e_media_cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4 ,
                        e_media_cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5 ,
                        e_media_cost / NULLIF(pixel_1_24, 0)        avg_cost_per_pixel_1_24 ,
                        e_media_cost / NULLIF(pixel_1_168, 0)       avg_cost_per_pixel_1_168 ,
                        e_media_cost / NULLIF(pixel_1_720, 0)       avg_cost_per_pixel_1_720 ,
                        e_media_cost / NULLIF(pixel_1_2160, 0)      avg_cost_per_pixel_1_2160 ,
                        CASE
                            WHEN TRUE AND TRUNC(NVL(e_media_cost, 0), 2) > 0
                                    AND NVL(TRUNC(CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END, 2), 0) = 0
                                THEN 0
                            WHEN (CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END) IS NULL
                                    OR 0.50000 IS NULL
                                THEN NULL
                            WHEN TRUE THEN
                                (2 * 0.50000 - TRUNC((CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END), 2)) / NULLIF(0.50000, 0)
                            ELSE TRUNC(CASE WHEN FALSE THEN e_media_cost / NULLIF(0, 0) ELSE cpc END, 2) / NULLIF(0.50000, 0)
                            END performance_campaign_goal_1,
                        CASE
                                WHEN TRUE AND TRUNC(NVL(e_media_cost, 0), 2) > 0
                                        AND NVL(TRUNC(CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END, 2), 0) = 0
                                    THEN 0
                                WHEN (CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END) IS NULL
                                        OR 3.80000 IS NULL
                                    THEN NULL
                                WHEN TRUE THEN
                                    (2 * 3.80000 - TRUNC((CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END), 2)) / NULLIF(3.80000, 0)
                                ELSE TRUNC(CASE WHEN TRUE THEN e_media_cost / NULLIF(pixel_1_168, 0) ELSE -1 END, 2) / NULLIF(3.80000, 0)
                            END performance_campaign_goal_2
                    FROM temp_base NATURAL LEFT OUTER JOIN temp_yesterday NATURAL LEFT OUTER JOIN temp_conversions NATURAL LEFT OUTER JOIN temp_touchpoints
                    ) a
            ) b
        WHERE r >= 5 + 1
  AND r <= 10
        """)

        self.assertEquals(params, [
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])
