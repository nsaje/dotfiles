import mock
from boto.s3.key import Key
from django.conf import settings
from django.test import TestCase

from reports.management.commands.update_publishers import Command
from utils import s3helpers


class CommandUpdatePublishersTest(TestCase):
    @mock.patch('reports.redshift.get_cursor')
    @mock.patch.object(s3helpers.S3Helper, 'list')
    def test_handle(self, s3helper_list_mock, get_cursor_mock):
        mock_cursor = mock.Mock()
        get_cursor_mock.return_value = mock_cursor
        s3helper_list_mock.return_value = [
            Key(name='publishers/2015-12-29-2015-12-31--1451296802070761934'),
            Key(name='publishers/2015-12-29-2015-12-31--1451282401204254907')]
        command = Command()
        command.handle(start_date='2015-12-29', end_date='2015-12-31')
        query = 'DELETE FROM b1_publishers_1 WHERE date >= %s AND date <= %s'
        params = ['2015-12-29', '2015-12-31']
        mock_cursor.execute.assert_any_call(query, params)
        query = "COPY b1_publishers_1 FROM '%s' CREDENTIALS 'aws_access_key_id=%s;aws_secret_access_key=%s' FORMAT CSV LZOP"
        params = ['s3://b1-eventlog-sync-test/publishers/2015-12-29-2015-12-31--1451296802070761934/part-00000.lzo',
                  settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY]
        mock_cursor.execute.assert_any_call(query, params)
        query = "COPY b1_publishers_1 FROM '%s' CREDENTIALS 'aws_access_key_id=%s;aws_secret_access_key=%s' FORMAT CSV LZOP"
        params = ['s3://b1-eventlog-sync-test/publishers/2015-12-29-2015-12-31--1451282401204254907/part-00000.lzo',
                  settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY]
        mock_cursor.execute.assert_called_with(query, params)
        s3helper_list_mock.assert_called_with('publishers/2015-12-29-2015-12-31')
