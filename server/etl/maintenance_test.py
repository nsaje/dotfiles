import datetime

import mock
from django.test import TestCase

import backtosql
import etl.maintenance
from etl.helpers import get_local_date_query


class TestCheckExistingDataByHours(TestCase):
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    def test_correct_sql_call(self, mock_cursor):
        etl.maintenance.check_existing_data_by_hours(datetime.date(2020, 4, 5))
        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        f"select count(distinct hour) from stats where {get_local_date_query(datetime.date(2020, 4, 5))}"
                    )
                )
            ]
        )
