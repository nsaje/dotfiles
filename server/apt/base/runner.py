import django.test.runner
from django.conf import settings
from xmlrunner.extra.djangotestrunner import XMLTestRunner

from utils.test_runner_mixin import FilterSuiteMixin

from .test_case import APTTestCase


class APTTestRunner(FilterSuiteMixin, XMLTestRunner, django.test.runner.DiscoverRunner):
    def run_tests(self, *args, **kwargs):
        assert settings.APT_MODE, 'Not running in "apt" environment. Set CONF_ENV=apt to use it.'

        super().run_tests(*args, **kwargs)
        self.filter_functions.append(self._get_filter_apt_fn())

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        # set to location as default to narrow the search
        test_labels = test_labels or [settings.APT_TESTS_PATH]
        suite = super().build_suite(test_labels=test_labels, **kwargs)
        return suite

    def _get_filter_apt_fn(self):
        def _is_apt_test(test):
            return isinstance(test, APTTestCase)

        return _is_apt_test

    def setup_databases(self, *args, **kwargs):
        # NOTE: db setup skipped intentionally - apt tests are supposed to run on production
        pass

    def teardown_databases(self, *args, **kwargs):
        # NOTE: no need to teardown - setup was skipped
        pass
