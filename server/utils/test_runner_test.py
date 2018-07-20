import os
import unittest

from utils import test_runner


class TestRunnerTestCase(unittest.TestCase):
    def tearDown(self):
        if "INTEGRATION_TESTS" in os.environ:
            del os.environ["INTEGRATION_TESTS"]

    def test_init_none(self):
        test_runner.SplitTestsRunner()
        self.assertIs(os.environ.get("INTEGRATION_TESTS"), None)

    def test_init_integration(self):
        test_runner.SplitTestsRunner(integration_tests=True)
        self.assertEqual(os.environ.get("INTEGRATION_TESTS"), "1")
