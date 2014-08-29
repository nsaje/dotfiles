import os
import logging
import time
from optparse import make_option

from xmlrunner.extra.djangotestrunner import XMLTestRunner

from django.test import runner
from django.conf import settings


class SplitTestsRunner(runner.DiscoverRunner):
    option_list = runner.DiscoverRunner.option_list + (
        make_option(
            '--integration-tests',
            action='store_true',
            dest='integration_tests',
            default=False,
            help='Run integration tests.'
        ),
        make_option(
            '--ui-tests',
            action='store_true',
            dest='ui_tests',
            default=False,
            help='Run UI tests.'
        ),
        make_option(
            '--health-check',
            action='store_true',
            dest='health_check',
            default=False,
            help='Run health check tests in production during test execution.'
        ),
    )

    def __init__(self, integration_tests=None, ui_tests=None, health_check=None, *args, **kwargs):
        self.skip_db = False

        logging.disable(logging.CRITICAL)

        if integration_tests:
            os.environ['INTEGRATION_TESTS'] = '1'

        if ui_tests:
            os.environ['UI_TESTS'] = '1'

        if health_check:
            self.skip_db = True
            os.environ['HEALTH_CHECK'] = '1'

        super(SplitTestsRunner, self).__init__(*args, **kwargs)

    def setup_databases(self, **kwargs):
        if not self.skip_db:
            return super(SplitTestsRunner, self).setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        if not self.skip_db:
            return super(SplitTestsRunner, self).teardown_databases(old_config, **kwargs)


class CustomRunner(XMLTestRunner, SplitTestsRunner):
    pass









