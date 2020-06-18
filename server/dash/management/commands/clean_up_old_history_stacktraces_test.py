import datetime

from django.test import TestCase

import core.features.history.models
from dash.management.commands import clean_up_old_history_stacktraces
from utils.magic_mixer import magic_mixer


class CleanUpOldHistoryStackTracesTest(TestCase):
    def test_delete(self):
        magic_mixer.blend(core.features.history.models.HistoryStacktrace, value="TEST")

        old_trace = magic_mixer.blend(core.features.history.models.HistoryStacktrace, value="TEST")
        old_trace.created_dt = datetime.datetime(2020, 4, 20)
        old_trace.save()
        self.assertEqual(len(core.features.history.models.HistoryStacktrace.objects.filter(value="TEST").all()), 2)
        clean_up_old_history_stacktraces.Command._delete_old_data()
        self.assertEqual(len(core.features.history.models.HistoryStacktrace.objects.filter(value="TEST").all()), 1)
