import os
import logging
import time
import operator

import unittest

from xmlrunner.extra.djangotestrunner import XMLTestRunner

import django.test
from django.conf import settings
from django.core.management import call_command


class SplitTestsRunner(django.test.runner.DiscoverRunner):
    @classmethod
    def add_arguments(cls, parser):
        super(SplitTestsRunner, cls).add_arguments(parser)

        parser.set_defaults(pattern="*test*.py")

        parser.add_argument(
            "--integration-tests",
            action="store_true",
            dest="integration_tests",
            default=False,
            help="Run integration tests.",
        )

        parser.add_argument(
            "--redshift",
            action="store_true",
            dest="redshift_tests",
            default=False,
            help="Run tests for Amazon Redshift.",
        )

        parser.add_argument(
            "-n", "--test-name", dest="test_name", default=None, help="Filter out any tests not matching name."
        )

        parser.add_argument(
            "--skip-transaction-tests",
            dest="skip_transaction_tests",
            action="store_true",
            default=False,
            help="Filter out tests that use TransactionTestCase.",
        )

        parser.add_argument(
            "--timing", action="store_true", dest="timing", default=False, help="Measure tests execution time"
        )

    def __init__(
        self,
        integration_tests=None,
        redshift_tests=None,
        test_name=None,
        skip_transaction_tests=False,
        timing=False,
        *args,
        **kwargs
    ):
        logging.disable(logging.CRITICAL)

        if integration_tests:
            os.environ["INTEGRATION_TESTS"] = "1"

        self.redshift_tests = redshift_tests
        self.test_name = test_name
        self.skip_transaction_tests = skip_transaction_tests
        settings.RUN_REDSHIFT_UNITTESTS = redshift_tests

        self.test_timings = {}
        if timing:
            monkey_patch_test_case_for_timing(self.test_timings)

        super(SplitTestsRunner, self).__init__(*args, **kwargs)

    def setup_databases(self, **kwargs):
        from django.db import connections

        # HACK: stats connection is removed from connections because we need to handle
        # database creation and migrations separately

        stats_conn = None
        stats_meta_conn = None

        if self.redshift_tests:
            stats_conn = connections.databases.pop(settings.STATS_DB_NAME, None)
            stats_meta_conn = connections.databases.pop(settings.STATS_TEST_DB_NAME, None)

        old_configs = super(SplitTestsRunner, self).setup_databases(**kwargs)

        # put the connections back as they will be needed
        if stats_conn is not None:
            connections.databases[settings.STATS_DB_NAME] = stats_conn

        if stats_meta_conn is not None:
            connections.databases[settings.STATS_TEST_DB_NAME] = stats_meta_conn

        if self.redshift_tests:
            print("Running tests including Redshift database")
            db_name = settings.DATABASES[settings.STATS_DB_NAME]["NAME"]
            test_db_name = "test_" + db_name
            settings.DATABASES[settings.STATS_DB_NAME]["NAME"] = test_db_name
            call_command("redshift_createdb", settings.STATS_DB_NAME, settings.STATS_TEST_DB_NAME, verbosity=0)
            call_command("redshift_migrate", verbosity=0)
            print('Using "{}" Redshift database'.format(test_db_name))

        return old_configs

    def teardown_databases(self, old_config, **kwargs):
        super(SplitTestsRunner, self).teardown_databases(old_config, **kwargs)

        # drop redshift database
        if not self.keepdb and self.redshift_tests:
            call_command("redshift_dropdb", settings.STATS_DB_NAME, settings.STATS_TEST_DB_NAME, verbosity=0)

    def teardown_test_environment(self, **kwargs):
        super(SplitTestsRunner, self).teardown_test_environment(**kwargs)

        if self.test_timings:
            print_times(self.test_timings)

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        return self._filter_by_prefix(
            self._filter_transaction_tests(
                super(SplitTestsRunner, self).build_suite(test_labels=test_labels, extra_tests=extra_tests, **kwargs)
            )
        )

    def _filter_transaction_tests(self, test_suite):
        if not self.skip_transaction_tests:
            return test_suite

        def _filter_non_transaction_tests(test):
            # django.test.TestCase inherits from django.test.TransactionTestCase so
            # every test will be subclass of TransactionTestCase unless it uses
            # python unittest.TestCase base class
            return issubclass(type(test), django.test.TestCase) or not issubclass(
                type(test), django.test.TransactionTestCase
            )

        return self._filter_suite(test_suite, _filter_non_transaction_tests)

    def _filter_by_prefix(self, test_suite):
        prefix = self.test_name
        if prefix is None:
            return test_suite

        def _filter_tests_wo_prefix(test):
            # the next string is <test_name> (<module path>)
            return str(test).split()[0] == prefix

        return self._filter_suite(test_suite, _filter_tests_wo_prefix)

    def _filter_suite(self, suite, fn):
        new_suite = unittest.TestSuite()
        if type(suite) == unittest.TestSuite:
            self._add_filtered_tests(suite, new_suite, fn)
            return new_suite

        assert type(suite) == django.test.runner.ParallelTestSuite
        for subsuite in suite.subsuites:
            self._add_filtered_tests(subsuite, new_suite, fn)
        return self.parallel_test_suite(new_suite, self.parallel, self.failfast)

    def _add_filtered_tests(self, suite, new_suite, fn):
        for test in suite._tests:
            if not fn(test):
                continue
            new_suite.addTest(test)


class CustomRunner(XMLTestRunner, SplitTestsRunner):
    pass


def monkey_patch_test_case_for_timing(test_timings):

    __call__ = unittest.TestCase.__call__

    def measure_n_run(self, *args, **kwargs):
        start = time.time()
        __call__(self, *args, **kwargs)
        test_timings[str(self)] = (time.time() - start) * 1000

    unittest.TestCase.__call__ = measure_n_run


def print_times(test_timings, nr_top_slow=10):
    by_time = sorted(iter(list(test_timings.items())), key=operator.itemgetter(1), reverse=True)[:nr_top_slow]
    print("\n{} slowest tests:".format(nr_top_slow))
    for func_name, timing in by_time:
        if timing < 1000.0:
            color = "\033[92m"
        elif timing < 2000.0:
            color = "\033[93m"
        else:
            color = "\033[91m"
        print("{color}{t:.2f}ms {f}".format(color=color, f=func_name, t=timing))
