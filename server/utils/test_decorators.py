import os
import unittest


def integration_test(func):
    skip = os.environ.get('INTEGRATION_TESTS', '0') == '0'
    return unittest.skipIf(skip, 'Skipping integration tests.')(func)


def ui_test(func):
    skip = os.environ.get('UI_TESTS', '0') == '0'
    return unittest.skipIf(skip, 'Skipping UI tests.')(func)


def health_check(func):
    skip = os.environ.get('HEALTH_CHECK', '0') == '0'
    return unittest.skipIf(skip, 'Skipping health check tests.')(func)
