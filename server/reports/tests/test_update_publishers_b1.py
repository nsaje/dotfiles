import datetime
import mock
from django.test import TestCase

from reports.management.commands.update_publishers_b1 import Command


class CommandUpdatePublishersTest(TestCase):

    @mock.patch('reports.refresh.refresh_b1_publishers_data')
    def test_handle(self, mock_refresh_b1_publishers_data):

        command = Command()
        command.handle(start_date='2015-12-29', end_date='2015-12-31')
        calls = [
            mock.call(datetime.date(2015, 12, 29)),
            mock.call(datetime.date(2015, 12, 30)),
            mock.call(datetime.date(2015, 12, 31)),
        ]

        mock_refresh_b1_publishers_data.assert_has_calls(calls)
