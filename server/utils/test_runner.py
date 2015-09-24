import os
import logging

from xmlrunner.extra.djangotestrunner import XMLTestRunner

from django.test import runner
from django.conf import settings
from django.core.management import call_command


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

        parser.add_argument(
            '--redshift',
            action='store_true',
            dest='redshift_tests',
            default=False,
            help='Run tests for Amazon Redshift.'
        )

    def __init__(self, integration_tests=None, redshift_tests=None, *args, **kwargs):
        logging.disable(logging.CRITICAL)

        if integration_tests:
            os.environ['INTEGRATION_TESTS'] = '1'

        self.redshift_tests = redshift_tests
        settings.RUN_REDSHIFT_UNITTESTS = redshift_tests

        super(SplitTestsRunner, self).__init__(*args, **kwargs)

    def setup_databases(self, **kwargs):
        from django.db import connections

        # HACK: stats connection is removed from connections because we need to handle
        # database creation and migrations separately
        stats_conn = connections.databases.pop(settings.STATS_DB_NAME)
        stats_meta_conn = connections.databases.pop(settings.STATS_E2E_DB_NAME)
        old_configs = super(SplitTestsRunner, self).setup_databases(**kwargs)

        # put the connection back as it will be needed
        if stats_conn:
            connections.databases[settings.STATS_DB_NAME] = stats_conn

        if stats_meta_conn:
            connections.databases[settings.STATS_E2E_DB_NAME] = stats_meta_conn

        if self.redshift_tests:
            print 'Running tests including Redshift database'
            db_name = settings.DATABASES[settings.STATS_DB_NAME]['NAME']
            test_db_name = 'test_' + db_name
            settings.DATABASES[settings.STATS_DB_NAME]['NAME'] = test_db_name
            call_command('redshift_createdb',
                         settings.STATS_DB_NAME,
                         settings.STATS_E2E_DB_NAME,
                         verbosity=0)
            call_command('redshift_migrate', verbosity=0)
            print 'Using "{}" Redshift database'.format(test_db_name)

        return old_configs

    def teardown_databases(self, old_config, **kwargs):
        super(SplitTestsRunner, self).teardown_databases(old_config, **kwargs)

        # drop redshift database
        if not self.keepdb and self.redshift_tests:
            call_command('redshift_dropdb',
                         settings.STATS_DB_NAME,
                         settings.STATS_E2E_DB_NAME,
                         verbosity=0)


class CustomRunner(XMLTestRunner, SplitTestsRunner):
    pass
