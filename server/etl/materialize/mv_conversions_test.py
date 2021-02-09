import datetime

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
from dash import constants
from utils import test_helper

from .mv_conversions import MVConversions
from .mv_master import MasterView


class MVConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = MVConversions("asd", date_from, date_to, account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_conversions WHERE date=%(date)s"),
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
                    {"date": datetime.date(2016, 7, 1)},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                COPY mv_conversions
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                BLANKSASNULL EMPTYASNULL
                CREDENTIALS %(credentials)s
                MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_conversions/2016/07/01/mv_conversions_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_conversions WHERE date=%(date)s"),
                    {"date": datetime.date(2016, 7, 2)},
                ),
                mock.call(mock.ANY, {"date": datetime.date(2016, 7, 2)}),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_conversions/2016/07/02/mv_conversions_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_conversions WHERE date=%(date)s"),
                    {"date": datetime.date(2016, 7, 3)},
                ),
                mock.call(mock.ANY, {"date": datetime.date(2016, 7, 3)}),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_conversions/2016/07/03/mv_conversions_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_generate_rows(self):
        date = datetime.date(2016, 7, 1)

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
                    1,
                    "bla.com",
                    constants.DeviceType.UNKNOWN,
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
                ),
                ('{"einpix": 2, "preuba": 1}', "gaapi"),
            ),
            (
                (1, 3),
                (
                    date,
                    1,
                    1,
                    1,
                    3,
                    3,
                    3,
                    "nesto.com",
                    constants.DeviceType.UNKNOWN,
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
                ),
                ('{"poop": 111}', "omniture"),
            ),
            (
                (1, 3),
                (
                    date,
                    2,
                    1,
                    1,
                    3,
                    3,
                    3,
                    "nesto2.com",
                    constants.DeviceType.UNKNOWN,
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
                ),
                ("{}", None),
            ),
            (
                (1, 3),
                (
                    date,
                    3,
                    1,
                    1,
                    3,
                    3,
                    3,
                    "nesto3.com",
                    constants.DeviceType.UNKNOWN,
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
                ),
                ("", None),
            ),
            (
                (1, 3),
                (
                    date,
                    4,
                    1,
                    1,
                    3,
                    3,
                    3,
                    "nesto4.com",
                    constants.DeviceType.UNKNOWN,
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
                ),
                (None, "gaapi"),
            ),
            (
                (3, 4),
                (
                    date,
                    3,
                    1,
                    2,
                    2,
                    2,
                    4,
                    "trol",
                    constants.DeviceType.UNKNOWN,
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
                ),
                ('{"poop": 23}', "ga_mail"),
            ),
        ]

        with mock.patch.object(MasterView, "get_postclickstats", return_value=postclickstats_return_value):

            mv = MVConversions("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
            rows = list(mv.generate_rows(mock_cursor, date))

            self.assertCountEqual(
                rows,
                [
                    (date, 3, 1, 1, 1, 1, 1, "bla.com", "ga__einpix", 2),
                    (date, 3, 1, 1, 1, 1, 1, "bla.com", "ga__preuba", 1),
                    (date, 1, 1, 1, 3, 3, 3, "nesto.com", "omniture__poop", 111),
                    (date, 3, 1, 2, 2, 2, 4, "trol", "ga__poop", 23),
                ],
            )


class MVConversionsTestAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = MVConversions("asd", date_from, date_to, account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_conversions WHERE date=%(date)s AND account_id=%(account_id)s"
                    ),
                    {"date": datetime.date(2016, 7, 1), "account_id": 1},
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
                COPY mv_conversions
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                BLANKSASNULL EMPTYASNULL
                CREDENTIALS %(credentials)s
                MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_conversions/2016/07/01/mv_conversions_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_conversions WHERE date=%(date)s AND account_id=%(account_id)s"
                    ),
                    {"date": datetime.date(2016, 7, 2), "account_id": 1},
                ),
                mock.call(
                    mock.ANY, {"date": datetime.date(2016, 7, 2), "ad_group_id": test_helper.ListMatcher([1, 3, 4])}
                ),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_conversions/2016/07/02/mv_conversions_asd.csv",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_conversions WHERE date=%(date)s AND account_id=%(account_id)s"
                    ),
                    {"date": datetime.date(2016, 7, 3), "account_id": 1},
                ),
                mock.call(
                    mock.ANY, {"date": datetime.date(2016, 7, 3), "ad_group_id": test_helper.ListMatcher([1, 3, 4])}
                ),
                mock.call(
                    mock.ANY,
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mv_conversions/2016/07/03/mv_conversions_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
