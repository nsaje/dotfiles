import datetime

import mock
from django.test import TestCase

import backtosql

from .mv_touchpoint_conversions import MVTouchpointConversions


class MVTouchpointConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_generate(self, mock_transaction, mock_cursor):
        mv = MVTouchpointConversions("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_touchpointconversions WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)},
                ),
                mock.call(mock.ANY, {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)}),
            ]
        )

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_generate_account_id(self, mock_transaction, mock_cursor):
        mv = MVTouchpointConversions("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_touchpointconversions WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;"
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3), "account_id": 1},
                ),
                mock.call(
                    mock.ANY,
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3), "account_id": 1},
                ),
            ]
        )
