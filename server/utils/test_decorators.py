import os
import unittest


def integration_test(func):
    skip = os.environ.get('INTEGRATION_TESTS', '0') == '0'
    return unittest.skipIf(skip, 'Skipping integration tests.')(func)
