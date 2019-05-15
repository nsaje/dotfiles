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
    "license_fee",
    "local_license_fee",
    "margin",
    "local_margin",
    "media_cost",
    "local_media_cost",
    "e_media_cost",
    "local_e_media_cost",
    "data_cost",
    "local_data_cost",
    "e_data_cost",
    "local_e_data_cost",
    "at_cost",
    "local_at_cost",
    "et_cost",
    "local_et_cost",
    "etf_cost",
    "local_etf_cost",
    "etfm_cost",
    "local_etfm_cost",  # noqa
    "total_cost",
    "local_total_cost",
    "billing_cost",
    "local_billing_cost",
    "agency_cost",
    "local_agency_cost",  # legacy
    "ctr",
    "cpc",
    "local_cpc",
    "et_cpc",
    "local_et_cpc",
    "etfm_cpc",
    "local_etfm_cpc",
    "cpm",
    "local_cpm",
    "et_cpm",
    "local_et_cpm",
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
    "avg_cost_per_minute",
    "local_avg_cost_per_minute",
    "avg_et_cost_per_minute",
    "local_avg_et_cost_per_minute",
    "avg_etfm_cost_per_minute",
    "local_avg_etfm_cost_per_minute",  # noqa
    "avg_cost_per_non_bounced_visit",
    "local_avg_cost_per_non_bounced_visit",
    "avg_et_cost_per_non_bounced_visit",
    "local_avg_et_cost_per_non_bounced_visit",
    "avg_etfm_cost_per_non_bounced_visit",
    "local_avg_etfm_cost_per_non_bounced_visit",  # noqa
    "avg_cost_per_pageview",
    "local_avg_cost_per_pageview",
    "avg_et_cost_per_pageview",
    "local_avg_et_cost_per_pageview",
    "avg_etfm_cost_per_pageview",
    "local_avg_etfm_cost_per_pageview",  # noqa
    "avg_cost_for_new_visitor",
    "local_avg_cost_for_new_visitor",
    "avg_et_cost_for_new_visitor",
    "local_avg_et_cost_for_new_visitor",
    "avg_etfm_cost_for_new_visitor",
    "local_avg_etfm_cost_for_new_visitor",  # noqa
    "avg_cost_per_visit",
    "local_avg_cost_per_visit",
    "avg_et_cost_per_visit",
    "local_avg_et_cost_per_visit",
    "avg_etfm_cost_per_visit",
    "local_avg_etfm_cost_per_visit",  # noqa
    "video_start",
    "video_first_quartile",
    "video_midpoint",
    "video_third_quartile",
    "video_complete",
    "video_progress_3s",  # noqa
    "video_cpv",
    "local_video_cpv",
    "video_et_cpv",
    "local_video_et_cpv",
    "video_etfm_cpv",
    "local_video_etfm_cpv",
    "video_cpcv",
    "local_video_cpcv",
    "video_et_cpcv",
    "local_video_et_cpcv",
    "video_etfm_cpcv",
    "local_video_etfm_cpcv",  # noqa
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
        self.assertCountEqual([x.alias for x in self.model.get_aggregates([], "mv_master")], ALL_AGGREGATES)

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
        self.assertEqual(context["aggregates"], self.model.get_aggregates(breakdown, ""))
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
            ["-yesterday_cost"],
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
                [
                    "yesterday_cost",
                    "local_yesterday_cost",
                    "e_yesterday_cost",
                    "local_e_yesterday_cost",
                    "yesterday_et_cost",
                    "local_yesterday_et_cost",
                    "yesterday_at_cost",
                    "local_yesterday_at_cost",
                    "yesterday_etfm_cost",
                    "local_yesterday_etfm_cost",
                ]
            ),
        )
        self.assertEqual(context["view"], "mv_account")
        self.assertSQLEquals(context["orders"][0].only_alias(), "yesterday_cost DESC NULLS LAST")

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
            [x.alias for x in self.model.get_aggregates(["publisher_id"], "mv_master_pubs")],
            ALL_AGGREGATES + ["external_id", "publisher_id"],
        )
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["publisher_id"], "mv_master")],
            ALL_AGGREGATES + ["publisher_id"],
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
            [x.alias for x in self.model.get_aggregates(["account_id"], "mv_account_touch")],
            ["count", "conversion_value"],
        )

        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["account_id", "publisher_id"], "mv_touchpointconversions")],
            ["publisher_id", "count", "conversion_value"],
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
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["account_id"], "mv_account_conv")], ["count"]
        )

        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["account_id", "publisher_id"], "mv_conversions")],
            ["publisher_id", "count"],
        )


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
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168 AND (2=1 AND
            (a.type=1 OR a.type IS NULL) OR 2=2 AND a.type=2) THEN conversion_count ELSE 0 END) pixel_1_168_view"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=168 AND (2=1 AND
            (a.type=1 OR a.type IS NULL) OR 2=2 AND a.type=2) THEN conversion_value_nano ELSE 0 END
            )/1000000000.0 total_conversion_value_pixel_1_168_view"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720 AND (2=1 AND
            (a.type=1 OR a.type IS NULL) OR 2=2 AND a.type=2) THEN conversion_count ELSE 0 END) pixel_1_720_view"""
                ),
                backtosql.SQLMatcher(
                    """SUM(CASE WHEN a.slug='test' AND a.account_id=1 AND a.conversion_window<=720 AND (2=1 AND
            (a.type=1 OR a.type IS NULL) OR 2=2 AND a.type=2) THEN conversion_value_nano ELSE 0 END
            )/1000000000.0 total_conversion_value_pixel_1_720_view"""
                ),
            ],
        )

        # prefixes should be added afterwards
        self.assertEqual(
            [x.column_as_alias("a") for x in after_join_columns],
            [
                backtosql.SQLMatcher("e_media_cost / NULLIF(conversion_goal_2, 0) avg_cost_per_conversion_goal_2"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(conversion_goal_2, 0) local_avg_cost_per_conversion_goal_2"
                ),  # noqa
                backtosql.SQLMatcher("et_cost / NULLIF(conversion_goal_2, 0) avg_et_cost_per_conversion_goal_2"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(conversion_goal_2, 0) local_avg_et_cost_per_conversion_goal_2"
                ),  # noqa
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_2, 0) avg_etfm_cost_per_conversion_goal_2"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_2, 0) local_avg_etfm_cost_per_conversion_goal_2"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(conversion_goal_3, 0) avg_cost_per_conversion_goal_3"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(conversion_goal_3, 0) local_avg_cost_per_conversion_goal_3"
                ),  # noqa
                backtosql.SQLMatcher("et_cost / NULLIF(conversion_goal_3, 0) avg_et_cost_per_conversion_goal_3"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(conversion_goal_3, 0) local_avg_et_cost_per_conversion_goal_3"
                ),  # noqa
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_3, 0) avg_etfm_cost_per_conversion_goal_3"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_3, 0) local_avg_etfm_cost_per_conversion_goal_3"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(conversion_goal_4, 0) avg_cost_per_conversion_goal_4"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(conversion_goal_4, 0) local_avg_cost_per_conversion_goal_4"
                ),  # noqa
                backtosql.SQLMatcher("et_cost / NULLIF(conversion_goal_4, 0) avg_et_cost_per_conversion_goal_4"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(conversion_goal_4, 0) local_avg_et_cost_per_conversion_goal_4"
                ),  # noqa
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_4, 0) avg_etfm_cost_per_conversion_goal_4"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_4, 0) local_avg_etfm_cost_per_conversion_goal_4"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(conversion_goal_5, 0) avg_cost_per_conversion_goal_5"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(conversion_goal_5, 0) local_avg_cost_per_conversion_goal_5"
                ),  # noqa
                backtosql.SQLMatcher("et_cost / NULLIF(conversion_goal_5, 0) avg_et_cost_per_conversion_goal_5"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(conversion_goal_5, 0) local_avg_et_cost_per_conversion_goal_5"
                ),  # noqa
                backtosql.SQLMatcher("etfm_cost / NULLIF(conversion_goal_5, 0) avg_etfm_cost_per_conversion_goal_5"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(conversion_goal_5, 0) local_avg_etfm_cost_per_conversion_goal_5"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_24, 0) avg_cost_per_pixel_1_24"),
                backtosql.SQLMatcher("local_e_media_cost / NULLIF(pixel_1_24, 0) local_avg_cost_per_pixel_1_24"),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_24, 0) avg_et_cost_per_pixel_1_24"),
                backtosql.SQLMatcher("local_et_cost / NULLIF(pixel_1_24, 0) local_avg_et_cost_per_pixel_1_24"),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_24, 0) avg_etfm_cost_per_pixel_1_24"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_24, 0) local_avg_etfm_cost_per_pixel_1_24"),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_24, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_24"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_24, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_24"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_24, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_24"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_168, 0) avg_cost_per_pixel_1_168"),
                backtosql.SQLMatcher("local_e_media_cost / NULLIF(pixel_1_168, 0) local_avg_cost_per_pixel_1_168"),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_168, 0) avg_et_cost_per_pixel_1_168"),
                backtosql.SQLMatcher("local_et_cost / NULLIF(pixel_1_168, 0) local_avg_et_cost_per_pixel_1_168"),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_168, 0) avg_etfm_cost_per_pixel_1_168"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_168, 0) local_avg_etfm_cost_per_pixel_1_168"),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_168, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_168"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_168, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_168"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_168, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_168"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_720, 0) avg_cost_per_pixel_1_720"),
                backtosql.SQLMatcher("local_e_media_cost / NULLIF(pixel_1_720, 0) local_avg_cost_per_pixel_1_720"),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_720, 0) avg_et_cost_per_pixel_1_720"),
                backtosql.SQLMatcher("local_et_cost / NULLIF(pixel_1_720, 0) local_avg_et_cost_per_pixel_1_720"),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_720, 0) avg_etfm_cost_per_pixel_1_720"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_720, 0) local_avg_etfm_cost_per_pixel_1_720"),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_720, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_720"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_720, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_720"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_720, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_720"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_2160, 0) avg_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher("local_e_media_cost / NULLIF(pixel_1_2160, 0) local_avg_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_2160, 0) avg_et_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher("local_et_cost / NULLIF(pixel_1_2160, 0) local_avg_et_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_2160, 0) avg_etfm_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher("local_etfm_cost / NULLIF(pixel_1_2160, 0) local_avg_etfm_cost_per_pixel_1_2160"),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_2160, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_2160"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_2160, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_2160"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_2160, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_2160"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_24_view, 0) avg_cost_per_pixel_1_24_view"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(pixel_1_24_view, 0) local_avg_cost_per_pixel_1_24_view"
                ),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_24_view, 0) avg_et_cost_per_pixel_1_24_view"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(pixel_1_24_view, 0) local_avg_et_cost_per_pixel_1_24_view"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_24_view, 0) avg_etfm_cost_per_pixel_1_24_view"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(pixel_1_24_view, 0) local_avg_etfm_cost_per_pixel_1_24_view"
                ),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_24_view, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_24_view"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_24_view, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_24_view"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_24_view, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_24_view"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_168_view, 0) avg_cost_per_pixel_1_168_view"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(pixel_1_168_view, 0) local_avg_cost_per_pixel_1_168_view"
                ),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_168_view, 0) avg_et_cost_per_pixel_1_168_view"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(pixel_1_168_view, 0) local_avg_et_cost_per_pixel_1_168_view"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_168_view, 0) avg_etfm_cost_per_pixel_1_168_view"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(pixel_1_168_view, 0) local_avg_etfm_cost_per_pixel_1_168_view"
                ),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_168_view, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_168_view"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_168_view, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_168_view"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_168_view, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_168_view"
                ),  # noqa
                backtosql.SQLMatcher("e_media_cost / NULLIF(pixel_1_720_view, 0) avg_cost_per_pixel_1_720_view"),
                backtosql.SQLMatcher(
                    "local_e_media_cost / NULLIF(pixel_1_720_view, 0) local_avg_cost_per_pixel_1_720_view"
                ),
                backtosql.SQLMatcher("et_cost / NULLIF(pixel_1_720_view, 0) avg_et_cost_per_pixel_1_720_view"),
                backtosql.SQLMatcher(
                    "local_et_cost / NULLIF(pixel_1_720_view, 0) local_avg_et_cost_per_pixel_1_720_view"
                ),
                backtosql.SQLMatcher("etfm_cost / NULLIF(pixel_1_720_view, 0) avg_etfm_cost_per_pixel_1_720_view"),
                backtosql.SQLMatcher(
                    "local_etfm_cost / NULLIF(pixel_1_720_view, 0) local_avg_etfm_cost_per_pixel_1_720_view"
                ),
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_720_view, 0) - COALESCE(local_e_media_cost, 0) roas_pixel_1_720_view"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_720_view, 0) - COALESCE(local_et_cost, 0) et_roas_pixel_1_720_view"
                ),  # noqa
                backtosql.SQLMatcher(
                    "COALESCE(total_conversion_value_pixel_1_720_view, 0) - COALESCE(local_etfm_cost, 0) etfm_roas_pixel_1_720_view"
                ),  # noqa
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
                    "pixel_1_168_view",
                    "total_conversion_value_pixel_1_168_view",
                    "pixel_1_720_view",
                    "total_conversion_value_pixel_1_720_view",
                ]
            ),
        )

        self.assertListEqual(
            context["after_join_aggregates"],
            m.select_columns(
                [
                    "avg_cost_per_conversion_goal_2",
                    "local_avg_cost_per_conversion_goal_2",
                    "avg_et_cost_per_conversion_goal_2",
                    "local_avg_et_cost_per_conversion_goal_2",
                    "avg_etfm_cost_per_conversion_goal_2",
                    "local_avg_etfm_cost_per_conversion_goal_2",
                    "avg_cost_per_conversion_goal_3",
                    "local_avg_cost_per_conversion_goal_3",
                    "avg_et_cost_per_conversion_goal_3",
                    "local_avg_et_cost_per_conversion_goal_3",
                    "avg_etfm_cost_per_conversion_goal_3",
                    "local_avg_etfm_cost_per_conversion_goal_3",
                    "avg_cost_per_conversion_goal_4",
                    "local_avg_cost_per_conversion_goal_4",
                    "avg_et_cost_per_conversion_goal_4",
                    "local_avg_et_cost_per_conversion_goal_4",
                    "avg_etfm_cost_per_conversion_goal_4",
                    "local_avg_etfm_cost_per_conversion_goal_4",
                    "avg_cost_per_conversion_goal_5",
                    "local_avg_cost_per_conversion_goal_5",
                    "avg_et_cost_per_conversion_goal_5",
                    "local_avg_et_cost_per_conversion_goal_5",
                    "avg_etfm_cost_per_conversion_goal_5",
                    "local_avg_etfm_cost_per_conversion_goal_5",
                    "avg_cost_per_pixel_1_24",
                    "local_avg_cost_per_pixel_1_24",
                    "avg_et_cost_per_pixel_1_24",
                    "local_avg_et_cost_per_pixel_1_24",
                    "avg_etfm_cost_per_pixel_1_24",
                    "local_avg_etfm_cost_per_pixel_1_24",
                    "roas_pixel_1_24",
                    "et_roas_pixel_1_24",
                    "etfm_roas_pixel_1_24",
                    "avg_cost_per_pixel_1_168",
                    "local_avg_cost_per_pixel_1_168",
                    "avg_et_cost_per_pixel_1_168",
                    "local_avg_et_cost_per_pixel_1_168",
                    "avg_etfm_cost_per_pixel_1_168",
                    "local_avg_etfm_cost_per_pixel_1_168",
                    "roas_pixel_1_168",
                    "et_roas_pixel_1_168",
                    "etfm_roas_pixel_1_168",
                    "avg_cost_per_pixel_1_720",
                    "local_avg_cost_per_pixel_1_720",
                    "avg_et_cost_per_pixel_1_720",
                    "local_avg_et_cost_per_pixel_1_720",
                    "avg_etfm_cost_per_pixel_1_720",
                    "local_avg_etfm_cost_per_pixel_1_720",
                    "roas_pixel_1_720",
                    "et_roas_pixel_1_720",
                    "etfm_roas_pixel_1_720",
                    "avg_cost_per_pixel_1_2160",
                    "local_avg_cost_per_pixel_1_2160",
                    "avg_et_cost_per_pixel_1_2160",
                    "local_avg_et_cost_per_pixel_1_2160",
                    "avg_etfm_cost_per_pixel_1_2160",
                    "local_avg_etfm_cost_per_pixel_1_2160",
                    "roas_pixel_1_2160",
                    "et_roas_pixel_1_2160",
                    "etfm_roas_pixel_1_2160",
                    "avg_cost_per_pixel_1_24_view",
                    "local_avg_cost_per_pixel_1_24_view",
                    "avg_et_cost_per_pixel_1_24_view",
                    "local_avg_et_cost_per_pixel_1_24_view",
                    "avg_etfm_cost_per_pixel_1_24_view",
                    "local_avg_etfm_cost_per_pixel_1_24_view",
                    "roas_pixel_1_24_view",
                    "et_roas_pixel_1_24_view",
                    "etfm_roas_pixel_1_24_view",
                    "avg_cost_per_pixel_1_168_view",
                    "local_avg_cost_per_pixel_1_168_view",
                    "avg_et_cost_per_pixel_1_168_view",
                    "local_avg_et_cost_per_pixel_1_168_view",
                    "avg_etfm_cost_per_pixel_1_168_view",
                    "local_avg_etfm_cost_per_pixel_1_168_view",
                    "roas_pixel_1_168_view",
                    "et_roas_pixel_1_168_view",
                    "etfm_roas_pixel_1_168_view",
                    "avg_cost_per_pixel_1_720_view",
                    "local_avg_cost_per_pixel_1_720_view",
                    "avg_et_cost_per_pixel_1_720_view",
                    "local_avg_et_cost_per_pixel_1_720_view",
                    "avg_etfm_cost_per_pixel_1_720_view",
                    "local_avg_etfm_cost_per_pixel_1_720_view",
                    "roas_pixel_1_720_view",
                    "et_roas_pixel_1_720_view",
                    "etfm_roas_pixel_1_720_view",
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

        order_field = "performance_" + campaign_goals.get(pk=1).get_view_key()

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

        self.assertListEqual(
            context["after_join_aggregates"], [m.get_column(order_field), m.get_column("etfm_" + order_field)]
        )

        self.assertEqual(context["orders"][0].alias, order_field)


class MVJointMasterPublishersTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVJointMaster()

    def test_aggregates(self):
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["publisher_id"], "mv_master_pubs")],
            ALL_AGGREGATES + ["external_id", "publisher_id"],
        )
        self.assertCountEqual(
            [x.alias for x in self.model.get_aggregates(["publisher_id"], "mv_master")],
            ALL_AGGREGATES + ["publisher_id"],
        )


class MVJointMasterTest(TestCase, backtosql.TestSQLMixin):
    def setUp(self):
        self.model = models.MVJointMaster()

    def test_get_aggregates(self):
        self.assertCountEqual([x.alias for x in self.model.get_aggregates([], "mv_master")], ALL_AGGREGATES)

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
