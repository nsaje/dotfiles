from django.test import TestCase

import dash.constants

from . import history


class ManagerTest(TestCase):
    def test_stack_trace(self):
        self.maxDiff = None
        obj = history.History.objects.create(changes={}, changes_text="", level=dash.constants.HistoryLevel.AD_GROUP)
        self.assertTrue(obj.stack_trace.strip().startswith("File"))
