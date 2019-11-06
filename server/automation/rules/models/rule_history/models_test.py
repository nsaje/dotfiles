from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import models


class RuleTriggerHistoryModelTest(TestCase):
    def test_save(self):
        history = magic_mixer.blend(models.RuleTriggerHistory)
        with self.assertRaises(AssertionError):
            history.save()

    def test_delete(self):
        history = magic_mixer.blend(models.RuleTriggerHistory)
        with self.assertRaises(AssertionError):
            history.delete()


class RuleHistoryModelTest(TestCase):
    def test_save(self):
        history = magic_mixer.blend(models.RuleHistory)
        with self.assertRaises(AssertionError):
            history.save()

    def test_delete(self):
        history = magic_mixer.blend(models.RuleHistory)
        with self.assertRaises(AssertionError):
            history.delete()
