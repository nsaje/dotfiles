import collections
import backtosql
import datetime
import mock

from django.test import TestCase, override_settings

from dash import constants

from utils import test_helper

from .mv_master_spark import MasterSpark


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


class MasterSparkTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        spark_session = mock.MagicMock()
        mv = MasterSpark("asd", date_from, date_to, account_id=None, spark_session=spark_session)

        mv.generate()

        self.assertEqual(spark_session.run_file.call_count, 7)
        spark_session.run_file.assert_has_calls(
            [
                mock.call("sql_to_table.py.tmpl", sql=mock.ANY, table="mv_master_stats"),
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master_postclick/data.csv",
                    schema=mock.ANY,
                    table="mv_master_postclick",
                ),
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master_diff/*.gz",
                    schema=mock.ANY,
                    table="mv_master_diff",
                ),
                mock.call("sql_to_table.py.tmpl", sql=mock.ANY, table="mv_master_diff"),
                mock.call(
                    "union_tables.py.tmpl",
                    source_table_1="mv_master_stats",
                    source_table_2="mv_master_postclick",
                    table="mv_master",
                ),
                mock.call(
                    "union_tables.py.tmpl",
                    source_table_1="mv_master",
                    source_table_2="mv_master_diff",
                    table="mv_master",
                ),
                mock.call("cache_table.py.tmpl", table="mv_master"),
            ]
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
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
                    {"date": datetime.date(2016, 7, 2)},
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
                    {"date": datetime.date(2016, 7, 3)},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                    UNLOAD
                        ('SELECT * FROM mv_master_diff WHERE (date BETWEEN \\'2016-07-01\\' AND \\'2016-07-03\\') ')
                    TO %(s3_url)s
                    DELIMITER AS %(delimiter)s
                    CREDENTIALS %(credentials)s
                    ESCAPE NULL AS '$NA$'
                    GZIP
                    MANIFEST;
                    """
                    ),
                    {
                        "s3_url": "s3://test_bucket/spark/asd/mv_master_diff/mv_master_diff-2016-07-01-2016-07-03-0",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_generate_rows(self):

        date = datetime.date(2016, 5, 1)

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
                    constants.PlacementMedium.UNKNOWN,
                    constants.PlacementType.UNKNOWN,
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
                    "{einpix: 2}",
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
                    constants.PlacementMedium.UNKNOWN,
                    constants.PlacementType.UNKNOWN,
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
                    "{einpix: 2}",
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
                    constants.PlacementMedium.UNKNOWN,
                    constants.PlacementType.UNKNOWN,
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
                    "{einpix: 2}",
                    None,
                ),
                None,
            ),
        ]

        with mock.patch.object(MasterSpark, "get_postclickstats", return_value=postclickstats_return_value):
            mv = MasterSpark("asd", datetime.date(2016, 5, 1), datetime.date(2016, 5, 1), account_id=None)
            rows = list(mv.generate_rows())

            self.maxDiff = None
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
                        constants.PlacementMedium.UNKNOWN,
                        constants.PlacementType.UNKNOWN,
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
                        "{einpix: 2}",
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
                        constants.PlacementMedium.UNKNOWN,
                        constants.PlacementType.UNKNOWN,
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
                        "{einpix: 2}",
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
                        constants.PlacementMedium.UNKNOWN,
                        constants.PlacementType.UNKNOWN,
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
                        "{einpix: 2}",
                        None,
                    ),
                ],
            )

    @mock.patch("etl.materialize.mv_master_spark.MasterSpark.get_postclickstats_query_results")
    def test_get_postclickstats(self, mock_get_postclickstats_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_postclickstats_query_results.return_value = [
            PostclickstatsResults(1, "gaapi", 1, "outbrain", "Bla.com", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
            # this one should be left out as its from lower priority postclick source
            PostclickstatsResults(1, "ga_mail", 2, "outbrain", "beer.com", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
            PostclickstatsResults(3, "gaapi", 3, "adblade", "Nesto.com", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
            PostclickstatsResults(2, "omniture", 4, "outbrain", "Trol", 12, "{einpix: 2}", 22, 100, 20, 2, 24),
        ]

        mv = MasterSpark("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
        mv.prefetch()

        self.maxDiff = None
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
                        "Bla.com",
                        "Bla.com__3",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.PlacementMedium.UNKNOWN,
                        constants.PlacementType.UNKNOWN,
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
                        "Trol",
                        "Trol__3",
                        constants.DeviceType.UNKNOWN,
                        None,
                        None,
                        constants.PlacementMedium.UNKNOWN,
                        constants.PlacementType.UNKNOWN,
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
                        constants.PlacementMedium.UNKNOWN,
                        constants.PlacementType.UNKNOWN,
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
                    ),
                    ("{einpix: 2}", "gaapi"),
                ),
            ],
        )

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = MasterSpark("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
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


class MasterSparkTestByAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        account_id = 1
        spark_session = mock.MagicMock()
        mv = MasterSpark("asd", date_from, date_to, account_id=account_id, spark_session=spark_session)

        mv.generate()

        self.assertEqual(spark_session.run_file.call_count, 7)
        spark_session.run_file.assert_has_calls(
            [
                mock.call("sql_to_table.py.tmpl", sql=mock.ANY, table="mv_master_stats"),
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master_postclick/data.csv",
                    schema=mock.ANY,
                    table="mv_master_postclick",
                ),
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master_diff/*.gz",
                    schema=mock.ANY,
                    table="mv_master_diff",
                ),
                mock.call("sql_to_table.py.tmpl", sql=mock.ANY, table="mv_master_diff"),
                mock.call(
                    "union_tables.py.tmpl",
                    source_table_1="mv_master_stats",
                    source_table_2="mv_master_postclick",
                    table="mv_master",
                ),
                mock.call(
                    "union_tables.py.tmpl",
                    source_table_1="mv_master",
                    source_table_2="mv_master_diff",
                    table="mv_master",
                ),
                mock.call("cache_table.py.tmpl", table="mv_master"),
            ]
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
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
                    {"date": datetime.date(2016, 7, 1), "ad_group_id": [1, 3, 4]},
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
                    {"date": datetime.date(2016, 7, 2), "ad_group_id": [1, 3, 4]},
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
                    {"date": datetime.date(2016, 7, 3), "ad_group_id": [1, 3, 4]},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                    UNLOAD ('
                        SELECT * FROM mv_master_diff
                        WHERE
                            (date BETWEEN \\'2016-07-01\\' AND \\'2016-07-03\\')
                            AND account_id = 1
                    ')
                    TO %(s3_url)s
                    DELIMITER AS %(delimiter)s
                    CREDENTIALS %(credentials)s
                    ESCAPE NULL AS '$NA$'
                    GZIP
                    MANIFEST;
                    """
                    ),
                    {
                        "s3_url": "s3://test_bucket/spark/asd/mv_master_diff/mv_master_diff-2016-07-01-2016-07-03-1",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = MasterSpark("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)
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
