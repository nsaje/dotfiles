import os
import unittest
from django.conf import settings

def integration_test(func):
    skip = os.environ.get('INTEGRATION_TESTS', '0') == '0'
    return unittest.skipIf(skip, 'Skipping integration tests.')(func)

def skipIfNoMigrations(func):
    skip = getattr(settings.MIGRATION_MODULES, 'dash', None) == "server.migrations_not_used_in_tests"
    return unittest.skipIf(skip, "We are running tests without migrations")(func)
