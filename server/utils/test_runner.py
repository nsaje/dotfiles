import os
import logging

from xmlrunner.extra.djangotestrunner import XMLTestRunner

from django.test import runner


class SplitTestsRunner(runner.DiscoverRunner):
    @classmethod
    def add_arguments(cls, parser):
        super(SplitTestsRunner, cls).add_arguments(parser)

        parser.add_argument(
            '--integration-tests',
            action='store_true',
            dest='integration_tests',
            default=False,
            help='Run integration tests.'
        )

    def __init__(self, integration_tests=None, *args, **kwargs):
        logging.disable(logging.CRITICAL)

        if integration_tests:
            os.environ['INTEGRATION_TESTS'] = '1'

        super(SplitTestsRunner, self).__init__(*args, **kwargs)


class CustomRunner(XMLTestRunner, SplitTestsRunner):
    pass
