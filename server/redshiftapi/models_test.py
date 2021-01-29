import datetime

import mock
from django.test import TestCase

import backtosql
import dash.models
from redshiftapi import models
from stats.helpers import Goals

ALL_AGGREGATES = [
    "clicks",
    "impressions",
    "service_fee",
    "local_service_fee",
    "license_fee",
    "local_license_fee",
    "margin",
    "local_margin",
    "media_cost",
    "local_media_cost",
    "b_media_cost",
    "local_b_media_cost",
    "e_media_cost",
    "local_e_media_cost",
    "data_cost",
    "local_data_cost",
    "b_data_cost",
    "local_b_data_cost",
    "e_data_cost",
    "local_e_data_cost",
    "at_cost",
    "local_at_cost",
    "bt_cost",
    "local_bt_cost",
    "et_cost",
    "local_et_cost",
    "etf_cost",
    "local_etf_cost",
    "etfm_cost",
    "local_etfm_cost",
    "ctr",
    "etfm_cpc",
    "local_etfm_cpc",
    "etfm_cpm",
    "local_etfm_cpm",
    "visits",
    "pageviews",
    "click_discrepancy",
    "new_visits",
    "percent_new_users",
    "bounce_rate",
    "pv_per_visit",
    "avg_tos",
    "returning_users",
    "unique_users",
    "new_users",
    "bounced_visits",
    "total_seconds",
    "non_bounced_visits",
    "total_pageviews",
    "avg_etfm_cost_per_minute",
    "local_avg_etfm_cost_per_minute",
    "avg_etfm_cost_per_non_bounced_visit",
    "local_avg_etfm_cost_per_non_bounced_visit",
    "avg_etfm_cost_per_pageview",
    "local_avg_etfm_cost_per_pageview",
    "avg_etfm_cost_per_new_visitor",
    "local_avg_etfm_cost_per_new_visitor",
    "avg_etfm_cost_per_visit",
    "local_avg_etfm_cost_per_visit",
    "avg_etfm_cost_per_unique_user",
    "local_avg_etfm_cost_per_unique_user",
    "video_start",
    "video_first_quartile",
    "video_midpoint",
    "video_third_quartile",
    "video_complete",
    "video_progress_3s",
    "video_etfm_cpv",
    "local_video_etfm_cpv",
    "video_etfm_cpcv",
    "local_video_etfm_cpcv",
    "video_start_percent",
    "video_first_quartile_percent",
    "video_midpoint_percent",
    "video_third_quartile_percent",
    "video_complete_percent",
    "video_progress_3s_percent",
    "mrc50_measurable",
    "mrc50_viewable",
    "mrc50_non_measurable",
    "mrc50_non_viewable",
    "mrc50_measurable_percent",
    "mrc50_viewable_percent",
    "mrc50_viewable_distribution",
    "mrc50_non_measurable_distribution",
    "mrc50_non_viewable_distribution",
    "etfm_mrc50_vcpm",
    "local_etfm_mrc50_vcpm",
    "mrc100_measurable",
    "mrc100_viewable",
    "mrc100_non_measurable",
    "mrc100_non_viewable",
    "mrc100_measurable_percent",
    "mrc100_viewable_percent",
    "mrc100_viewable_distribution",
    "mrc100_non_measurable_distribution",
    "mrc100_non_viewable_distribution",
    "etfm_mrc100_vcpm",
    "local_etfm_mrc100_vcpm",
    "vast4_measurable",
    "vast4_viewable",
    "vast4_non_measurable",
    "vast4_non_viewable",
    "vast4_measurable_percent",
    "vast4_viewable_percent",
    "vast4_viewable_distribution",
    "vast4_non_measurable_distribution",
    "vast4_non_viewable_distribution",
    "etfm_vast4_vcpm",
    "local_etfm_vast4_vcpm",
]


class BreakdownBaseTest(TestCase):
    def test_get_breakdown(self):
        model = models.BreakdownsBase()
        self.assertEqual(model.get_breakdown(["publisher_id"]), model.select_columns(["publisher", "source_id"]))
        self.assertEqual(
            model.get_breakdown(["account_id", "publisher_id", "publisher"]),
            model.select_columns(["account_id", "publisher", "source_id"]),
        )


class MVMasterTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVMaster()

    def test_get_breakdown(self):
        self.assertEqual(
            self.model.get_breakdown(["account_id", "campaign_id"]),
            [self.model.get_column("account_id"), self.model.get_column("campaign_id")],
        )

        # query for unknown column
        with self.assertRaises(backtosql.BackToSQLException):
            self.model.get_breakdown(["bla", "campaign_id"])

    def test_get_aggregates(self):
        self.assertCountEqual([x.alias for x in self.model.get_aggregates([])], ALL_AGGREGATES)

    def test_get_constraints(self):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {"account_id": 123, "campaign_id": 223, "date__gte": date_from, "date__lte": date_to}

        parents = [
            {"content_ad_id": 32, "source_id": 1},
            {"content_ad_id": 33, "source_id": [2, 3]},
            {"content_ad_id": 35, "source_id": [2, 4, 22]},
        ]

        q = self.model.get_constraints(constraints, parents)

        self.assertSQLEquals(
            q.generate("A"),
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
            """,
        )

        self.assertEqual(q.get_params(), [123, 223, date_from, date_to, 32, 1, 33, [2, 3], 35, [2, 4, 22]])

    def test_get_query_all_context(self):
        breakdown = ["account_id"]
        view = "mv_account"

        context = self.model.get_query_all_context(
            breakdown, {"account_id": [1, 2, 3]}, None, ["clicks"] + ["account_id"], view
        )

        self.assertEqual(context["breakdown"], self.model.select_columns(["account_id"]))
        self.assertSQLEquals(
            context["constraints"].generate("A"),
            """(a.account_id IN
                   (SELECT account_id
                   FROM tmp_filter_account_id_0017c395f39ceeaee171dff6a1b5bb3d6388e221))
            """,
        )
        self.assertEqual(context["aggregates"], self.model.get_aggregates(breakdown))
        self.assertEqual(context["view"], "mv_account")
        self.assertEqual([x.alias for x in context["orders"]], ["clicks", "account_id"])

        self.assertEqual(len(context["temp_tables"]), 1)
        temp_table = list(context["temp_tables"])[0]
        self.assertEqual(temp_table.name, "tmp_filter_account_id_0017c395f39ceeaee171dff6a1b5bb3d6388e221")
        self.assertEqual(temp_table.values, [1, 2, 3])

    @mock.patch("utils.dates_helper.local_today", return_value=datetime.date(2016, 10, 3))
    def test_get_query_all_yesterday_context(self, mock_yesterday):
        context = self.model.get_query_all_yesterday_context(
            ["account_id"],
            {"account_id": [1, 2, 3], "date__lte": datetime.date(2016, 10, 1), "date__gte": datetime.date(2016, 9, 1)},
            None,
            ["-yesterday_at_cost"],
            "mv_account",
        )

        self.assertEqual(context["breakdown"], self.model.select_columns(["account_id"]))
        self.assertSQLEquals(
            context["constraints"].generate("A"),
            """(a.account_id IN
                   (SELECT account_id
                   FROM tmp_filter_account_id_0017c395f39ceeaee171dff6a1b5bb3d6388e221)
                AND a.date=%s)
            """,
        )
        self.assertEqual(context["constraints"].get_params(), [datetime.date(2016, 10, 2)])

        self.assertCountEqual(
            context["aggregates"],
            self.model.select_columns(
                ["yesterday_at_cost", "local_yesterday_at_cost", "yesterday_etfm_cost", "local_yesterday_etfm_cost"]
            ),
        )
        self.assertEqual(context["view"], "mv_account")
        self.assertSQLEquals(context["orders"][0].only_alias(), "yesterday_at_cost DESC NULLS LAST")

        self.assertEqual(len(context["temp_tables"]), 1)
        temp_table = list(context["temp_tables"])[0]
        self.assertEqual(temp_table.name, "tmp_filter_account_id_0017c395f39ceeaee171dff6a1b5bb3d6388e221")
        self.assertEqual(temp_table.values, [1, 2, 3])

    def test_get_query_counts_context(self):
        breakdown = ["account_id", "country"]
        view = "mv_account_geo"

        context = self.model.get_query_counts_context(breakdown, {"account_id": [1, 2, 3]}, [{"account_id": 1}], view)

        self.assertEqual(context["parent_breakdown"], self.model.select_columns(["account_id"]))
        self.assertEqual(context["breakdown"], self.model.select_columns(["account_id", "country"]))
        self.assertSQLEquals(
            context["constraints"].generate("A"),
            """((a.account_id IN (SELECT account_id FROM tmp_filter_account_id_0017c395f39ceeaee171dff6a1b5bb3d6388e221)) AND ((A.account_id=%s)))""",
        )
        self.assertEqual(context["view"], view)

        self.assertEqual(len(context["temp_tables"]), 1)
        temp_table = list(context["temp_tables"])[0]
        self.assertEqual(temp_table.name, "tmp_filter_account_id_0017c395f39ceeaee171dff6a1b5bb3d6388e221")
        self.assertEqual(temp_table.values, [1, 2, 3])


class MVMasterPublishersTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVMaster()

    def test_get_breakdown(self):
        self.assertEqual(
            self.model.get_breakdown(["publisher_id"]), self.model.select_columns(["publisher", "source_id"])
        )

        self.assertEqual(
            self.model.get_breakdown(["publisher_id", "dma"]),
            self.model.select_columns(["publisher", "source_id", "dma"]),
        )

    def test_get_aggregates(self):
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["placement_id"])], ALL_AGGREGATES + ["placement_type"]
        )

    def test_get_constraints(self):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            "account_id": 123,
            "campaign_id": 223,
            "ad_group_id": 111,
            "date__gte": date_from,
            "date__lte": date_to,
        }

        q = self.model.get_constraints(constraints, None)

        self.assertSQLEquals(
            q.generate("A"), "(A.account_id=%s AND A.ad_group_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)"
        )

        self.assertEqual(q.get_params(), [123, 111, 223, date_from, date_to])

    def test_get_constraints_publisher_parents(self):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {
            "account_id": 123,
            "campaign_id": 223,
            "ad_group_id": 111,
            "date__gte": date_from,
            "date__lte": date_to,
        }

        parents = [{"publisher_id": "asd__1"}, {"publisher_id": "adsdd__2"}]
        q = self.model.get_constraints(constraints, parents)

        self.assertSQLEquals(
            q.generate("A"),
            """
            (
                (A.account_id=%s AND A.ad_group_id=%s AND A.campaign_id=%s AND A.date>=%s AND A.date<=%s)
                AND
                (
                    (A.publisher=ANY(%s) AND A.source_id=%s) OR
                    (A.publisher=ANY(%s) AND A.source_id=%s)
                )
            )
            """,
        )

        self.assertEqual(q.get_params(), [123, 111, 223, date_from, date_to, ["asd"], 1, ["adsdd"], 2])


class MVTouchpointConversionsTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVTouchpointConversions()

    def test_get_breakdown(self):
        self.assertEqual(
            self.model.get_breakdown(["publisher_id", "slug", "window"]),
            self.model.select_columns(["publisher", "source_id", "slug", "window"]),
        )

    def test_get_aggregates(self):
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["account_id"])],
            ["count", "conversion_value", "count_view", "conversion_value_view"],
        )

        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["account_id", "publisher_id"])],
            ["count", "conversion_value", "count_view", "conversion_value_view"],
        )


class MVConversionsTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVConversions()

    def test_get_breakdown(self):
        self.assertEqual(
            self.model.get_breakdown(["publisher_id", "slug"]),
            self.model.select_columns(["publisher", "source_id", "slug"]),
        )

    def test_get_aggregates(self):
        self.assertCountEqual([x.alias for x in self.model.get_aggregates(["account_id"])], ["count"])

        self.assertCountEqual([x.alias for x in self.model.get_aggregates(["account_id", "publisher_id"])], ["count"])


class MVMasterConversionsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_views.yaml"]

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

        self.assertCountEqual(
            [x.column_as_alias("a") for x in conversion_columns],
            [
                backtosql.SQLMatcher(
                    "SUM(CASE WHEN a.slug='ga__2' THEN conversion_count ELSE 0 END) conversion_goal_2"
                ),
                backtosql.SQLMatcher(
                    "SUM(CASE WHEN a.slug='ga__3' THEN conversion_count ELSE 0 END) conversion_goal_3"
                ),
                backtosql.SQLMatcher(
                    "SUM(CASE WHEN a.slug='omniture__4' THEN conversion_count ELSE 0 END) conversion_goal_4"
                ),
                backtosql.SQLMatcher(
                    "SUM(CASE WHEN a.slug='omniture__5' THEN conversion_count ELSE 0 END) conversion_goal_5"
                ),
            ],
        )

        self.assertListEqual(
            [x.column_as_alias("a") for x in touchpoint_columns],
            [
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_count ELSE 0 END) pixel_1_24"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_value_nano ELSE 0 END
            )/1000000000.0 total_conversion_value_pixel_1_24"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_count ELSE 0 END) pixel_1_168"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_value_nano ELSE 0 END
            )/1000000000.0 total_conversion_value_pixel_1_168"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_count ELSE 0 END) pixel_1_720"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_value_nano ELSE 0 END
            )/1000000000.0 total_conversion_value_pixel_1_720"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=2160 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_count ELSE 0 END) pixel_1_2160"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=2160 AND (1=1 AND
            (a.type=1 OR a.type IS NULL) OR 1=2 AND a.type=2) THEN conversion_value_nano ELSE 0 END
            )/1000000000.0 total_conversion_value_pixel_1_2160"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24 AND (2=1 AND
            (a.type=1 OR a.type IS NULL) OR 2=2 AND a.type=2)
            THEN conversion_count ELSE 0 END) pixel_1_24_view"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=24 AND (2=1 AND
            (a.type=1 OR a.type IS NULL) OR 2=2 AND a.type=2)
            THEN conversion_value_nano ELSE 0 END)/1000000000.0 total_conversion_value_pixel_1_24_view"""
                ),
            ],
        )

        # prefixes should be added afterwards
        self.assertEqual(
            [x.column_as_alias("a") for x in after_join_columns],
            [
                backtosql.SQLMatcher(
                    "(COALESCE(a.conversion_goal_2, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_conversion_goal_2"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_2, 0) avg_etfm_cost_per_conversion_goal_2"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_2, 0) local_avg_etfm_cost_per_conversion_goal_2"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.conversion_goal_3, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_conversion_goal_3"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_3, 0) avg_etfm_cost_per_conversion_goal_3"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_3, 0) local_avg_etfm_cost_per_conversion_goal_3"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.conversion_goal_4, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_conversion_goal_4"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_4, 0) avg_etfm_cost_per_conversion_goal_4"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_4, 0) local_avg_etfm_cost_per_conversion_goal_4"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.conversion_goal_5, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_conversion_goal_5"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_5, 0) avg_etfm_cost_per_conversion_goal_5"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_5, 0) local_avg_etfm_cost_per_conversion_goal_5"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.pixel_1_24, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_pixel_1_24"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_24, 0) avg_etfm_cost_per_pixel_1_24"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_24, 0) local_avg_etfm_cost_per_pixel_1_24"),
                backtosql.SQLMatcher(
                    "(CASE WHEN COALESCE(local_etfm_cost, 0) = 0 THEN NULL ELSE COALESCE(total_conversion_value_pixel_1_24, 0) / COALESCE(local_etfm_cost, 1) END) etfm_roas_pixel_1_24"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.pixel_1_168, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_pixel_1_168"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_168, 0) avg_etfm_cost_per_pixel_1_168"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_168, 0) local_avg_etfm_cost_per_pixel_1_168"),
                backtosql.SQLMatcher(
                    "(CASE WHEN COALESCE(local_etfm_cost, 0) = 0 THEN NULL ELSE COALESCE(total_conversion_value_pixel_1_168, 0) / COALESCE(local_etfm_cost, 1) END) etfm_roas_pixel_1_168"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.pixel_1_720, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_pixel_1_720"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_720, 0) avg_etfm_cost_per_pixel_1_720"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_720, 0) local_avg_etfm_cost_per_pixel_1_720"),
                backtosql.SQLMatcher(
                    "(CASE WHEN COALESCE(local_etfm_cost, 0) = 0 THEN NULL ELSE COALESCE(total_conversion_value_pixel_1_720, 0) / COALESCE(local_etfm_cost, 1) END) etfm_roas_pixel_1_720"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.pixel_1_2160, 0))::FLOAT /\n(NULLIF(a.clicks, 0) * 0.01)\nconversion_rate_per_pixel_1_2160"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_2160, 0) avg_etfm_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_2160, 0) local_avg_etfm_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher(
                    "(CASE WHEN COALESCE(local_etfm_cost, 0) = 0 THEN NULL ELSE COALESCE(total_conversion_value_pixel_1_2160, 0) / COALESCE(local_etfm_cost, 1) END) etfm_roas_pixel_1_2160"
                ),
                backtosql.SQLMatcher(
                    "(COALESCE(a.pixel_1_24_view, 0))::FLOAT /\n(NULLIF(a.impressions, 0) * 0.01)\nconversion_rate_per_pixel_1_24_view"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_24_view, 0) avg_etfm_cost_per_pixel_1_24_view"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(pixel_1_24_view, 0) local_avg_etfm_cost_per_pixel_1_24_view"
                ),
                backtosql.SQLMatcher(
                    "(CASE WHEN COALESCE(local_etfm_cost, 0) = 0 THEN NULL ELSE COALESCE(total_conversion_value_pixel_1_24_view, 0) / COALESCE(local_etfm_cost, 1) END) etfm_roas_pixel_1_24_view"
                ),
            ],
        )

    def test_get_query_joint_context(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)
        goals = Goals(None, conversion_goals, None, pixels, None)

        m = models.MVJointMaster()

        constraints = {
            "account_id": 123,
            "campaign_id": 223,
            "date__gte": datetime.date(2016, 7, 1),
            "date__lte": datetime.date(2016, 7, 10),
        }

        parents = [
            {"content_ad_id": 32, "source_id": 1},
            {"content_ad_id": 33, "source_id": [2, 3]},
            {"content_ad_id": 35, "source_id": [2, 4, 22]},
        ]

        context = m.get_query_joint_context(
            ["account_id", "source_id"],
            constraints,
            parents,
            ["pixel_1_24"],
            2,
            33,
            goals,
            views={
                "base": "mv_master",
                "yesterday": "mv_master",
                "conversions": "mv_conversions",
                "touchpoints": "mv_touchpointconversions",
            },
            skip_performance_columns=False,
            supports_conversions=True,
            supports_touchpoints=True,
        )

        self.assertListEqual(
            context["conversions_aggregates"],
            m.select_columns(["conversion_goal_2", "conversion_goal_3", "conversion_goal_4", "conversion_goal_5"]),
        )

        self.assertListEqual(
            context["touchpoints_aggregates"],
            m.select_columns(
                [
                    "pixel_1_24",
                    "total_conversion_value_pixel_1_24",
                    "pixel_1_168",
                    "total_conversion_value_pixel_1_168",
                    "pixel_1_720",
                    "total_conversion_value_pixel_1_720",
                    "pixel_1_2160",
                    "total_conversion_value_pixel_1_2160",
                    "pixel_1_24_view",
                    "total_conversion_value_pixel_1_24_view",
                ]
            ),
        )

        self.assertListEqual(
            context["after_join_aggregates"],
            m.select_columns(
                [
                    "conversion_rate_per_conversion_goal_2",
                    "avg_etfm_cost_per_conversion_goal_2",
                    "local_avg_etfm_cost_per_conversion_goal_2",
                    "conversion_rate_per_conversion_goal_3",
                    "avg_etfm_cost_per_conversion_goal_3",
                    "local_avg_etfm_cost_per_conversion_goal_3",
                    "conversion_rate_per_conversion_goal_4",
                    "avg_etfm_cost_per_conversion_goal_4",
                    "local_avg_etfm_cost_per_conversion_goal_4",
                    "conversion_rate_per_conversion_goal_5",
                    "avg_etfm_cost_per_conversion_goal_5",
                    "local_avg_etfm_cost_per_conversion_goal_5",
                    "conversion_rate_per_pixel_1_24",
                    "avg_etfm_cost_per_pixel_1_24",
                    "local_avg_etfm_cost_per_pixel_1_24",
                    "etfm_roas_pixel_1_24",
                    "conversion_rate_per_pixel_1_168",
                    "avg_etfm_cost_per_pixel_1_168",
                    "local_avg_etfm_cost_per_pixel_1_168",
                    "etfm_roas_pixel_1_168",
                    "conversion_rate_per_pixel_1_720",
                    "avg_etfm_cost_per_pixel_1_720",
                    "local_avg_etfm_cost_per_pixel_1_720",
                    "etfm_roas_pixel_1_720",
                    "conversion_rate_per_pixel_1_2160",
                    "avg_etfm_cost_per_pixel_1_2160",
                    "local_avg_etfm_cost_per_pixel_1_2160",
                    "etfm_roas_pixel_1_2160",
                    "conversion_rate_per_pixel_1_24_view",
                    "avg_etfm_cost_per_pixel_1_24_view",
                    "local_avg_etfm_cost_per_pixel_1_24_view",
                    "etfm_roas_pixel_1_24_view",
                ]
            ),
        )

        self.assertEqual(context["orders"][0].alias, "pixel_1_24")


class MVJointMasterAfterJoinAggregatesTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_augmenter.yaml"]

    def test_after_join_columns(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign_id=campaign.id)
        campaign_goals = dash.models.CampaignGoal.objects.filter(campaign_id=campaign.id)
        campaign_goal_values = dash.models.CampaignGoalValue.objects.filter(campaign_goal__in=campaign_goals)
        pixels = dash.models.ConversionPixel.objects.filter(account_id=campaign.account_id)

        goals = Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, None)

        m = models.MVJointMaster()

        constraints = {
            "account_id": 123,
            "campaign_id": 223,
            "date__gte": datetime.date(2016, 7, 1),
            "date__lte": datetime.date(2016, 7, 10),
        }

        parents = [
            {"content_ad_id": 32, "source_id": 1},
            {"content_ad_id": 33, "source_id": [2, 3]},
            {"content_ad_id": 35, "source_id": [2, 4, 22]},
        ]

        order_field = "etfm_performance_" + campaign_goals.get(pk=1).get_view_key()

        context = m.get_query_joint_context(
            ["account_id", "source_id", "dma"],
            constraints,
            parents,
            ["-" + order_field],
            2,
            33,
            goals,
            views={"base": "mv_master", "yesterday": "mv_master"},
            skip_performance_columns=False,
            supports_conversions=False,
            supports_touchpoints=False,
        )

        self.assertListEqual(context["after_join_aggregates"], [m.get_column(order_field)])

        self.assertEqual(context["orders"][0].alias, order_field)


class MVJointMasterPublishersTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVJointMaster()

    def test_aggregates(self):
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["placement_id"])], ALL_AGGREGATES + ["placement_type"]
        )


class MVJointMasterTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVJointMaster()

    def test_get_aggregates(self):
        self.assertCountEqual([x.alias for x in self.model.get_aggregates([])], ALL_AGGREGATES)

    @mock.patch("utils.dates_helper.local_today", return_value=datetime.date(2016, 7, 2))
    def test_get_query_joint_context(self, mock_today):
        m = models.MVJointMaster()

        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 10)
        constraints = {"account_id": 123, "campaign_id": 223, "date__gte": date_from, "date__lte": date_to}

        parents = [
            {"content_ad_id": 32, "source_id": 1},
            {"content_ad_id": 33, "source_id": [2, 3]},
            {"content_ad_id": 35, "source_id": [2, 4, 22]},
        ]

        context = m.get_query_joint_context(
            ["account_id", "source_id"],
            constraints,
            parents,
            ["-clicks"],
            2,
            33,
            Goals(None, None, None, None, None),
            views={
                "base": "mv_master",
                "yesterday": "mv_master",
                "conversions": "mv_conversions",
                "touchpoints": "mv_touchpoints",
            },
            skip_performance_columns=False,
            supports_conversions=True,
            supports_touchpoints=True,
        )

        q = context["constraints"]
        self.assertSQLEquals(
            q.generate("A"),
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
            """,
        )
        self.assertEqual(q.get_params(), [123, 223, date_from, date_to, 32, 1, 33, [2, 3], 35, [2, 4, 22]])

        q = context["yesterday_constraints"]
        self.assertSQLEquals(
            q.generate("A"),
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
            """,
        )
        self.assertEqual(q.get_params(), [123, 223, datetime.date(2016, 7, 1), 32, 1, 33, [2, 3], 35, [2, 4, 22]])

        self.assertEqual(context["offset"], 2)
        self.assertEqual(context["limit"], 33)
        self.assertEqual(context["orders"][0].alias, "clicks")

        self.assertListEqual(context["partition"], m.select_columns(["account_id"]))
