from django.test import TestCase

from redshiftapi import models
from redshiftapi import constants

class RSContentAdStatsTest(TestCase):
    def test_columns(self):
        columns = models.RSContentAdStats.get_columns()
        self.assertEquals(len(columns), 26)

        # TODO assert this print matches expected
        print [(x.group, x.alias, x.template_name) for x in models.RSContentAdStats.get_columns()]
        columns = models.RSContentAdStats.select_columns(group=constants.ColumnGroup.BREAKDOWN)
        self.assertEquals(len(columns), 6)