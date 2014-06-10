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
            os.environ['HEALTH_CHECK'] = '1'

        super(CustomDiscoverRunner, self).__init__(
            *args,
            **kwargs
        )
