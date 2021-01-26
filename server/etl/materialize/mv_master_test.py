import collections
import datetime

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
from dash import constants
from utils import test_helper

from .mv_master import MasterView

PostclickstatsResults = collections.namedtuple(
    "Result2",
    [
        "ad_group_id",
        "postclick_source",
        "content_ad_id",
        "source_slug",
        "publisher",
        "bounced_visits",
        "conversions",
        "new_visits",
        "pageviews",
        "total_time_on_site",
        "visits",
        "users",
    ],
)


class MasterViewTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = MasterView("asd", date_from, date_to, account_id=None)

        mv.generate()

        insert_into_master_sql = mock.ANY

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE date=%(date)s"),
                    {"date": datetime.date(2016, 7, 1)},
                ),
                mock.call(
                    insert_into_master_sql,
                    {
                        "date": "2016-07-01",
                        "tzdate_from": "2016-07-01",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-07-02",
                        "tzhour_to": 4,
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                SELECT
                    ad_group_id AS ad_group_id,
                    type AS postclick_source,
                    content_ad_id AS content_ad_id,
                    source AS source_slug,
                    publisher AS publisher,
                    SUM(bounced_visits) bounced_visits,
                    json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
                    SUM(new_visits) new_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(users) users,
                    SUM(visits) visits
                FROM postclickstats
                WHERE date=%(date)s
                GROUP BY ad_group_id, postclick_source, content_ad_id, source_slug, publisher;
            """
                    ),
                    {"date": datetime.date(2016, 7, 1)},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                COPY mv_master
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                BLANKSASNULL EMPTYASNULL
                CREDENTIALS %(credentials)s
                MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": ("s3://test_bucket/materialized_views/" "mv_master/2016/07/01/mv_master_asd.csv"),
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE date=%(date)s"),
                    {"date": datetime.date(2016, 7, 2)},
                ),
                mock.call(
                    insert_into_master_sql,
                    {
                        "date": "2016-07-02",
                        "tzdate_from": "2016-07-02",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-07-03",
                        "tzhour_to": 4,
                    },
                ),
                mock.call(mock.ANY, {"date": datetime.date(2016, 7, 2)}),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_master/2016/07/02/mv_master_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE date=%(date)s"),
                    {"date": datetime.date(2016, 7, 3)},
                ),
                mock.call(
                    insert_into_master_sql,
                    {
                        "date": "2016-07-03",
                        "tzdate_from": "2016-07-03",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-07-04",
                        "tzhour_to": 4,
                    },
                ),
                mock.call(mock.ANY, {"date": datetime.date(2016, 7, 3)}),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_master/2016/07/03/mv_master_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_generate_rows(self):

        date = datetime.date(2016, 5, 1)

        mock_cursor = mock.MagicMock()

        postclickstats_return_value = [
            (
                (3, 1),
                (
                    date,
                    3,
                    1,
                    1,
                    1,
                    1,
                    "bla.com",
                    "bla.com__3",
                    constants.DeviceType.UNKNOWN,
                    None,
                    None,
                    constants.Environment.UNKNOWN,
                    constants.ZemPlacementType.UNKNOWN,
                    constants.VideoPlaybackMethod.UNKNOWN,
                    None,
                    None,
                    None,
                    None,
                    constants.Age.UNDEFINED,
                    constants.Gender.UNDEFINED,
                    constants.AgeGender.UNDEFINED,
                    0,
                    0,
                    0,
                    0,
                    2,
                    22,
                    12,
                    100,
                    20,
                    0,
                    0,
                    0,
                    0,
                    10,
                    9,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    constants.BrowserFamily.UNKNOWN,
                    constants.ConnectionType.UNKNOWN,
                    None,
                    None,
                ),
                None,
            ),
            (
                (1, 3),
                (
                    date,
                    1,
                    1,
                    3,
                    3,
                    3,
                    "nesto.com",
                    "nesto.com__1",
                    constants.DeviceType.UNKNOWN,
                    None,
                    None,
                    constants.Environment.UNKNOWN,
                    constants.ZemPlacementType.UNKNOWN,
                    constants.VideoPlaybackMethod.UNKNOWN,
                    None,
                    None,
                    None,
                    None,
                    constants.Age.UNDEFINED,
                    constants.Gender.UNDEFINED,
                    constants.AgeGender.UNDEFINED,
                    0,
                    0,
                    0,
                    0,
                    2,
                    22,
                    12,
                    100,
                    20,
                    0,
                    0,
                    0,
                    0,
                    11,
                    10,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    constants.BrowserFamily.UNKNOWN,
                    constants.ConnectionType.UNKNOWN,
                    None,
                    None,
                ),
                None,
            ),
            (
                (3, 4),
                (
                    date,
                    3,
                    2,
                    2,
                    2,
                    4,
                    "trol",
                    "trol__3",
                    constants.DeviceType.UNKNOWN,
                    None,
                    None,
                    constants.Environment.UNKNOWN,
                    constants.ZemPlacementType.UNKNOWN,
                    constants.VideoPlaybackMethod.UNKNOWN,
                    None,
                    None,
                    None,
                    None,
                    constants.Age.UNDEFINED,
                    constants.Gender.UNDEFINED,
                    constants.AgeGender.UNDEFINED,
                    0,
                    0,
                    0,
                    0,
                    2,
                    22,
                    12,
                    100,
                    20,
                    0,
                    0,
                    0,
                    0,
                    12,
                    11,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    constants.BrowserFamily.UNKNOWN,
                    constants.ConnectionType.UNKNOWN,
                    None,
                    None,
                ),
                None,
            ),
        ]

        with mock.patch.object(MasterView, "get_postclickstats", return_value=postclickstats_return_value):
            mv = MasterView("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
            rows = list(mv.generate_rows(mock_cursor, date))

            self.assertCountEqual(
                rows,
                [
                    (
                        date,
                        3,
                        1,
                        1,
                        1,
                        1,
                        "bla.com",
                        "bla.com__3",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.Environment.UNKNOWN,
                        constants.ZemPlacementType.UNKNOWN,
                        constants.VideoPlaybackMethod.UNKNOWN,
                        None,
                        None,
                        None,
                        None,
                        constants.Age.UNDEFINED,
                        constants.Gender.UNDEFINED,
                        constants.AgeGender.UNDEFINED,
                        0,
                        0,
                        0,
                        0,
                        2,
                        22,
                        12,
                        100,
                        20,
                        0,
                        0,
                        0,
                        0,
                        10,
                        9,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        constants.BrowserFamily.UNKNOWN,
                        constants.ConnectionType.UNKNOWN,
                        None,
                        None,
                    ),
                    (
                        date,
                        1,
                        1,
                        3,
                        3,
                        3,
                        "nesto.com",
                        "nesto.com__1",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.Environment.UNKNOWN,
                        constants.ZemPlacementType.UNKNOWN,
                        constants.VideoPlaybackMethod.UNKNOWN,
                        None,
                        None,
                        None,
                        None,
                        constants.Age.UNDEFINED,
                        constants.Gender.UNDEFINED,
                        constants.AgeGender.UNDEFINED,
                        0,
                        0,
                        0,
                        0,
                        2,
                        22,
                        12,
                        100,
                        20,
                        0,
                        0,
                        0,
                        0,
                        11,
                        10,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        constants.BrowserFamily.UNKNOWN,
                        constants.ConnectionType.UNKNOWN,
                        None,
                        None,
                    ),
                    (
                        date,
                        3,
                        2,
                        2,
                        2,
                        4,
                        "trol",
                        "trol__3",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.Environment.UNKNOWN,
                        constants.ZemPlacementType.UNKNOWN,
                        constants.VideoPlaybackMethod.UNKNOWN,
                        None,
                        None,
                        None,
                        None,
                        constants.Age.UNDEFINED,
                        constants.Gender.UNDEFINED,
                        constants.AgeGender.UNDEFINED,
                        0,
                        0,
                        0,
                        0,
                        2,
                        22,
                        12,
                        100,
                        20,
                        0,
                        0,
                        0,
                        0,
                        12,
                        11,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        constants.BrowserFamily.UNKNOWN,
                        constants.ConnectionType.UNKNOWN,
                        None,
                        None,
                    ),
                ],
            )

    @mock.patch("etl.materialize.mv_master.MasterView.get_postclickstats_query_results")
    def test_get_postclickstats(self, mock_get_postclickstats_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_postclickstats_query_results.return_value = [
            PostclickstatsResults(1, "gaapi", 1, "testsource", "Bla.com", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
            # this one should be left out as its from lower priority postclick source
            PostclickstatsResults(1, "ga_mail", 2, "testsource", "beer.com", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
            PostclickstatsResults(3, "gaapi", 3, "adblade", "Nesto.com", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
            PostclickstatsResults(2, "omniture", 4, "testsource", "Trol", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
        ]

        mv = MasterView("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
        mv.prefetch()

        self.assertCountEqual(
            list(mv.get_postclickstats(None, date)),
            [
                (
                    (3, 1),
                    (
                        date,
                        3,
                        1,
                        1,
                        1,
                        1,
                        "bla.com",
                        "bla.com__3",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.Environment.UNKNOWN,
                        constants.ZemPlacementType.UNKNOWN,
                        constants.VideoPlaybackMethod.UNKNOWN,
                        None,
                        None,
                        None,
                        None,
                        constants.Age.UNDEFINED,
                        constants.Gender.UNDEFINED,
                        constants.AgeGender.UNDEFINED,
                        0,
                        0,
                        0,
                        0,
                        2,
                        22,
                        12,
                        100,
                        20,
                        0,
                        0,
                        0,
                        0,
                        24,
                        2,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        constants.BrowserFamily.UNKNOWN,
                        constants.ConnectionType.UNKNOWN,
                        None,
                        None,
                    ),
                    ("{einpix: 2}", "gaapi"),
                ),
                (
                    (3, 4),
                    (
                        date,
                        3,
                        2,
                        2,
                        2,
                        4,
                        "trol",
                        "trol__3",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.Environment.UNKNOWN,
                        constants.ZemPlacementType.UNKNOWN,
                        constants.VideoPlaybackMethod.UNKNOWN,
                        None,
                        None,
                        None,
                        None,
                        constants.Age.UNDEFINED,
                        constants.Gender.UNDEFINED,
                        constants.AgeGender.UNDEFINED,
                        0,
                        0,
                        0,
                        0,
                        2,
                        22,
                        12,
                        100,
                        20,
                        0,
                        0,
                        0,
                        0,
                        24,
                        2,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        constants.BrowserFamily.UNKNOWN,
                        constants.ConnectionType.UNKNOWN,
                        None,
                        None,
                    ),
                    ("{einpix: 2}", "omniture"),
                ),
                (
                    (1, 3),
                    (
                        date,
                        1,
                        1,
                        3,
                        3,
                        3,
                        "nesto.com",
                        "nesto.com__1",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.Environment.UNKNOWN,
                        constants.ZemPlacementType.UNKNOWN,
                        constants.VideoPlaybackMethod.UNKNOWN,
                        None,
                        None,
                        None,
                        None,
                        constants.Age.UNDEFINED,
                        constants.Gender.UNDEFINED,
                        constants.AgeGender.UNDEFINED,
                        0,
                        0,
                        0,
                        0,
                        2,
                        22,
                        12,
                        100,
                        20,
                        0,
                        0,
                        0,
                        0,
                        24,
                        2,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        constants.BrowserFamily.UNKNOWN,
                        constants.ConnectionType.UNKNOWN,
                        None,
                        None,
                    ),
                    ("{einpix: 2}", "gaapi"),
                ),
            ],
        )

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = MasterView("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
        sql, params = mv.prepare_postclickstats_query(date)

        self.assertSQLEquals(
            sql,
            """
        SELECT
            ad_group_id AS ad_group_id,
            type AS postclick_source,
            content_ad_id AS content_ad_id,
            source AS source_slug,
            publisher AS publisher,
            SUM(bounced_visits) bounced_visits,
            json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
            SUM(new_visits) new_visits,
            SUM(pageviews) pageviews,
            SUM(total_time_on_site) total_time_on_site,
            SUM(users) users,
            SUM(visits) visits
        FROM postclickstats
        WHERE date=%(date)s
        GROUP BY
            ad_group_id,
            postclick_source,
            content_ad_id,
            source_slug,
            publisher;""",
        )

        self.assertDictEqual(params, {"date": date})


class MasterViewTestByAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        account_id = 1
        mv = MasterView("asd", date_from, date_to, account_id=account_id)

        mv.generate()

        insert_into_master_sql = mock.ANY
        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE date=%(date)s AND account_id=%(account_id)s"),
                    {"date": datetime.date(2016, 7, 1), "account_id": account_id},
                ),
                mock.call(
                    insert_into_master_sql,
                    {
                        "date": "2016-07-01",
                        "tzdate_from": "2016-07-01",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-07-02",
                        "tzhour_to": 4,
                        "account_id": 1,
                        "ad_group_id": test_helper.ListMatcher([1, 3, 4]),
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                SELECT
                    ad_group_id AS ad_group_id,
                    type AS postclick_source,
                    content_ad_id AS content_ad_id,
                    source AS source_slug,
                    publisher AS publisher,
                    SUM(bounced_visits) bounced_visits,
                    json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
                    SUM(new_visits) new_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(users) users,
                    SUM(visits) visits
                FROM postclickstats
                WHERE date=%(date)s AND ad_group_id=ANY(%(ad_group_id)s)
                GROUP BY ad_group_id, postclick_source, content_ad_id, source_slug, publisher;
            """
                    ),
                    {"date": datetime.date(2016, 7, 1), "ad_group_id": test_helper.ListMatcher([1, 3, 4])},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                COPY mv_master
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                BLANKSASNULL EMPTYASNULL
                CREDENTIALS %(credentials)s
                MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_master/2016/07/01/mv_master_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE date=%(date)s AND account_id=%(account_id)s"),
                    {"date": datetime.date(2016, 7, 2), "account_id": account_id},
                ),
                mock.call(
                    insert_into_master_sql,
                    {
                        "date": "2016-07-02",
                        "tzdate_from": "2016-07-02",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-07-03",
                        "tzhour_to": 4,
                        "account_id": 1,
                        "ad_group_id": test_helper.ListMatcher([1, 3, 4]),
                    },
                ),
                mock.call(
                    mock.ANY, {"date": datetime.date(2016, 7, 2), "ad_group_id": test_helper.ListMatcher([1, 3, 4])}
                ),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_master/2016/07/02/mv_master_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE date=%(date)s AND account_id=%(account_id)s"),
                    {"date": datetime.date(2016, 7, 3), "account_id": account_id},
                ),
                mock.call(
                    insert_into_master_sql,
                    {
                        "date": "2016-07-03",
                        "tzdate_from": "2016-07-03",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-07-04",
                        "tzhour_to": 4,
                        "account_id": 1,
                        "ad_group_id": test_helper.ListMatcher([1, 3, 4]),
                    },
                ),
                mock.call(
                    mock.ANY, {"date": datetime.date(2016, 7, 3), "ad_group_id": test_helper.ListMatcher([1, 3, 4])}
                ),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_master/2016/07/03/mv_master_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = MasterView("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)
        sql, params = mv.prepare_postclickstats_query(date)

        self.assertSQLEquals(
            sql,
            """
        SELECT
            ad_group_id AS ad_group_id,
            type AS postclick_source,
            content_ad_id AS content_ad_id,
            source AS source_slug,
            publisher AS publisher,
            SUM(bounced_visits) bounced_visits,
            json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
            SUM(new_visits) new_visits,
            SUM(pageviews) pageviews,
            SUM(total_time_on_site) total_time_on_site,
            SUM(users) users,
            SUM(visits) visits
        FROM postclickstats
        WHERE date=%(date)s AND ad_group_id=ANY(%(ad_group_id)s)
        GROUP BY
            ad_group_id,
            postclick_source,
            content_ad_id,
            source_slug,
            publisher;""",
        )

        self.assertDictEqual(params, {"date": date, "ad_group_id": test_helper.ListMatcher([1, 3, 4])})
