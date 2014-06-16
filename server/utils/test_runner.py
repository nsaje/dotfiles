from optparse import make_option
import os

from django.test import runner


class CustomDiscoverRunner(runner.DiscoverRunner):
    option_list = runner.DiscoverRunner.option_list + (
        make_option(
            '--health-check',
            action='store_true',
            dest='health_check',
            default=False,
            help='Run health check tests in production during test execution'
        ),
    )

    def __init__(self, health_check=None, *args, **kwargs):

        if health_check:
            self.health_check = True
            os.environ['HEALTH_CHECK'] = '1'
        else:
            self.health_check = False

        super(CustomDiscoverRunner, self).__init__(*args, **kwargs)

    def setup_databases(self, *args, **kwargs):
        if not self.health_check:
            return super(CustomDiscoverRunner, self).setup_databases(*args, **kwargs)

    def teardown_databases(self, *args, **kwargs):
        if not self.health_check:
            return super(CustomDiscoverRunner, self).teardown_databases(*args, **kwargs)
