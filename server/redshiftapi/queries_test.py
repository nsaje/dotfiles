import backtosql
import datetime
import mock

from django.test import TestCase

from stats.helpers import Goals

import dash.models

from . import queries
from . import models


class PrepareQueryAllTest(TestCase, backtosql.TestSQLMixin):

    @mock.patch.object(models.MVMaster, 'get_aggregates', return_value=[models.MVMaster.clicks])
    def test_query_all_base(self, _):
        sql, params, _ = queries.prepare_query_all_base(
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
        FROM mv_account_geo base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
            AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY clicks DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, dma ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    @mock.patch.object(models.MVMaster, 'get_aggregates', return_value=[models.MVMaster.clicks])
    def test_query_all_base_totals(self, _):
        sql, params, _ = queries.prepare_query_all_base(
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

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8)])

    @mock.patch.object(models.MVMaster, 'get_aggregates', return_value=[
        models.MVMaster.clicks, models.MVMaster.external_id, models.MVMaster.publisher_id])
    def test_query_all_base_publishers(self, _):
        sql, params, _ = queries.prepare_query_all_base(
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
            MAX(base_table.publisher_source_id) publisher_id
        FROM mv_master_pubs base_table
        WHERE ( base_table.date >=%s AND base_table.date <=%s)
        GROUP BY 1, 2, 3
        ORDER BY clicks DESC NULLS LAST, publisher_id ASC NULLS LAST, dma ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8)])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 10, 3))
    def test_query_all_yesterday(self, _):
        sql, params, _ = queries.prepare_query_all_yesterday(
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
            (COALESCE(SUM(base_table.cost_nano), 0) + COALESCE(SUM(base_table.data_cost_nano), 0))::float/1000000000 yesterday_at_cost,
            (COALESCE(SUM(base_table.local_cost_nano), 0) + COALESCE(SUM(base_table.local_data_cost_nano), 0))::float/1000000000 local_yesterday_at_cost,
            (COALESCE(SUM(base_table.effective_cost_nano), 0) + COALESCE(SUM(base_table.effective_data_cost_nano), 0))::float/1000000000 yesterday_et_cost,
            (COALESCE(SUM(base_table.local_effective_cost_nano), 0) + COALESCE(SUM(base_table.local_effective_data_cost_nano), 0))::float/1000000000 local_yesterday_et_cost,
            (COALESCE(SUM(base_table.effective_cost_nano), 0) + COALESCE(SUM(base_table.effective_data_cost_nano), 0) + COALESCE(SUM(base_table.license_fee_nano), 0) + COALESCE(SUM(base_table.margin_nano), 0))::float/1000000000 yesterday_etfm_cost,
            (COALESCE(SUM(base_table.local_effective_cost_nano), 0) + COALESCE(SUM(base_table.local_effective_data_cost_nano), 0) + COALESCE(SUM(base_table.local_license_fee_nano), 0) + COALESCE(SUM(base_table.local_margin_nano), 0))::float/1000000000 local_yesterday_etfm_cost,
            (COALESCE(SUM(base_table.cost_nano), 0) + COALESCE(SUM(base_table.data_cost_nano), 0))::float/1000000000 yesterday_cost,
            (COALESCE(SUM(base_table.local_cost_nano), 0) + COALESCE(SUM(base_table.local_data_cost_nano), 0))::float/1000000000 local_yesterday_cost,
            (COALESCE(SUM(base_table.effective_cost_nano), 0) + COALESCE(SUM(base_table.effective_data_cost_nano), 0))::float/1000000000 e_yesterday_cost,
            (COALESCE(SUM(base_table.local_effective_cost_nano), 0) + COALESCE(SUM(base_table.local_effective_data_cost_nano), 0))::float/1000000000 local_e_yesterday_cost
        FROM mv_account_geo base_table
        WHERE (( base_table.date = %s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY yesterday_cost DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, dma ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 10, 2), 1, 2])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 10, 3))
    def test_query_all_yesterday_publishers(self, _):
        sql, params, _ = queries.prepare_query_all_yesterday(
            ['publisher_id', 'day'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}],
            'mv_account_pubs'
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.date AS day,
            (COALESCE(SUM(base_table.cost_nano), 0) + COALESCE(SUM(base_table.data_cost_nano), 0))::float/1000000000 yesterday_at_cost,
            (COALESCE(SUM(base_table.local_cost_nano), 0) + COALESCE(SUM(base_table.local_data_cost_nano), 0))::float/1000000000 local_yesterday_at_cost,
            (COALESCE(SUM(base_table.effective_cost_nano), 0) + COALESCE(SUM(base_table.effective_data_cost_nano), 0))::float/1000000000 yesterday_et_cost,
            (COALESCE(SUM(base_table.local_effective_cost_nano), 0) + COALESCE(SUM(base_table.local_effective_data_cost_nano), 0))::float/1000000000 local_yesterday_et_cost,
            (COALESCE(SUM(base_table.effective_cost_nano), 0) + COALESCE(SUM(base_table.effective_data_cost_nano), 0) + COALESCE(SUM(base_table.license_fee_nano), 0) + COALESCE(SUM(base_table.margin_nano), 0))::float/1000000000 yesterday_etfm_cost,
            (COALESCE(SUM(base_table.local_effective_cost_nano), 0) + COALESCE(SUM(base_table.local_effective_data_cost_nano), 0) + COALESCE(SUM(base_table.local_license_fee_nano), 0) + COALESCE(SUM(base_table.local_margin_nano), 0))::float/1000000000 local_yesterday_etfm_cost,
            (COALESCE(SUM(base_table.cost_nano), 0) + COALESCE(SUM(base_table.data_cost_nano), 0))::float/1000000000 yesterday_cost,
            (COALESCE(SUM(base_table.local_cost_nano), 0) + COALESCE(SUM(base_table.local_data_cost_nano), 0))::float/1000000000 local_yesterday_cost,
            (COALESCE(SUM(base_table.effective_cost_nano), 0) + COALESCE(SUM(base_table.effective_data_cost_nano), 0))::float/1000000000 e_yesterday_cost,
            (COALESCE(SUM(base_table.local_effective_cost_nano), 0) + COALESCE(SUM(base_table.local_effective_data_cost_nano), 0))::float/1000000000 local_e_yesterday_cost,
            MAX(base_table.publisher_source_id) publisher_id
        FROM mv_account_pubs base_table
        WHERE (( base_table.date = %s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY yesterday_cost DESC NULLS LAST, publisher_id ASC NULLS LAST, day ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 10, 2), 1, 2])

    def test_query_all_conversions(self):
        sql, params, _ = queries.prepare_query_all_conversions(
            ['account_id', 'source_id', 'slug'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}]
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.slug AS slug,
            SUM(base_table.conversion_count) count
        FROM mv_account_conv base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY count DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, slug ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_all_conversions_publishers(self):
        sql, params, _ = queries.prepare_query_all_conversions(
            ['publisher_id', 'day'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}]
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.date AS day,
            SUM(base_table.conversion_count) count,
            MAX(base_table.publisher_source_id) publisher_id
        FROM mv_conversions base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3
        ORDER BY count DESC NULLS LAST, publisher_id ASC NULLS LAST, day ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_all_touchpoints(self):
        sql, params, _ = queries.prepare_query_all_touchpoints(
            ['account_id', 'source_id', 'slug', 'window'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}]
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.slug AS slug,
            base_table.conversion_window AS "window",
            SUM(base_table.conversion_value_nano)/1000000000.0 conversion_value,
            SUM(base_table.conversion_count) count
        FROM mv_account_touch base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3, 4
        ORDER BY count DESC NULLS LAST, account_id ASC NULLS LAST, source_id ASC NULLS LAST, slug ASC NULLS LAST, "window" ASC NULLS LAST
        """)

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_all_touchpoints_publishers(self):
        sql, params, _ = queries.prepare_query_all_touchpoints(
            ['publisher_id', 'day', 'slug', 'window'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            [{'account_id': 1, 'source_id': 2}]
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.publisher AS publisher,
            base_table.source_id AS source_id,
            base_table.date AS day,
            base_table.slug AS slug,
            base_table.conversion_window AS "window",
            SUM(base_table.conversion_value_nano)/1000000000.0 conversion_value,
            SUM(base_table.conversion_count) count,
            MAX(base_table.publisher_source_id) publisher_id
        FROM mv_touchpointconversions base_table
        WHERE (( base_table.date >=%s AND base_table.date <=%s)
               AND (( base_table.account_id =%s AND base_table.source_id =%s)))
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY count DESC NULLS LAST, publisher_id ASC NULLS LAST, day ASC NULLS LAST, slug ASC NULLS LAST, "window" ASC NULLS LAST""")

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8), 1, 2])

    def test_query_structure_with_stats(self):
        sql, params, _ = queries.prepare_query_structure_with_stats(
            ['account_id', 'source_id', 'dma'],
            {
                'date__gte': datetime.date(2016, 1, 5),
                'date__lte': datetime.date(2016, 1, 8),
            },
            use_publishers_view=False
        )

        self.assertSQLEquals(sql, """
        SELECT
            base_table.account_id AS account_id,
            base_table.source_id AS source_id,
            base_table.dma AS dma
        FROM mv_account_geo base_table
        WHERE ( base_table.date >=%s AND base_table.date <=%s)
        GROUP BY 1, 2, 3;
        """)

        self.assertEqual(params, [datetime.date(2016, 1, 5), datetime.date(2016, 1, 8)])


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

        sql, params, _ = queries.prepare_query_joint_base(['account_id'], constraints, None,
                                                          ['total_seconds'], 5, 10, goals, False)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.account_id AS account_id,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 e_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_e_yesterday_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_at_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_yesterday_et_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0) + COALESCE(SUM(a.local_license_fee_nano), 0) + COALESCE(SUM(a.local_margin_nano), 0))::float/1000000000 local_yesterday_etfm_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_at_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 yesterday_et_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0) + COALESCE(SUM(a.license_fee_nano), 0) + COALESCE(SUM(a.margin_nano), 0))::float/1000000000 yesterday_etfm_cost
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
            temp_yesterday.local_e_yesterday_cost,
            temp_yesterday.local_yesterday_at_cost,
            temp_yesterday.local_yesterday_cost,
            temp_yesterday.local_yesterday_et_cost,
            temp_yesterday.local_yesterday_etfm_cost,
            temp_yesterday.yesterday_at_cost,
            temp_yesterday.yesterday_cost,
            temp_yesterday.yesterday_et_cost,
            temp_yesterday.yesterday_etfm_cost
        FROM temp_base LEFT OUTER JOIN temp_yesterday ON
            (temp_base.account_id = temp_yesterday.account_id OR temp_base.account_id IS NULL AND temp_yesterday.account_id IS NULL)
        ORDER BY total_seconds ASC NULLS LAST
        LIMIT 10
        OFFSET 5
        """)

        self.assertEqual(params, [
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMaster, 'get_aggregates',
                       return_value=[models.MVJointMaster.clicks, models.MVJointMaster.total_seconds])
    def test_query_joint_base_publishers(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        goals = Goals(None, None, None, None, None)

        sql, params, _ = queries.prepare_query_joint_base(['publisher_id'], constraints, None,
                                                          ['total_seconds'], 5, 10, goals, True)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 e_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_e_yesterday_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_at_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_yesterday_et_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0) + COALESCE(SUM(a.local_license_fee_nano), 0) + COALESCE(SUM(a.local_margin_nano), 0))::float/1000000000 local_yesterday_etfm_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_at_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 yesterday_et_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0) + COALESCE(SUM(a.license_fee_nano), 0) + COALESCE(SUM(a.margin_nano), 0))::float/1000000000 yesterday_etfm_cost
                FROM mv_account_pubs a
                WHERE (a.date=%s)
                GROUP BY 1, 2
            ),
            temp_base AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_account_pubs a
                WHERE (a.date>=%s AND a.date<=%s)
                GROUP BY 1, 2
            )
        SELECT
            temp_base.publisher,
            temp_base.source_id,
            temp_base.clicks,
            temp_base.total_seconds,
            temp_yesterday.e_yesterday_cost,
            temp_yesterday.local_e_yesterday_cost,
            temp_yesterday.local_yesterday_at_cost,
            temp_yesterday.local_yesterday_cost,
            temp_yesterday.local_yesterday_et_cost,
            temp_yesterday.local_yesterday_etfm_cost,
            temp_yesterday.yesterday_at_cost,
            temp_yesterday.yesterday_cost,
            temp_yesterday.yesterday_et_cost,
            temp_yesterday.yesterday_etfm_cost
        FROM temp_base LEFT OUTER JOIN temp_yesterday ON
            (temp_base.publisher = temp_yesterday.publisher OR temp_base.publisher IS NULL AND temp_yesterday.publisher IS NULL) AND
            (temp_base.source_id = temp_yesterday.source_id OR temp_base.source_id IS NULL AND temp_yesterday.source_id IS NULL)
        ORDER BY total_seconds ASC NULLS LAST
        LIMIT 10
        OFFSET 5
        """)

        self.assertEqual(params, [
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

        sql, params, _ = queries.prepare_query_joint_levels(
            ['account_id', 'campaign_id'], constraints, None, ['total_seconds', 'account_id', 'campaign_id'], 5, 10, goals, False)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 e_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_e_yesterday_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_at_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_yesterday_et_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0) + COALESCE(SUM(a.local_license_fee_nano), 0) + COALESCE(SUM(a.local_margin_nano), 0))::float/1000000000 local_yesterday_etfm_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_at_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 yesterday_et_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0) + COALESCE(SUM(a.license_fee_nano), 0) + COALESCE(SUM(a.margin_nano), 0))::float/1000000000 yesterday_etfm_cost
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
            b.local_e_yesterday_cost,
            b.local_yesterday_at_cost,
            b.local_yesterday_cost,
            b.local_yesterday_et_cost,
            b.local_yesterday_etfm_cost,
            b.yesterday_at_cost,
            b.yesterday_cost,
            b.yesterday_et_cost,
            b.yesterday_etfm_cost
        FROM
            (SELECT a.account_id,
                    a.campaign_id,
                    a.clicks,
                    a.total_seconds,
                    a.e_yesterday_cost,
                    a.local_e_yesterday_cost,
                    a.local_yesterday_at_cost,
                    a.local_yesterday_cost,
                    a.local_yesterday_et_cost,
                    a.local_yesterday_etfm_cost,
                    a.yesterday_at_cost,
                    a.yesterday_cost,
                    a.yesterday_et_cost,
                    a.yesterday_etfm_cost,
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
                        temp_yesterday.local_e_yesterday_cost,
                        temp_yesterday.local_yesterday_at_cost,
                        temp_yesterday.local_yesterday_cost,
                        temp_yesterday.local_yesterday_et_cost,
                        temp_yesterday.local_yesterday_etfm_cost,
                        temp_yesterday.yesterday_at_cost,
                        temp_yesterday.yesterday_cost,
                        temp_yesterday.yesterday_et_cost,
                        temp_yesterday.yesterday_etfm_cost
                FROM temp_base LEFT OUTER JOIN temp_yesterday ON
                    (temp_base.account_id = temp_yesterday.account_id OR temp_base.account_id IS NULL AND temp_yesterday.account_id IS NULL) AND
                    (temp_base.campaign_id = temp_yesterday.campaign_id OR temp_base.campaign_id IS NULL AND temp_yesterday.campaign_id IS NULL)
                ) a
            ) b
        WHERE r >= 5+1 AND r <= 10
        """)

        self.assertEqual(params, [
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    @mock.patch.object(models.MVJointMaster, 'get_aggregates',
                       return_value=[models.MVJointMaster.clicks, models.MVJointMaster.total_seconds])
    def test_query_joint_levels_publishers(self, _a, _b):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        goals = Goals(None, None, None, None, None)

        sql, params, _ = queries.prepare_query_joint_levels(
            ['publisher_id', 'dma'], constraints, None, ['total_seconds'], 5, 10, goals, True)

        self.assertSQLEquals(sql, """
        WITH
            temp_yesterday AS (
                SELECT
                    a.publisher AS publisher,
                    a.source_id AS source_id,
                    a.dma AS dma,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 e_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_e_yesterday_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_at_cost,
                    (COALESCE(SUM(a.local_cost_nano), 0) + COALESCE(SUM(a.local_data_cost_nano), 0))::float/1000000000 local_yesterday_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0))::float/1000000000 local_yesterday_et_cost,
                    (COALESCE(SUM(a.local_effective_cost_nano), 0) + COALESCE(SUM(a.local_effective_data_cost_nano), 0) + COALESCE(SUM(a.local_license_fee_nano), 0) + COALESCE(SUM(a.local_margin_nano), 0))::float/1000000000 local_yesterday_etfm_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_at_cost,
                    (COALESCE(SUM(a.cost_nano), 0) + COALESCE(SUM(a.data_cost_nano), 0))::float/1000000000 yesterday_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0))::float/1000000000 yesterday_et_cost,
                    (COALESCE(SUM(a.effective_cost_nano), 0) + COALESCE(SUM(a.effective_data_cost_nano), 0) + COALESCE(SUM(a.license_fee_nano), 0) + COALESCE(SUM(a.margin_nano), 0))::float/1000000000 yesterday_etfm_cost
                FROM mv_master_pubs a
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
                FROM mv_master_pubs a
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
            b.local_e_yesterday_cost,
            b.local_yesterday_at_cost,
            b.local_yesterday_cost,
            b.local_yesterday_et_cost,
            b.local_yesterday_etfm_cost,
            b.yesterday_at_cost,
            b.yesterday_cost,
            b.yesterday_et_cost,
            b.yesterday_etfm_cost
        FROM
            (SELECT a.publisher,
                    a.source_id,
                    a.dma,
                    a.clicks,
                    a.total_seconds,
                    a.e_yesterday_cost,
                    a.local_e_yesterday_cost,
                    a.local_yesterday_at_cost,
                    a.local_yesterday_cost,
                    a.local_yesterday_et_cost,
                    a.local_yesterday_etfm_cost,
                    a.yesterday_at_cost,
                    a.yesterday_cost,
                    a.yesterday_et_cost,
                    a.yesterday_etfm_cost,
                    ROW_NUMBER() OVER (PARTITION BY a.publisher, a.source_id
                                        ORDER BY a.total_seconds ASC NULLS LAST ) AS r
            FROM
                (SELECT temp_base.publisher,
                        temp_base.source_id,
                        temp_base.dma,
                        temp_base.clicks,
                        temp_base.total_seconds,
                        temp_yesterday.e_yesterday_cost,
                        temp_yesterday.local_e_yesterday_cost,
                        temp_yesterday.local_yesterday_at_cost,
                        temp_yesterday.local_yesterday_cost,
                        temp_yesterday.local_yesterday_et_cost,
                        temp_yesterday.local_yesterday_etfm_cost,
                        temp_yesterday.yesterday_at_cost,
                        temp_yesterday.yesterday_cost,
                        temp_yesterday.yesterday_et_cost,
                        temp_yesterday.yesterday_etfm_cost
                FROM temp_base LEFT OUTER JOIN temp_yesterday ON
                    (temp_base.publisher = temp_yesterday.publisher OR temp_base.publisher IS NULL AND temp_yesterday.publisher IS NULL) AND
                    (temp_base.source_id = temp_yesterday.source_id OR temp_base.source_id IS NULL AND temp_yesterday.source_id IS NULL) AND
                    (temp_base.dma = temp_yesterday.dma OR temp_base.dma IS NULL AND temp_yesterday.dma IS NULL)
                ) a
            ) b
        WHERE r >= 5+1 AND r <= 10
        """)

        self.assertEqual(params, [
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

        _, params, _ = queries.prepare_query_joint_base(['account_id'], constraints, None,
                                                        ['total_seconds'], 5, 10, goals, False)

        self.assertEqual(params, [
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

        _, params, _ = queries.prepare_query_joint_levels(['account_id', 'campaign_id'],
                                                          constraints, None, ['total_seconds'], 5, 10, goals, False)

        self.assertEqual(params, [
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            datetime.date(2016, 7, 1),
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
        ])
