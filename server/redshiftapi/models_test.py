import backtosql
import datetime
import mock

from django.test import TestCase

import dash.models
from stats.helpers import Goals

from redshiftapi import models


ALL_AGGREGATES = [
    'clicks', 'impressions',
    'license_fee', 'margin',
    'media_cost', 'e_media_cost', 'data_cost', 'e_data_cost',
    'at_cost', 'et_cost', 'etf_cost', 'etfm_cost',
    'total_cost', 'billing_cost', 'agency_cost',  # legacy
    'ctr',
    'cpc', 'et_cpc', 'etfm_cpc',
    'cpm', 'et_cpm', 'etfm_cpm',
    'visits', 'pageviews', 'click_discrepancy',
    'new_visits', 'percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos', 'returning_users', 'unique_users',
    'new_users', 'bounced_visits', 'total_seconds', 'non_bounced_visits', 'total_pageviews',
    'avg_cost_per_minute', 'avg_et_cost_per_minute', 'avg_etfm_cost_per_minute',
    'avg_cost_per_non_bounced_visit', 'avg_et_cost_per_non_bounced_visit', 'avg_etfm_cost_per_non_bounced_visit',
    'avg_cost_per_pageview', 'avg_et_cost_per_pageview', 'avg_etfm_cost_per_pageview',
    'avg_cost_for_new_visitor', 'avg_et_cost_for_new_visitor', 'avg_etfm_cost_for_new_visitor',
    'avg_cost_per_visit', 'avg_et_cost_per_visit', 'avg_etfm_cost_per_visit',
    'video_start', 'video_first_quartile', 'video_midpoint', 'video_third_quartile', 'video_complete', 'video_progress_3s',
    'video_cpv', 'video_et_cpv', 'video_etfm_cpv',
    'video_cpcv', 'video_et_cpcv', 'video_etfm_cpcv',
]


class MVMasterTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVMaster()

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
                              ALL_AGGREGATES)

    def test_get_constraints(self):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': date_from,
            'date__lte': date_to,
        }

        parents = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        q = self.model.get_constraints(constraints, parents)

        self.assertSQLEquals(
            q.generate('A'),
            """
            (
                (A.account_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)
                AND
                (
                    (A.content_ad_id=%s AND A.source_id=%s) OR
                    (A.content_ad_id=%s AND A.source_id=ANY(%s)) OR
                    (A.content_ad_id=%s AND A.source_id=ANY(%s))
                )
            )
            """
        )

        self.assertEqual(q.get_params(), [123, 223, date_from, date_to, 32, 1, 33, [2, 3], 35, [2, 4, 22]])

    def test_get_query_all_context(self):
        context = self.model.get_query_all_context(['account_id'], {'account_id': [1, 2, 3]}, None,
                                                   ['clicks'] + ['account_id'], False)
        self.assertEqual(context['breakdown'], self.model.select_columns(['account_id']))
        self.assertSQLEquals(context['constraints'].generate('A'), '(A.account_id=ANY(%s))')
        self.assertEqual(context['aggregates'], self.model.get_aggregates())
        self.assertEqual(context['view'], 'mv_account')
        self.assertEqual([x.alias for x in context['orders']], ['clicks', 'account_id'])

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 10, 3))
    def test_get_query_all_yesterday_context(self, mock_yesterday):
        context = self.model.get_query_all_yesterday_context(
            ['account_id'], {
                'account_id': [1, 2, 3],
                'date__lte': datetime.date(2016, 10, 1),
                'date__gte': datetime.date(2016, 9, 1)
            }, None,
            ['-yesterday_cost'], False)
        self.assertEqual(context['breakdown'], self.model.select_columns(['account_id']))
        self.assertSQLEquals(context['constraints'].generate('A'), '(A.account_id=ANY(%s) AND A.date=%s)')
        self.assertEqual(context['constraints'].get_params(), [[1, 2, 3], datetime.date(2016, 10, 2)])

        self.assertItemsEqual(context['aggregates'], self.model.select_columns([
            'yesterday_cost', 'e_yesterday_cost', 'yesterday_et_cost', 'yesterday_at_cost', 'yesterday_etfm_cost']))
        self.assertEqual(context['view'], 'mv_account')
        self.assertSQLEquals(context['orders'][0].only_alias(), 'yesterday_cost DESC NULLS LAST')

    def test_get_best_view(self):

        self.assertEqual(self.model.get_best_view(['account_id'], False), 'mv_account')


class MVMasterPublishersTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVMasterPublishers()

    def test_get_breakdown(self):
        self.assertEquals(
            self.model.get_breakdown(['publisher_id']),
            self.model.select_columns(['publisher', 'source_id'])
        )

        self.assertEquals(
            self.model.get_breakdown(['publisher_id', 'dma']),
            self.model.select_columns(['publisher', 'source_id', 'dma'])
        )

    def test_get_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ALL_AGGREGATES + ['external_id', 'publisher_id'])

    def test_get_constraints(self):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'ad_group_id': 111,
            'date__gte': date_from,
            'date__lte': date_to,
        }

        q = self.model.get_constraints(constraints, None)

        self.assertSQLEquals(
            q.generate('A'),
            "(A.account_id=%s AND A.ad_group_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)"
        )

        self.assertEqual(q.get_params(), [123, 111, 223, date_from, date_to])

    def test_get_constraints_publisher_parents(self):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'ad_group_id': 111,
            'date__gte': date_from,
            'date__lte': date_to,
        }

        parents = [{'publisher_id': 'asd__1'}, {'publisher_id': 'adsdd__2'}]
        q = self.model.get_constraints(constraints, parents)

        self.assertSQLEquals(
            q.generate('A'),
            """
            (
                (A.account_id=%s AND A.ad_group_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)
                AND
                (
                    (A.publisher=ANY(%s) AND A.source_id=%s) OR
                    (A.publisher=ANY(%s) AND A.source_id=%s)
                )
            )
            """
        )

        self.assertEqual(q.get_params(), [123, 111, 223, date_from, date_to, ['asd'], 1, ['adsdd'], 2])

    def test_get_best_view(self):
        self.assertEqual(self.model.get_best_view(['publisher_id'], True), 'mv_pubs_ad_group')


class MVTouchpointConversionsTest(TestCase, backtosql.TestSQLMixin):

    def setUp(self):
        self.model = models.MVTouchpointConversions()

    def test_get_breakdown(self):
        self.assertEquals(
            self.model.get_breakdown(['publisher_id', 'slug', 'window']),
            self.model.select_columns(['publisher', 'source_id', 'slug', 'window'])
        )

    def test_get_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ['count', 'conversion_value'])

    def test_get_best_view(self):
        self.assertEqual(self.model.get_best_view(['account_id'], False), 'mv_touch_account')


class MVConversionsTest(TestCase, backtosql.TestSQLMixin):

    def setUp(self):
        self.model = models.MVConversions()

    def test_get_breakdown(self):
        self.assertEquals(
            self.model.get_breakdown(['publisher_id', 'slug']),
            self.model.select_columns(['publisher', 'source_id', 'slug'])
        )

    def test_get_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ['count'])

    def test_get_best_view(self):
        self.assertEqual(self.model.get_best_view(['account_id'], False), 'mv_conversions_account')


class MVMasterConversionsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_views.yaml']

    def test_create_columns(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)

        m = models.MVJointMaster()
        m.init_conversion_columns(conversion_goals)
        m.init_pixel_columns(pixels)

        conversion_columns = m.select_columns(group=models.CONVERSION_AGGREGATES)
        touchpoint_columns = m.select_columns(group=models.TOUCHPOINTS_AGGREGATES)
        after_join_columns = m.select_columns(group=models.AFTER_JOIN_AGGREGATES)

        self.assertItemsEqual([x.column_as_alias('a') for x in conversion_columns], [
            backtosql.SQLMatcher(
                "SUM(CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2"),
            backtosql.SQLMatcher(
                "SUM(CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3"),
            backtosql.SQLMatcher(
                "SUM(CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4"),
            backtosql.SQLMatcher(
                "SUM(CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5"),
        ])

        self.assertListEqual([x.column_as_alias('a') for x in touchpoint_columns], [
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24
            THEN conversion_count ELSE 0 END) pixel_1_24"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24
            THEN conversion_value_nano ELSE 0 END)/1000000000.0 total_conversion_value_pixel_1_24"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168
            THEN conversion_count ELSE 0 END) pixel_1_168"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168
            THEN conversion_value_nano ELSE 0 END)/1000000000.0 total_conversion_value_pixel_1_168"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720
            THEN conversion_count ELSE 0 END) pixel_1_720"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720
            THEN conversion_value_nano ELSE 0 END)/1000000000.0 total_conversion_value_pixel_1_720"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=2160
            THEN conversion_count ELSE 0 END) pixel_1_2160"""),
            backtosql.SQLMatcher("""SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=2160
            THEN conversion_value_nano ELSE 0 END)/1000000000.0 total_conversion_value_pixel_1_2160"""),
        ])

        # prefixes should be added afterwards
        self.assertEqual([x.column_as_alias('a') for x in after_join_columns], [
            backtosql.SQLMatcher('e_media_cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2'),
            backtosql.SQLMatcher('et_cost / NULLIF(conversion_goal_2, 0) avg_et_cost_per_conversion_goal_2'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(conversion_goal_2, 0) avg_etfm_cost_per_conversion_goal_2'),

            backtosql.SQLMatcher('e_media_cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3'),
            backtosql.SQLMatcher('et_cost / NULLIF(conversion_goal_3, 0) avg_et_cost_per_conversion_goal_3'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(conversion_goal_3, 0) avg_etfm_cost_per_conversion_goal_3'),

            backtosql.SQLMatcher('e_media_cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4'),
            backtosql.SQLMatcher('et_cost / NULLIF(conversion_goal_4, 0) avg_et_cost_per_conversion_goal_4'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(conversion_goal_4, 0) avg_etfm_cost_per_conversion_goal_4'),

            backtosql.SQLMatcher('e_media_cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5'),
            backtosql.SQLMatcher('et_cost / NULLIF(conversion_goal_5, 0) avg_et_cost_per_conversion_goal_5'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(conversion_goal_5, 0) avg_etfm_cost_per_conversion_goal_5'),

            backtosql.SQLMatcher('e_media_cost / NULLIF(pixel_1_24, 0) avg_cost_per_pixel_1_24'),
            backtosql.SQLMatcher('et_cost / NULLIF(pixel_1_24, 0) avg_et_cost_per_pixel_1_24'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(pixel_1_24, 0) avg_etfm_cost_per_pixel_1_24'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_24, 0) - NVL(e_media_cost, 0) roas_pixel_1_24'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_24, 0) - NVL(et_cost, 0) et_roas_pixel_1_24'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_24, 0) - NVL(etfm_cost, 0) etfm_roas_pixel_1_24'),

            backtosql.SQLMatcher('e_media_cost / NULLIF(pixel_1_168, 0) avg_cost_per_pixel_1_168'),
            backtosql.SQLMatcher('et_cost / NULLIF(pixel_1_168, 0) avg_et_cost_per_pixel_1_168'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(pixel_1_168, 0) avg_etfm_cost_per_pixel_1_168'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_168, 0) - NVL(e_media_cost, 0) roas_pixel_1_168'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_168, 0) - NVL(et_cost, 0) et_roas_pixel_1_168'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_168, 0) - NVL(etfm_cost, 0) etfm_roas_pixel_1_168'),  # noqa

            backtosql.SQLMatcher('e_media_cost / NULLIF(pixel_1_720, 0) avg_cost_per_pixel_1_720'),
            backtosql.SQLMatcher('et_cost / NULLIF(pixel_1_720, 0) avg_et_cost_per_pixel_1_720'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(pixel_1_720, 0) avg_etfm_cost_per_pixel_1_720'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_720, 0) - NVL(e_media_cost, 0) roas_pixel_1_720'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_720, 0) - NVL(et_cost, 0) et_roas_pixel_1_720'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_720, 0) - NVL(etfm_cost, 0) etfm_roas_pixel_1_720'),  # noqa

            backtosql.SQLMatcher('e_media_cost / NULLIF(pixel_1_2160, 0) avg_cost_per_pixel_1_2160'),
            backtosql.SQLMatcher('et_cost / NULLIF(pixel_1_2160, 0) avg_et_cost_per_pixel_1_2160'),
            backtosql.SQLMatcher('etfm_cost / NULLIF(pixel_1_2160, 0) avg_etfm_cost_per_pixel_1_2160'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_2160, 0) - NVL(e_media_cost, 0) roas_pixel_1_2160'),  # noqa
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_2160, 0) - NVL(et_cost, 0) et_roas_pixel_1_2160'),
            backtosql.SQLMatcher('NVL(total_conversion_value_pixel_1_2160, 0) - NVL(etfm_cost, 0) etfm_roas_pixel_1_2160'),  # noqa
        ])

    def test_get_query_joint_context(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)
        goals = Goals(None, conversion_goals, None, pixels, None)

        m = models.MVJointMaster()

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': datetime.date(2016, 7, 1),
            'date__lte': datetime.date(2016, 7, 10),
        }

        parents = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        context = m.get_query_joint_context(
            ['account_id', 'source_id'],
            constraints,
            parents,
            ['pixel_1_24'],
            2,
            33,
            goals,
            False
        )

        self.assertListEqual(context['conversions_aggregates'], m.select_columns([
            'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5',
        ]))

        self.assertListEqual(context['touchpoints_aggregates'], m.select_columns([
            'pixel_1_24', 'total_conversion_value_pixel_1_24',
            'pixel_1_168', 'total_conversion_value_pixel_1_168',
            'pixel_1_720', 'total_conversion_value_pixel_1_720',
            'pixel_1_2160', 'total_conversion_value_pixel_1_2160',
        ]))

        self.assertListEqual(context['after_join_aggregates'], m.select_columns([
            'avg_cost_per_conversion_goal_2', 'avg_et_cost_per_conversion_goal_2', 'avg_etfm_cost_per_conversion_goal_2',  # noqa
            'avg_cost_per_conversion_goal_3', 'avg_et_cost_per_conversion_goal_3', 'avg_etfm_cost_per_conversion_goal_3',  # noqa
            'avg_cost_per_conversion_goal_4', 'avg_et_cost_per_conversion_goal_4', 'avg_etfm_cost_per_conversion_goal_4',  # noqa
            'avg_cost_per_conversion_goal_5', 'avg_et_cost_per_conversion_goal_5', 'avg_etfm_cost_per_conversion_goal_5',  # noqa
            'avg_cost_per_pixel_1_24', 'avg_et_cost_per_pixel_1_24', 'avg_etfm_cost_per_pixel_1_24',
            'roas_pixel_1_24', 'et_roas_pixel_1_24', 'etfm_roas_pixel_1_24',
            'avg_cost_per_pixel_1_168', 'avg_et_cost_per_pixel_1_168', 'avg_etfm_cost_per_pixel_1_168',
            'roas_pixel_1_168', 'et_roas_pixel_1_168', 'etfm_roas_pixel_1_168',
            'avg_cost_per_pixel_1_720', 'avg_et_cost_per_pixel_1_720', 'avg_etfm_cost_per_pixel_1_720',
            'roas_pixel_1_720', 'et_roas_pixel_1_720', 'etfm_roas_pixel_1_720',
            'avg_cost_per_pixel_1_2160', 'avg_et_cost_per_pixel_1_2160', 'avg_etfm_cost_per_pixel_1_2160',
            'roas_pixel_1_2160', 'et_roas_pixel_1_2160', 'etfm_roas_pixel_1_2160',
        ]))

        self.assertEquals(context['orders'][0].alias, 'pixel_1_24')


class MVJointMasterAfterJoinAggregatesTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_augmenter.yaml']

    def test_after_join_columns(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        campaign_goals = dash.models.CampaignGoal.objects.filter(campaign_id=campaign.id)
        campaign_goal_values = dash.models.CampaignGoalValue.objects.filter(campaign_goal__in=campaign_goals)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)

        goals = Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, None)

        m = models.MVJointMaster()

        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': datetime.date(2016, 7, 1),
            'date__lte': datetime.date(2016, 7, 10),
        }

        parents = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        order_field = 'performance_' + campaign_goals.get(pk=1).get_view_key()

        context = m.get_query_joint_context(
            ['account_id', 'source_id', 'dma'],
            constraints,
            parents,
            ['-' + order_field],
            2,
            33,
            goals,
            False
        )

        self.assertListEqual(context['after_join_aggregates'], [m.get_column(order_field),
                                                                m.get_column('etfm_' + order_field)])

        self.assertEquals(context['orders'][0].alias, order_field)


class MVJointMasterPublishersTest(TestCase, backtosql.TestSQLMixin):

    def setUp(self):
        self.model = models.MVJointMasterPublishers()

    def test_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ALL_AGGREGATES + ['external_id', 'publisher_id'])


class MVJointMasterTest(TestCase, backtosql.TestSQLMixin):

    def setUp(self):
        self.model = models.MVJointMaster()

    def test_get_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ALL_AGGREGATES)

    @mock.patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 7, 2))
    def test_get_query_joint_context(self, mock_today):
        m = models.MVJointMaster()

        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            'account_id': 123,
            'campaign_id': 223,
            'date__gte': date_from,
            'date__lte': date_to,
        }

        parents = [
            {'content_ad_id': 32, 'source_id': 1},
            {'content_ad_id': 33, 'source_id': [2, 3]},
            {'content_ad_id': 35, 'source_id': [2, 4, 22]},
        ]

        context = m.get_query_joint_context(
            ['account_id', 'source_id'],
            constraints,
            parents,
            ['-clicks'],
            2,
            33,
            Goals(None, None, None, None, None),
            False
        )

        q = context['constraints']
        self.assertSQLEquals(
            q.generate('A'),
            """
            (
                (A.account_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)
                AND
                (
                    (A.content_ad_id=%s AND A.source_id=%s) OR
                    (A.content_ad_id=%s AND A.source_id=ANY(%s)) OR
                    (A.content_ad_id=%s AND A.source_id=ANY(%s))
                )
            )
            """)
        self.assertEqual(q.get_params(), [123, 223, date_from, date_to, 32, 1, 33, [2, 3], 35, [2, 4, 22]])

        q = context['yesterday_constraints']
        self.assertSQLEquals(
            q.generate('A'),
            """
            (
                (A.account_id=%s AND A.campaign_id=%s AND A.date=%s)
                AND
                (
                    (A.content_ad_id=%s AND A.source_id=%s) OR
                    (A.content_ad_id=%s AND A.source_id=ANY(%s)) OR
                    (A.content_ad_id=%s AND A.source_id=ANY(%s))
                )
            )
            """)
        self.assertEqual(q.get_params(), [123, 223, datetime.date(2016, 7, 1), 32, 1, 33, [2, 3], 35, [2, 4, 22]])

        self.assertEqual(context['offset'], 2)
        self.assertEqual(context['limit'], 33)
        self.assertEqual(context['orders'][0].alias, 'clicks')

        self.assertListEqual(context['partition'], m.select_columns(['account_id']))
