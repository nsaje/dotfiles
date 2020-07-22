from dataclasses import dataclass

import django.test.runner
from django.conf import settings
from xmlrunner.extra.djangotestrunner import XMLTestRunner

from utils import metrics_compat
from utils import zlogging
from utils.test_runner_mixin import FilterSuiteMixin

from .test_case import APTTestCase

logger = zlogging.getLogger(__name__)


@dataclass
class XmlResultSetDescription:
    attr_name: str
    metric: str
    includesStackTrace: bool


XML_RESULT_STRUCTURE = [
    XmlResultSetDescription("successes", 0, False),
    XmlResultSetDescription("failures", 1, True),
    XmlResultSetDescription("skipped", 2, True),
    XmlResultSetDescription("expectedFailures", 3, True),
    XmlResultSetDescription("unexpectedSuccesses", 4, True),
]


def _init_worker(*args, **kwargs):
    """
    Django's ParallelTestSuite switches databases in this function: https://github.com/django/django/blob/80f92177eb2a175579f4a6907ef5a358863bddca/django/test/runner.py#L304
    This step has to be skipped since we're not setting up test databases as a part of APT tests.
    """
    pass


class APTParallelTestSuite(django.test.runner.ParallelTestSuite):
    init_worker = _init_worker


class APTTestRunner(FilterSuiteMixin, XMLTestRunner, django.test.runner.DiscoverRunner):
    parallel_test_suite = APTParallelTestSuite

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--emit-metrics", action="store_true", dest="emit_metrics", default=False, help="Emit metrics"
        )

    def __init__(self, *args, emit_metrics=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.emit_metrics = emit_metrics
        self.filter_functions.append(self._get_filter_apt_fn())

    def run_suite(self, *args, **kwargs):
        result = super().run_suite(*args, **kwargs)
        if self.emit_metrics:
            self._emit_metrics(result)
        return result

    def _emit_metrics(self, xml_result):
        logger.info("Emitting metrics...")
        for description in XML_RESULT_STRUCTURE:
            for test in getattr(xml_result, description.attr_name):
                if description.includesStackTrace:
                    test = test[0]
                test_case, test_method = test.test_id.rsplit(".", 1)
                metrics_compat.timing("apt_runner_suite_timing", test.elapsed_time, suite=test_case, test=test_method)
                metrics_compat.gauge("apt_runner_suite_status", description.metric, suite=test_case, test=test_method)

    def run_tests(self, *args, **kwargs):
        assert settings.APT_MODE, 'Not running in "apt" environment. Set CONF_ENV=apt to use it.'
        return super().run_tests(*args, **kwargs)

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
