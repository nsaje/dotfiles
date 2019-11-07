from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import model


class RuleHistoryInstanceTest(TestCase):
    def test_save(self):
        history = magic_mixer.blend(model.RuleHistory)
        with self.assertRaises(AssertionError):
            history.save()

    def test_delete(self):
        history = magic_mixer.blend(model.RuleHistory)
        with self.assertRaises(AssertionError):
            history.delete()
