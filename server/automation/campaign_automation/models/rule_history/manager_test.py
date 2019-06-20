from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import model


class RuleHistoryManagerTest(TestCase):
    def test_update(self):
        magic_mixer.blend(model.RuleHistory)
        with self.assertRaises(AssertionError):
            model.RuleHistory.objects.update()

    def test_delete(self):
        magic_mixer.blend(model.RuleHistory)
        with self.assertRaises(AssertionError):
            model.RuleHistory.objects.delete()
