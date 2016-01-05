import datetime
import mock
from boto.s3.key import Key
from django.conf import settings
from django.test import TestCase

from reports.management.commands.update_publishers_b1 import Command
from utils import s3helpers


class CommandUpdatePublishersTest(TestCase):
    @mock.patch('reports.redshift.delete_publishers')
    @mock.patch('reports.redshift.update_publishers')
    @mock.patch.object(s3helpers.S3Helper, 'list')
    def test_handle(self, s3helper_list_mock, update_publishers_mock, delete_publishers_mock):
        s3helper_list_mock.return_value = [
            Key(name='publishers/2015-12-29-2015-12-31--1451296802070761934'),
            Key(name='publishers/2015-12-29-2015-12-31--1451282401204254907')]
        command = Command()
        command.handle(start_date='2015-12-29', end_date='2015-12-31')
        delete_publishers_mock.assert_called_with(datetime.date(2015, 12, 29), datetime.date(2015, 12, 31))
        update_publishers_mock.assert_called_with(
            's3://b1-eventlog-sync-test/publishers/2015-12-29-2015-12-31--1451296802070761934/part-00000',
            settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        s3helper_list_mock.assert_called_with('publishers/2015-12-29-2015-12-31')
