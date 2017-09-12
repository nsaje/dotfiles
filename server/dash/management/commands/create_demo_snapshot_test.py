import difflib
import mock

from django.utils.six import StringIO
from django.core.management import call_command
from django.db.models.signals import pre_save
from django.test import TransactionTestCase, override_settings

from dash.management.commands import create_demo_snapshot
from utils import request_signer, s3helpers


class CreateDemoSnapshotTest(TransactionTestCase):

    fixtures = ['test_models', 'demo_snapshot_data']

    def setUp(self):
        self.mock_s3 = {}

    def tearDown(self):
        pre_save.disconnect(create_demo_snapshot._pre_save_handler)

    def mock_put(self, key, contents):
        self.mock_s3[key] = contents

    @override_settings(
        BUILD_NUMBER=12345,
        BRANCH=None,
    )
    @mock.patch.object(create_demo_snapshot, '_get_snapshot_id')
    @mock.patch.object(s3helpers, 'S3Helper')
    @mock.patch.object(request_signer, 'urllib2_secure_open')
    def test_command(self, secure_open, s3_helper, mock_snapshot_id):
        mock_snapshot_id.return_value = '2016-01-01_1200'
        mock_s3_helper = mock.MagicMock()
        mock_s3_helper.put.side_effect = self.mock_put
        s3_helper.return_value = mock_s3_helper

        db_at_start = StringIO()
        call_command('dumpdata', '--indent=2', stdout=db_at_start)

        command = create_demo_snapshot.Command()
        command.handle()

        db_at_end = StringIO()
        call_command('dumpdata', '--indent=2', stdout=db_at_end)

        try:
            self.assertEqual(db_at_start.getvalue(), db_at_end.getvalue())
        except AssertionError as e:
            diff = '\n'.join(difflib.unified_diff(db_at_start.getvalue().splitlines(),
                                                  db_at_end.getvalue().splitlines()))
            e.args = ('Shouldn\'t modify database:\n%s' % diff,)
            raise

        # anonymization sanity check
        dump_data = self.mock_s3.get('2016-01-01_1200/dump.tar')
        self.assertIn('My demo account name', dump_data)
        self.assertNotIn('test account 1', dump_data)
        self.assertIn('My campaign 1', dump_data)
        self.assertNotIn('test campaign 1', dump_data)
        self.assertIn('My AG 1', dump_data)
        self.assertNotIn('test adgroup 1', dump_data)

        # build.txt and latest.txt sanity check
        build_txt = self.mock_s3.get('2016-01-01_1200/build.txt')
        self.assertEqual(build_txt, '12345')
        latest_txt = self.mock_s3.get('latest.txt')
        self.assertEqual(latest_txt, '2016-01-01_1200')

    @override_settings(
        BUILD_NUMBER=12345,
        BRANCH='master',
    )
    @mock.patch.object(create_demo_snapshot, '_get_snapshot_id')
    @mock.patch.object(s3helpers, 'S3Helper')
    @mock.patch.object(request_signer, 'urllib2_secure_open')
    def test_command_jenkins_build(self, secure_open, s3_helper, mock_snapshot_id):
        mock_snapshot_id.return_value = '2016-01-01_1200'
        mock_s3_helper = mock.MagicMock()
        mock_s3_helper.put.side_effect = self.mock_put
        s3_helper.return_value = mock_s3_helper

        db_at_start = StringIO()
        call_command('dumpdata', '--indent=2', stdout=db_at_start)

        command = create_demo_snapshot.Command()
        command.handle()

        db_at_end = StringIO()
        call_command('dumpdata', '--indent=2', stdout=db_at_end)

        try:
            self.assertEqual(db_at_start.getvalue(), db_at_end.getvalue())
        except AssertionError as e:
            diff = '\n'.join(difflib.unified_diff(db_at_start.getvalue().splitlines(),
                                                  db_at_end.getvalue().splitlines()))
            e.args = ('Shouldn\'t modify database:\n%s' % diff,)
            raise

        # anonymization sanity check
        dump_data = self.mock_s3.get('2016-01-01_1200/dump.tar')
        self.assertIn('My demo account name', dump_data)
        self.assertNotIn('test account 1', dump_data)
        self.assertIn('My campaign 1', dump_data)
        self.assertNotIn('test campaign 1', dump_data)
        self.assertIn('My AG 1', dump_data)
        self.assertNotIn('test adgroup 1', dump_data)

        # build.txt and latest.txt sanity check
        build_txt = self.mock_s3.get('2016-01-01_1200/build.txt')
        self.assertEqual(build_txt, 'master/12345')
        latest_txt = self.mock_s3.get('latest.txt')
        self.assertEqual(latest_txt, '2016-01-01_1200')
