import datetime

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
import utils.test_helper

from .mv_adgroup_placement import MVAdGroupPlacement


class MVAdGroupPlacementTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_generate(self, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = MVAdGroupPlacement("asd", date_from, date_to, account_id=None)
        mv.generate()

        insert_into_mv_adgroup_placement_sql = mock.ANY

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_adgroup_placement WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)},
                ),
                mock.call(backtosql.SQLMatcher("SET statement_timeout TO 600000;")),
                mock.call(
                    insert_into_mv_adgroup_placement_sql,
                    {
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-04",
                        "date_from": "2016-07-01",
                        "date_to": "2016-07-03",
                    },
                ),
                mock.call(backtosql.SQLMatcher("SET statement_timeout TO 0;")),
            ]
        )


class MVAdGroupPlacementTestByAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_generate(self, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)
        account_id = 1

        mv = MVAdGroupPlacement("asd", date_from, date_to, account_id=account_id)
        mv.generate()

        insert_into_mv_adgroup_placement_sql = mock.ANY

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_adgroup_placement WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;"
                    ),
                    {
                        "date_from": datetime.date(2016, 7, 1),
                        "date_to": datetime.date(2016, 7, 3),
                        "account_id": account_id,
                    },
                ),
                mock.call(backtosql.SQLMatcher("SET statement_timeout TO 600000;")),
                mock.call(
                    insert_into_mv_adgroup_placement_sql,
                    {
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-04",
                        "date_from": "2016-07-01",
                        "date_to": "2016-07-03",
                        "account_id": account_id,
                        "ad_group_id": utils.test_helper.ListMatcher([1, 3, 4]),
                    },
                ),
                mock.call(backtosql.SQLMatcher("SET statement_timeout TO 0;")),
            ]
        )
