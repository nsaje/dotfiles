from django.test import TestCase

import dash.constants

from . import model


class ManagerTest(TestCase):
    def test_stack_trace(self):
        obj = model.History.objects.create(changes={}, changes_text="", level=dash.constants.HistoryLevel.AD_GROUP)
        self.assertTrue(obj.stacktrace.value.strip().startswith("File"))
