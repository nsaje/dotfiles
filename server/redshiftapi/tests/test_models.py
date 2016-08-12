import backtosql
import datetime
import mock
from django.test import TestCase

import dash.models
from utils import test_helper

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
        after_join_columns = m.select_columns(group=model_helpers.AFTER_JOIN_CALCULATIONS)

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

        # prefixes should be added afterwards
        self.assertListEqual([x.column_as_alias('a') for x in after_join_columns], [
            'media_cost / NULLIF(conversion_goal_1, 0) avg_cost_per_conversion_goal_1',
            'media_cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2',
            'media_cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3',
            'media_cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4',
            'media_cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5',
        ])

        columns = m.get_columns()
        self.assertEquals(len(columns), 64)

        columns = m.select_columns(group=model_helpers.BREAKDOWN)
        self.assertEquals(len(columns), 18)

    def test_get_default_context(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)
        m = models.MVMaster(conversion_goals)

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': datetime.date(2016, 7, 1),
            'date__lte': datetime.date(2016, 7, 10),
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
        self.assertFalse(context['is_ordered_by_after_join_conversions_calculations'])

        self.assertListEqual(context['conversions_aggregates'], m.select_columns([
            'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5',
        ]))

        self.assertListEqual(context['touchpointconversions_aggregates'], m.select_columns([
            'conversion_goal_1',
        ]))

        self.assertListEqual(context['after_join_conversions_calculations'], m.select_columns([
            'avg_cost_per_conversion_goal_1',
            'avg_cost_per_conversion_goal_2',
            'avg_cost_per_conversion_goal_3',
            'avg_cost_per_conversion_goal_4',
            'avg_cost_per_conversion_goal_5',
        ]))

        self.assertEquals(context['order'].alias, 'conversion_goal_1')

    def test_get_default_context_conversions_not_supported(self):
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=1)
        m = models.MVMaster(conversion_goals)

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': datetime.date(2016, 7, 1),
            'date__lte': datetime.date(2016, 7, 10),
        }

        breakdown_constraints = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        context = m.get_default_context(
            ['account_id', 'source_id', 'dma'],
            constraints,
            breakdown_constraints,
            '-conversion_goal_1',
            2,
            33
        )

        self.assertFalse(context['is_ordered_by_conversions'])
        self.assertFalse(context['is_ordered_by_touchpointconversions'])
        self.assertFalse(context['is_ordered_by_after_join_conversions_calculations'])

        self.assertListEqual(context['conversions_aggregates'], [])
        self.assertListEqual(context['touchpointconversions_aggregates'], [])
        self.assertListEqual(context['after_join_conversions_calculations'], [])

        # the order specified is not supported for this breakdown so select the default
        self.assertEquals(context['order'].alias, 'clicks')


class MVMasterTest(TestCase, backtosql.TestSQLMixin):

    def setUp(self):
        self.model = models.MVMaster()

    def test_columns(self):
        columns = self.model.get_columns()
        self.assertEquals(len(columns), 54)

        columns = self.model.select_columns(group=model_helpers.BREAKDOWN)
        self.assertEquals(len(columns), 18)

    def test_no_conversion_columns(self):
        conversion_columns = self.model.select_columns(group=model_helpers.CONVERSION_AGGREGATES)
        touchpoint_columns = self.model.select_columns(group=model_helpers.TOUCHPOINTCONVERSION_AGGREGATES)
        after_join_columns = self.model.select_columns(group=model_helpers.AFTER_JOIN_CALCULATIONS)

        self.assertItemsEqual(conversion_columns, [])
        self.assertItemsEqual(touchpoint_columns, [])
        self.assertItemsEqual(after_join_columns, [])

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
                              ['clicks', 'impressions', 'data_cost',
                               'media_cost', 'e_media_cost', 'e_data_cost',
                               'license_fee', 'billing_cost', 'total_cost',
                               'ctr', 'cpc', 'visits', 'click_discrepancy',
                               'pageviews', 'new_visits', 'percent_new_users',
                               'new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos',
                               'avg_cost_for_new_visitor', 'avg_cost_per_minute',
                               'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview',
                               'avg_cost_per_visit', 'total_pageviews', 'total_seconds',
                               'non_bounced_visits', 'margin', 'agency_total',
                               'cpm', 'returning_users', 'unique_users', 'bounced_visits'])

    def test_get_yesterday_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.select_columns(group=model_helpers.YESTERDAY_COST_AGGREGATES)],
                              ['yesterday_cost', 'e_yesterday_cost'])

    def test_get_default_context_constraints(self):
        m = models.MVMaster()

        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': date_from,
            'date__lte': date_to,
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
            "(A.account_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)")
        self.assertEqual(q.get_params(), [123, 223, date_from, date_to])

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

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    def test_get_default_yesterday_context(self, mock_local_today):
        m = models.MVMaster()
        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': datetime.date(2016, 6, 1),
            'date__lte': datetime.date(2016, 6, 5),
        }

        context = models.get_default_yesterday_context(
            m,
            constraints,
            m.yesterday_cost.as_order('-yesterday_cost')
        )

        self.assertDictContainsSubset({
            'is_ordered_by_yesterday_aggregates': True,
            'yesterday_aggregates': m.select_columns(['e_yesterday_cost', 'yesterday_cost']),
        }, context)

        self.assertSQLEquals(
            context['yesterday_constraints'].generate('A'),
            '(A.account_id=%s AND A.campaign_id=%s AND A.date=%s)'
        )

    def test_get_best_view(self):
        m = models.MVMaster()

        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_account',
            'conversions': 'mv_conversions_account',
            'touchpointconversions': 'mv_touch_account',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_account',
            'conversions': 'mv_conversions_account',
            'touchpointconversions': 'mv_touch_account',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.StructureDimension.SOURCE,
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_account',
            'conversions': 'mv_conversions_account',
            'touchpointconversions': 'mv_touch_account',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.StructureDimension.SOURCE,
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_account_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.StructureDimension.SOURCE,
            constants.DeliveryDimension.DMA,
        ], {}), {
            'base': 'mv_account_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_account_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.DeliveryDimension.DMA,
        ], {}), {
            'base': 'mv_account_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.ACCOUNT,
            constants.StructureDimension.CAMPAIGN,
        ], {}), {
            'base': 'mv_campaign',
            'conversions': 'mv_conversions_campaign',
            'touchpointconversions': 'mv_touch_campaign',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.CAMPAIGN,
            constants.StructureDimension.SOURCE,
        ], {}), {
            'base': 'mv_campaign',
            'conversions': 'mv_conversions_campaign',
            'touchpointconversions': 'mv_touch_campaign',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.CAMPAIGN,
            constants.StructureDimension.SOURCE,
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_campaign_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.CAMPAIGN,
            constants.StructureDimension.SOURCE,
            constants.DeliveryDimension.DMA,
        ], {}), {
            'base': 'mv_campaign_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.TimeDimension.MONTH,
        ], {}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_ad_group_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.DeliveryDimension.DMA,
        ], {}), {
            'base': 'mv_ad_group_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.CONTENT_AD,
            constants.DeliveryDimension.AGE,
        ], {}), {
            'base': 'mv_content_ad_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.CONTENT_AD,
            constants.DeliveryDimension.DMA,
        ], {}), {
            'base': 'mv_content_ad_delivery_geo',
        })

        # Campaign level - media sources tab
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_campaign',
            'conversions': 'mv_conversions_campaign',
            'touchpointconversions': 'mv_touch_campaign',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.StructureDimension.AD_GROUP,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.StructureDimension.CONTENT_AD,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_content_ad',
            'conversions': 'mv_conversions_content_ad',
            'touchpointconversions': 'mv_touch_content_ad',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.StructureDimension.AD_GROUP,
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.StructureDimension.AD_GROUP,
            constants.DeliveryDimension.DMA,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.StructureDimension.CONTENT_AD,
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_content_ad_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.SOURCE,
            constants.StructureDimension.CONTENT_AD,
            constants.DeliveryDimension.DMA,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_content_ad_delivery_geo',
        })

        # Campaign level - Ad groups tab
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.SOURCE,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group',
            'conversions': 'mv_conversions_ad_group',
            'touchpointconversions': 'mv_touch_ad_group',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.CONTENT_AD,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_content_ad',
            'conversions': 'mv_conversions_content_ad',
            'touchpointconversions': 'mv_touch_content_ad',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.SOURCE,
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.SOURCE,
            constants.DeliveryDimension.DMA,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_ad_group_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.CONTENT_AD,
            constants.DeliveryDimension.AGE,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_content_ad_delivery_demo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.CONTENT_AD,
            constants.DeliveryDimension.DMA,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_content_ad_delivery_geo',
        })
        self.assertEqual(m.get_best_view([
            constants.StructureDimension.AD_GROUP,
            constants.StructureDimension.PUBLISHER,
            constants.TimeDimension.DAY,
        ], {constants.StructureDimension.CAMPAIGN: 1}), {
            'base': 'mv_pubs_master',
            'conversions': 'mv_conversions',
            'touchpointconversions': 'mv_touchpointconversions',
        })
