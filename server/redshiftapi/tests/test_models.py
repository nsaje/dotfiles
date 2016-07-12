import backtosql
from django.test import TestCase

from redshiftapi import models
from redshiftapi import model_helpers
from stats import constants


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

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
        }

        breakdown_constraints = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        context = models.MVMaster().get_default_context(
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
