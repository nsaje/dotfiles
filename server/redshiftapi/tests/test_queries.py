import backtosql
import copy
import datetime

from django.test import TestCase

from stats import constants
from utils import exc

import dash.models

from redshiftapi import queries
from redshiftapi import models
from redshiftapi import model_helpers


class SmallMaster(models.MVMaster):
    """
    A subset of MVMaster so that its easier to test
    """

    def __init__(self, *args, **kwargs):
        super(SmallMaster, self).__init__(*args, **kwargs)

        columns = self.select_columns([
            'date', 'week', 'source_id', 'account_id', 'campaign_id',
            'clicks', 'total_seconds',
        ])

        columns += self.select_columns(group=model_helpers.CONVERSION_AGGREGATES)
        columns += self.select_columns(group=model_helpers.TOUCHPOINTCONVERSION_AGGREGATES)
        columns += self.select_columns(group=model_helpers.AFTER_JOIN_CALCULATIONS)

        self.columns = columns
        self.columns_dict = {x.alias: x for x in self.columns}


class PrepareTimeConstraintsTest(TestCase):

    def test_dimension_day(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        # fits into time span
        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 0, 5)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lt': datetime.date(2016, 2, 6),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 10, 3)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 11),
            'date__lt': datetime.date(2016, 2, 14),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 10, 10)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 11),
            'date__lte': datetime.date(2016, 2, 16),  # should use the end date
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 20, 10)

        self.assertEquals(constraints, {
            # offset is above date range - constraints should not select any row
            'date__gte': datetime.date(2016, 2, 21),
            'date__lte': datetime.date(2016, 2, 16),
        })

    def test_dimension_week(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 0, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lt': datetime.date(2016, 2, 15),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 1, 1)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 8),
            'date__lt': datetime.date(2016, 2, 15),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 1, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 8),
            'date__lte': datetime.date(2016, 2, 16),  # should use end date
        })

    def test_dimension_month(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 5),
            'date__lte': datetime.date(2016, 4, 16),
        }

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.MONTH, constraints, 0, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 5),
            'date__lt': datetime.date(2016, 4, 1),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.MONTH, constraints, 2, 3)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 4, 16),
        })


class TestPrepareQuery(TestCase, backtosql.TestSQLMixin):

    def test_breakdown_struct_delivery_top_rows(self):
        m = SmallMaster()

        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        breakdown_constraints = [
            {'source_id': 132},
        ]

        context = m.get_default_context(['account_id'], constraints, breakdown_constraints, 'total_seconds', 0, 10)

        sql, params = queries.prepare_breakdown_struct_delivery_top_rows(context)

        # extracts params correctly
        self.assertItemsEqual(params, [
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
        ])

        self.assertSQLEquals(sql, """
        WITH temp_base AS (
                SELECT
                    a.account_id AS account_id,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_account a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id
            )
        SELECT
            b.account_id,
            b.clicks,
            b.total_seconds
        FROM (
            SELECT
                temp_base.account_id,
                temp_base.clicks,
                temp_base.total_seconds,
                ROW_NUMBER() OVER (PARTITION BY ORDER BY temp_base.total_seconds ASC) AS r
            FROM temp_base
        ) b
        WHERE r <= 10
        """)

    def test_breakdown_struct_delivery_required_breakdown_constraints(self):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        context = {
            'constraints': backtosql.Q(models.MVMaster(), **constraints)
        }

        with self.assertRaises(exc.MissingBreakdownConstraintsError):
            queries.prepare_breakdown_struct_delivery_top_rows(context)

    def test_top_time_rows_prepares_time(self):
        m = SmallMaster()
        constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        breakdown_constraints = [
            {'source_id': 132},
        ]

        context = m.get_default_context(
            ['account_id', 'week'],
            constraints,
            breakdown_constraints,
            '-clicks',
            1,
            2
        )

        sql, params = queries.prepare_time_top_rows(
            models.MVMaster(),
            constants.TimeDimension.DAY, context, constraints)

        self.assertItemsEqual(params, [
            datetime.date(2016, 2, 2), datetime.date(2016, 2, 4), 132])

        self.assertSQLEquals(sql, """
        WITH temp_base AS (
            SELECT
                a.account_id AS account_id,
                TRUNC(DATE_TRUNC('week', a.date)) AS week,
                SUM(a.clicks) clicks,
                SUM(a.total_time_on_site) total_seconds
            FROM mv_account a
            WHERE (a.date>=%s AND a.date<%s)
                  AND ((a.source_id=%s))
            GROUP BY account_id, week
        )
        SELECT
            temp_base.account_id,
            temp_base.week,
            temp_base.clicks,
            temp_base.total_seconds
        FROM temp_base
        ORDER BY day ASC;
        """)


class PrepareQueryWConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_views.yaml']

    breakdown_time_sql = """
        WITH temp_conversions AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    TRUNC(DATE_TRUNC('week', a.date)) AS week,
                    SUM(CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2,
                    SUM(CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3,
                    SUM(CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4,
                    SUM(CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5
                FROM mv_conversions_campaign a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id, campaign_id, week
            ),
            temp_touchpointconversions AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    TRUNC(DATE_TRUNC('week', a.date)) AS week,
                    SUM(CASE WHEN a.slug='test' AND a.conversion_window<=168 THEN conversion_count ELSE 0 END)
                        conversion_goal_1
                FROM mv_touch_campaign a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id, campaign_id, week
            ),
            temp_base AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    TRUNC(DATE_TRUNC('week', a.date)) AS week,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_campaign a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id, campaign_id, week
            )
        SELECT b.account_id,
            b.campaign_id,
            b.week,
            b.clicks,
            b.total_seconds,
            b.conversion_goal_2,
            b.conversion_goal_3,
            b.conversion_goal_4,
            b.conversion_goal_5,
            b.conversion_goal_1,
            b.avg_cost_per_conversion_goal_1,
            b.avg_cost_per_conversion_goal_2,
            b.avg_cost_per_conversion_goal_3,
            b.avg_cost_per_conversion_goal_4,
            b.avg_cost_per_conversion_goal_5
        FROM
        (SELECT temp_base.account_id,
                temp_base.campaign_id,
                temp_base.week,
                temp_base.clicks,
                temp_base.total_seconds,
                temp_conversions.conversion_goal_2,
                temp_conversions.conversion_goal_3,
                temp_conversions.conversion_goal_4,
                temp_conversions.conversion_goal_5,
                temp_touchpointconversions.conversion_goal_1,
                cost / NULLIF(conversion_goal_1, 0) avg_cost_per_conversion_goal_1,
                cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2,
                cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3,
                cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4,
                cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5,
                ROW_NUMBER() OVER (PARTITION BY temp_base.account_id, temp_base.campaign_id
                                    ORDER BY temp_base.clicks DESC) AS r
        FROM temp_base NATURAL
        LEFT OUTER JOIN temp_conversions NATURAL
        LEFT OUTER JOIN temp_touchpointconversions) b
        WHERE r <= 10
    """

    breakdown_struct_sql = """
        WITH temp_conversions AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    SUM(CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2,
                    SUM(CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3,
                    SUM(CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4,
                    SUM(CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5
                FROM mv_conversions_campaign a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id, campaign_id
            ),

            temp_touchpointconversions AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    SUM(CASE WHEN a.slug='test' AND a.conversion_window<=168 THEN conversion_count ELSE 0 END)
                        conversion_goal_1
                FROM mv_touch_campaign a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id, campaign_id
            ),

            temp_base AS (
                SELECT
                    a.account_id AS account_id,
                    a.campaign_id AS campaign_id,
                    SUM(a.clicks) clicks,
                    SUM(a.total_time_on_site) total_seconds
                FROM mv_campaign a
                WHERE (a.date>=%s AND a.date<=%s) AND ((a.source_id=%s))
                GROUP BY account_id, campaign_id
            )
        SELECT
            b.account_id,
            b.campaign_id,
            b.clicks,
            b.total_seconds,
            b.conversion_goal_2,
            b.conversion_goal_3,
            b.conversion_goal_4,
            b.conversion_goal_5,
            b.conversion_goal_1,
            b.avg_cost_per_conversion_goal_1,
            b.avg_cost_per_conversion_goal_2,
            b.avg_cost_per_conversion_goal_3,
            b.avg_cost_per_conversion_goal_4,
            b.avg_cost_per_conversion_goal_5
        FROM (
            SELECT
                temp_base.account_id,
                temp_base.campaign_id,
                temp_base.clicks,
                temp_base.total_seconds,
                temp_conversions.conversion_goal_2,
                temp_conversions.conversion_goal_3,
                temp_conversions.conversion_goal_4,
                temp_conversions.conversion_goal_5,
                temp_touchpointconversions.conversion_goal_1,
                cost / NULLIF(conversion_goal_1, 0) avg_cost_per_conversion_goal_1,
                cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2,
                cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3,
                cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4,
                cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5,
                ROW_NUMBER() OVER (PARTITION BY temp_base.account_id ORDER BY temp_base.clicks DESC) AS r
        FROM temp_base NATURAL
        LEFT OUTER JOIN temp_conversions NATURAL
        LEFT OUTER JOIN temp_touchpointconversions) b
        WHERE r <= 10
    """

    def test_breakdown_time_top_rows(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)

        m = SmallMaster(conversion_goals)

        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        breakdown_constraints = [
            {'source_id': 132},
        ]

        context = m.get_default_context(
            ['account_id', 'campaign_id', 'week'],
            constraints,
            breakdown_constraints,
            '-clicks',
            0,
            10
        )

        self.assertDictContainsSubset({
            'is_ordered_by_conversions':  False,
            'is_ordered_by_touchpointconversions': False,
            'is_ordered_by_after_join_conversions_calculations': False,
        }, context)

        sql, params = queries.prepare_breakdown_struct_delivery_top_rows(context)

        # extracts params correctly
        self.assertItemsEqual(params, [
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
        ])

        self.assertSQLEquals(sql, self.breakdown_time_sql)

    def test_breakdown_struct_delivery_top_rows_w_conversions(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)

        m = SmallMaster(conversion_goals)

        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        breakdown_constraints = [
            {'source_id': 132},
        ]

        context = m.get_default_context(
            ['account_id', 'campaign_id'],
            constraints,
            breakdown_constraints,
            '-clicks',
            0,
            10
        )

        sql, params = queries.prepare_breakdown_struct_delivery_top_rows(context)

        # extracts params correctly
        self.assertItemsEqual(params, [
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
            datetime.date(2016, 4, 1),
            datetime.date(2016, 5, 1),
            132,
        ])

        self.assertSQLEquals(sql, self.breakdown_struct_sql)

    def test_breakdown_struct_delivery_top_rows_order(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)
        m = SmallMaster(conversion_goals)

        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        breakdown_constraints = [
            {'source_id': 132},
        ]

        orders = {
            '-avg_cost_per_conversion_goal_1': 'ORDER BY cost / NULLIF(conversion_goal_1, 0) DESC',
            'conversion_goal_1': 'ORDER BY temp_touchpointconversions.conversion_goal_1 ASC',
            'conversion_goal_2': 'ORDER BY temp_conversions.conversion_goal_2 ASC',
            'clicks': 'ORDER BY temp_base.clicks ASC',
        }

        for order, order_sql in orders.items():

            context = m.get_default_context(
                ['account_id', 'campaign_id'],
                constraints,
                breakdown_constraints,
                order,
                0,
                10
            )

            sql, _ = queries.prepare_breakdown_struct_delivery_top_rows(context)

            self.assertTrue(order_sql in sql, "Order {}:\n{}\nNOT IN\n{}".format(order, order_sql, sql))

    def test_breakdown_time_top_rows_order(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)
        m = SmallMaster(conversion_goals)

        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        breakdown_constraints = [
            {'source_id': 132},
        ]

        orders = [
            '-avg_cost_per_conversion_goal_1',
            'conversion_goal_1',
            'conversion_goal_2',
            'clicks',
        ]

        order_sql = 'ORDER BY week ASC'

        for order in orders:
            context = m.get_default_context(
                ['account_id', 'campaign_id', 'week'],
                constraints,
                breakdown_constraints,
                order,
                0,
                10
            )

            sql, _ = queries.prepare_time_top_rows(m, 'week', context, constraints)

            # should always order by time
            self.assertTrue(order_sql in sql, "Order {}:\n{}\nNOT IN\n{}".format(order, order_sql, sql))
