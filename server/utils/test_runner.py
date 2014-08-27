import os
import logging
import time
from optparse import make_option

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




def connect_to_librato():
    import librato
    try:

        librato_user = os.environ['LIBRATO_USER']
        librato_token = os.environ['LIBRATO_TOKEN']
    except KeyError:
        raise Exception('librato user or token not set in enviroment settings ' +
        'LIBRATO_USER and LIBRATO_TOKEN despite set COVERAGE_ENABLED enviroment variable')

    return librato.connect(librato_user, librato_token)

def post_tests_metrics_to_librato(librato_api, coverage_percentage, num_of_tests, tests_elapsed_time):
    queue = librato_api.new_queue()
    queue.add('tests.{0}.coverage_percentage'.format(settings.PROJECT_NAME), coverage_percentage ,type='gauge', source='circle-ci')
    queue.add('tests.{0}.num_of_tests'.format(settings.PROJECT_NAME), num_of_tests ,type='gauge', source='circle-ci')
    queue.add('tests.{0}.tests_elapsed_time'.format(settings.PROJECT_NAME), tests_elapsed_time ,type='gauge', source='circle-ci')
    queue.submit()

    if 'CIRCLECI' not in os.environ:
        return

    librato_api.post_annotation('circle_ci.{0}'.format(settings.PROJECT_NAME),
        title='build triggered by {0}'.os.environ.get('CIRCLE_USERNAME'), 
        source='circle-ci', 
        description='https://circleci.com/gh/{0}/{1}/{2}'.format(
                os.environ.get('CIRCLE_PROJECT_USERNAME'),
                os.environ.get('CIRCLE_PROJECT_REPONAME'),
                os.environ.get('CIRCLE_BUILD_NUM'),
            )
        )



class CoverageRunner(runner.DiscoverRunner):

    def build_suite(self, *args, **kwargs):
        suite = super(CoverageRunner, self).build_suite(*args, **kwargs)
        self._num_of_tests = suite.countTestCases()
        return suite

    def run_tests(self, *args, **kwargs):
        if not settings.COVERAGE_ENABLED:
            return super(CoverageRunner, self).run_tests(*args, **kwargs)

        import coverage
        librato_api = connect_to_librato()
        coverage = coverage.coverage()

        # start measuring time
        t0 = time.time()
        # start measuring coverage
        coverage.start()

        result = super(CoverageRunner, self).run_tests(*args, **kwargs)

        coverage.stop()
        coverage.save()

        post_tests_metrics_to_librato( librato_api, 
            coverage_percentage = coverage.report(file=open(os.devnull,'w')),
            num_of_tests = self._num_of_tests, 
            tests_elapsed_time = time.time() - t0
            )

        return result

class CustomRunner(CoverageRunner, SplitTestsRunner):
    pass









