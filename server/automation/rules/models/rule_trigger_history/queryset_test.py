from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import model


class RuleTriggerHistoryQuerysetTest(TestCase):
    def test_update(self):
        magic_mixer.blend(model.RuleTriggerHistory)
        with self.assertRaises(AssertionError):
            model.RuleTriggerHistory.objects.filter().update()

    def test_delete(self):
        magic_mixer.blend(model.RuleTriggerHistory)
        with self.assertRaises(AssertionError):
            model.RuleTriggerHistory.objects.filter().delete()
