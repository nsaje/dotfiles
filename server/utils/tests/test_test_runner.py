import os
import unittest

import mock

from utils import test_runner


class TestRunnerTestCase(unittest.TestCase):
    def tearDown(self):
        if 'INTEGRATION_TESTS' in os.environ:
            del os.environ['INTEGRATION_TESTS']

        if 'UI_TESTS' in os.environ:
            del os.environ['UI_TESTS']

        if 'HEALTH_CHECK' in os.environ:
            del os.environ['HEALTH_CHECK']

    def test_init_none(self):
        cd = test_runner.SplitTestsRunner()
        self.assertFalse(cd.skip_db)
        self.assertIs(os.environ.get('INTEGRATION_TESTS'), None)
        self.assertIs(os.environ.get('UI_TESTS'), None)
        self.assertIs(os.environ.get('HEALTH_CHECK'), None)

    def test_init_integration(self):
        cd = test_runner.SplitTestsRunner(integration_tests=True)
        self.assertFalse(cd.skip_db)
        self.assertEqual(os.environ.get('INTEGRATION_TESTS'), '1')
        self.assertIs(os.environ.get('UI_TESTS'), None)
        self.assertIs(os.environ.get('HEALTH_CHECK'), None)

    def test_init_ui(self):
        cd = test_runner.SplitTestsRunner(ui_tests=True)
        self.assertFalse(cd.skip_db)
        self.assertIs(os.environ.get('INTEGRATION_TESTS'), None)
        self.assertEqual(os.environ.get('UI_TESTS'), '1')
        self.assertIs(os.environ.get('HEALTH_CHECK'), None)

    def test_init_health_check(self):
        cd = test_runner.SplitTestsRunner(health_check=True)
        self.assertTrue(cd.skip_db)
        self.assertIs(os.environ.get('INTEGRATION_TESTS'), None)
        self.assertIs(os.environ.get('UI_TESTS'), None)
        self.assertEqual(os.environ.get('HEALTH_CHECK'), '1')

    def test_init_all(self):
        cd = test_runner.SplitTestsRunner(
            integration_tests=True, ui_tests=True, health_check=True)
        self.assertTrue(cd.skip_db)
        self.assertEqual(os.environ.get('INTEGRATION_TESTS'), '1')
        self.assertEqual(os.environ.get('UI_TESTS'), '1')
        self.assertEqual(os.environ.get('HEALTH_CHECK'), '1')

    @mock.patch('utils.test_runner.runner.DiscoverRunner.setup_databases')
    def test_setup_databases(self, setup_databases_mock):
        cd = test_runner.SplitTestsRunner()
        cd.setup_databases()

        self.assertTrue(setup_databases_mock.called)

    @mock.patch('utils.test_runner.runner.DiscoverRunner.setup_databases')
    def test_skip_setup_databases(self, setup_databases_mock):
        cd = test_runner.SplitTestsRunner()
        cd.skip_db = True
        cd.setup_databases()

        self.assertFalse(setup_databases_mock.called)

    @mock.patch('utils.test_runner.runner.DiscoverRunner.teardown_databases')
    def test_teardown_databases(self, teardown_databases_mock):
        cd = test_runner.SplitTestsRunner()
        cd.teardown_databases(None)

        self.assertTrue(teardown_databases_mock.called)

    @mock.patch('utils.test_runner.runner.DiscoverRunner.teardown_databases')
    def test_skip_teardown_databases(self, teardown_databases_mock):
        cd = test_runner.SplitTestsRunner()
        cd.skip_db = True
        cd.teardown_databases(None)

        self.assertFalse(teardown_databases_mock.called)
