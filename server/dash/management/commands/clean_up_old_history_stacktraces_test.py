import datetime

import mock
from django.test import TestCase

from dash.management.commands import clean_up_old_history_stacktraces


class CleanUpOldHistoryStackTracesTest(TestCase):
    @mock.patch("utils.dates_helper.utc_today", mock.MagicMock(return_value=datetime.datetime(2020, 9, 17).date()))
    @mock.patch("django.db.connection.cursor")
    def test_generate(self, mock_cursor):
        clean_up_old_history_stacktraces.Command().handle()
        mock_cursor().execute.assert_has_calls(
            [
                mock.call(
                    """
            CREATE TABLE IF NOT EXISTS
                dash_historystacktrace_20200918
            PARTITION OF
                dash_historystacktrace
            FOR VALUES FROM ('2020-09-18') TO ('2020-09-19');
        """
                ),
                mock.call(
                    """
            CREATE TABLE IF NOT EXISTS
                dash_historystacktrace_20200919
            PARTITION OF
                dash_historystacktrace
            FOR VALUES FROM ('2020-09-19') TO ('2020-09-20');
        """
                ),
                # mock.call("ALTER TABLE dash_historystacktrace DETACH PARTITION dash_historystacktrace_20200902;"),
                # mock.call("DROP TABLE IF EXISTS dash_historystacktrace_20200902;"),
                # mock.call("ALTER TABLE dash_historystacktrace DETACH PARTITION dash_historystacktrace_20200901;"),
                # mock.call("DROP TABLE IF EXISTS dash_historystacktrace_20200901;"),
            ]
        )
