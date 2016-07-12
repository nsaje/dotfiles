import backtosql
from django.test import TestCase

import dash.models

from redshiftapi import models
from redshiftapi import model_helpers
from stats import constants


class MVMasterConversionsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_views.yaml']

    def test_create_columns(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)

        m = models.MVMaster(conversion_goals)

        conversion_columns = m.select_columns(group=model_helpers.CONVERSION_AGGREGATES)
        touchpoint_columns = m.select_columns(group=model_helpers.TOUCHPOINTCONVERSION_AGGREGATES)

        self.assertListEqual([x.column_as_alias('a') for x in conversion_columns], [
            "SUM(CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2",
            "SUM(CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3",
            "SUM(CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4",
            "SUM(CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5",
        ])

        self.assertListEqual([x.column_as_alias('a') for x in touchpoint_columns], [
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.conversion_window<=168
            THEN conversion_count ELSE 0 END) conversion_goal_1""")
        ])

        columns = m.get_columns()
        self.assertEquals(len(columns), 43)

        columns = m.select_columns(group=model_helpers.BREAKDOWN)
        self.assertEquals(len(columns), 18)

    def test_get_default_context(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)
        m = models.MVMaster(conversion_goals)

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
        }

        breakdown_constraints = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        context = m.get_default_context(
            ['account_id', 'source_id'],
            constraints,
            breakdown_constraints,
            '-conversion_goal_1',
            2,
            33
        )

        self.assertFalse(context['is_ordered_by_conversions'])
        self.assertTrue(context['is_ordered_by_touchpointconversions'])

        self.assertListEqual(context['conversions_aggregates'], m.select_columns([
            'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5',
        ]))

        self.assertListEqual(context['touchpointconversions_aggregates'], m.select_columns([
            'conversion_goal_1',
        ]))


class RSModelTest(TestCase, backtosql.TestSQLMixin):

    def setUp(self):
        self.model = models.MVMaster()

    def test_columns(self):
        columns = self.model.get_columns()
        self.assertEquals(len(columns), 38)

        columns = self.model.select_columns(group=model_helpers.BREAKDOWN)
        self.assertEquals(len(columns), 18)

    def test_get_breakdown(self):
        self.assertEquals(
            self.model.get_breakdown(['account_id', 'campaign_id']),
            [self.model.get_column('account_id'), self.model.get_column('campaign_id')]
        )

        # query for unknown column
        with self.assertRaises(backtosql.BackToSQLException):
            self.model.get_breakdown(['bla', 'campaign_id'])

    def test_get_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ['clicks', 'impressions', 'cost', 'data_cost',
                               'media_cost', 'e_media_cost', 'e_data_cost',
                               'license_fee', 'billing_cost', 'total_cost',
                               'ctr', 'cpc', 'visits', 'click_discrepancy',
                               'pageviews', 'new_visits', 'percent_new_users',
                               'bounce_rate', 'pv_per_visit', 'avg_tos'])

    def test_get_default_context_constraints(self):
        m = models.MVMaster()

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
        }

        breakdown_constraints = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        context = m.get_default_context(
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
        self.assertSQLEquals(
            q.generate('A'),
            """\
            ((A.content_ad_id=%s AND A.source_id=%s) OR \
            (A.content_ad_id=%s AND A.source_id=ANY(%s)) OR \
            (A.content_ad_id=%s AND A.source_id=ANY(%s)))""")
        self.assertEqual(q.get_params(), [32, 1, 33, [2, 3], 35, [2, 4, 22]])

        self.assertEqual(context['offset'], 2)
        self.assertEqual(context['limit'], 33)

        self.assertListEqual(context['breakdown_partition'], m.select_columns(['account_id']))

    def test_get_best_view(self):
        m = models.MVMaster()

        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.ACCOUNT),
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_account',
            'conversions': 'mv_conversions_account',
            'touchpointconversions': 'mv_touch_account',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_account',
            'conversions': 'mv_conversions_account',
            'touchpointconversions': 'mv_touch_account',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.ACCOUNT),
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_account',
            'conversions': 'mv_conversions_account',
            'touchpointconversions': 'mv_touch_account',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.ACCOUNT),
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_account_delivery',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.ACCOUNT),
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_account_delivery',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.ACCOUNT),
            constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN),
        ], {}), {
            'base': 'mv_campaign',
            'conversions': 'mv_conversions_campaign',
            'touchpointconversions': 'mv_touch_campaign',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN),
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
        ], {}), {
            'base': 'mv_campaign',
            'conversions': 'mv_conversions_campaign',
            'touchpointconversions': 'mv_touch_campaign',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN),
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_campaign_delivery',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_ad_group_delivery',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.CONTENT_AD),
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_content_ad_delivery',
        })

        # Campaign level - media sources tab
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_campaign',
            'conversions': 'mv_conversions_campaign',
            'touchpointconversions': 'mv_touch_campaign',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.get_dimension_identifier(constants.StructureDimension.CONTENT_AD),
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_content_ad',
            'conversions': 'mv_conversions_content_ad',
            'touchpointconversions': 'mv_touch_content_ad',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_ad_group_delivery',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.get_dimension_identifier(constants.StructureDimension.CONTENT_AD),
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_content_ad_delivery',
        })

        # Campaign level - Ad groups tab
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.get_dimension_identifier(constants.StructureDimension.CONTENT_AD),
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_content_ad',
            'conversions': 'mv_conversions_content_ad',
            'touchpointconversions': 'mv_touch_content_ad',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.get_dimension_identifier(constants.StructureDimension.SOURCE),
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_ad_group_delivery',
        })
        self.assertEqual(m.get_best_view([
            constants.get_dimension_identifier(constants.StructureDimension.AD_GROUP),
            constants.get_dimension_identifier(constants.StructureDimension.CONTENT_AD),
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.get_dimension_identifier(constants.StructureDimension.CAMPAIGN): 1}), {
            'base': 'mv_content_ad_delivery',
        })
