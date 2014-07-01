import os
import unittest

from utils import test_decorators


class TestDecoratorsTestCase(unittest.TestCase):
    def deleteEnviron(self):
        if 'INTEGRATION_TESTS' in os.environ:
            del os.environ['INTEGRATION_TESTS']

        if 'UI_TESTS' in os.environ:
            del os.environ['UI_TESTS']

        if 'HEALTH_CHECK' in os.environ:
            del os.environ['HEALTH_CHECK']

    def setUp(self):
        self.original_integration_tests = os.environ.get('INTEGRATION_TESTS')
        self.original_ui_tests = os.environ.get('UI_TESTS')
        self.original_health_check = os.environ.get('HEALTH_CHECK')

        self.deleteEnviron()

    def tearDown(self):
        self.deleteEnviron()

        if self.original_integration_tests is not None:
            os.environ['INTEGRATION_TESTS'] = self.original_integration_tests

        if self.original_ui_tests is not None:
            os.environ['UI_TESTS'] = self.original_ui_tests

        if self.original_health_check is not None:
            os.environ['HEALTH_CHECK'] = self.original_health_check

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

    def test_skip_ui_test(self):
        class TestCase1(unittest.TestCase):
            @test_decorators.ui_test
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase1('test_something').run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

        @test_decorators.ui_test
        class TestCase2(unittest.TestCase):
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase2('test_something').run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

    def test_run_ui_test(self):
        os.environ['UI_TESTS'] = '1'

        class TestCase1(unittest.TestCase):
            @test_decorators.ui_test
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase1('test_something').run(result)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 1)

        @test_decorators.ui_test
        class TestCase2(unittest.TestCase):
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase2('test_something').run(result)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 1)

    def test_skip_health_check(self):
        class TestCase1(unittest.TestCase):
            @test_decorators.health_check
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase1('test_something').run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

        @test_decorators.health_check
        class TestCase2(unittest.TestCase):
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase2('test_something').run(result)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

    def test_run_health_check(self):
        os.environ['HEALTH_CHECK'] = '1'

        class TestCase1(unittest.TestCase):
            @test_decorators.health_check
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase1('test_something').run(result)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 1)

        @test_decorators.health_check
        class TestCase2(unittest.TestCase):
            def test_something(self):
                pass

        result = unittest.TestResult()
        TestCase2('test_something').run(result)
        self.assertEqual(len(result.skipped), 0)
        self.assertEqual(result.testsRun, 1)
