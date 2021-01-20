
# MigrationTest is based on https://github.com/plumdog/django_migration_testcase
"""
License applying to this specific file:
The MIT License (MIT)

Copyright (c) 2015 Michael Nelson, Andrew Plummer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import unittest

from django.core.management import CommandError
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TransactionTestCase


class MigrationTest(TransactionTestCase):

    __abstract__ = True

    def setUp(self):
        super(MigrationTest, self).setUp()
        try:
            call_command("migrate", self.app_name, self.before, no_initial_data=True, verbosity=0)
        except CommandError as e:
            if "does not have migrations (you cannot selectively sync unmigrated apps)" in str(e):
                raise unittest.SkipTest("Skip migration tests when migrations are disabled")

    def tearDown(self):
        super(MigrationTest, self).tearDown()
        call_command("migrate", self.app_name, no_initial_data=True, verbosity=0)

    def _get_apps_for_migration(self, app_label, migration_name):
        loader = MigrationLoader(connection)
        state = loader.project_state((app_label, migration_name))
        return state.apps

    def get_model_before(self, model_name):
        return self._get_apps_for_migration(self.app_name, self.before).get_model(self.app_name, model_name)

    def get_model_after(self, model_name):
        return self._get_apps_for_migration(self.app_name, self.after).get_model(self.app_name, model_name)

    def run_migration(self):
        call_command("migrate", self.app_name, self.after, no_initial_data=True, verbosity=0)
