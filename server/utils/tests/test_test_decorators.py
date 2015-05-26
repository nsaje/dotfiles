import os
import unittest

from utils import test_decorators


class TestDecoratorsTestCase(unittest.TestCase):
    def deleteEnviron(self):
        if 'INTEGRATION_TESTS' in os.environ:
            del os.environ['INTEGRATION_TESTS']

    def setUp(self):
        self.original_integration_tests = os.environ.get('INTEGRATION_TESTS')

        self.deleteEnviron()

    def tearDown(self):
        self.deleteEnviron()

        if self.original_integration_tests is not None:
            os.environ['INTEGRATION_TESTS'] = self.original_integration_tests

    def test_skip_integration_test(self):
        class TestCase1(unittest.TestCase):
            @test_decorators.integration_test
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase1('test_something').run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

        @test_decorators.integration_test
        class TestCase2(unittest.TestCase):
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase2('test_something').run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

    def test_run_integration_test(self):
        os.environ['INTEGRATION_TESTS'] = '1'

        class TestCase1(unittest.TestCase):
            @test_decorators.integration_test
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase1('test_something').run(result)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 1)

        @test_decorators.integration_test
        class TestCase2(unittest.TestCase):
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase2('test_something').run(result)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 1)
