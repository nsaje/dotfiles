import datetime

import mock
from django.test import TestCase

import backtosql
from utils import test_helper

from .mv_helpers_normalized_stats import MVHelpersNormalizedStats


@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
class MVHNormalizedStatsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    def test_generate(self, mock_transaction, mock_cursor):
        mv = MVHelpersNormalizedStats("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()
        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(
                    mock.ANY,
                    {
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-04",
                        "date_from": "2016-07-01",
                        "date_to": "2016-07-03",
                    },
                ),
            ]
        )

    def test_generate_account_id(self, mock_transaction, mock_cursor):
        mv = MVHelpersNormalizedStats("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()
        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(
                    mock.ANY,
                    {
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-04",
                        "date_from": "2016-07-01",
                        "date_to": "2016-07-03",
                        "ad_group_id": test_helper.ListMatcher([1, 3, 4]),
                    },
                ),
            ]
        )
