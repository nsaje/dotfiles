import unittest

import django.test.runner


class FilterSuiteMixin:
    def __init__(self, *args, **kwargs):
        self.filter_functions = []
        super().__init__(*args, **kwargs)

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels=test_labels, extra_tests=extra_tests, **kwargs)
        return self._filter_suite(suite, self.filter_functions)

    def _filter_suite(self, suite, fn_list):
        new_suite = unittest.TestSuite()
        if type(suite) == unittest.TestSuite:
            self._add_filtered_tests(suite, new_suite, fn_list)
            return new_suite

        assert isinstance(suite, django.test.runner.ParallelTestSuite)
        for subsuite in suite.subsuites:
            self._add_filtered_tests(subsuite, new_suite, fn_list)
        return self.parallel_test_suite(new_suite, self.parallel, self.failfast)

    def _add_filtered_tests(self, suite, new_suite, fn_list):
        for test in suite._tests:
            if not all(fn(test) for fn in fn_list):
                continue
            new_suite.addTest(test)
