from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import models


class RuleTriggerHistoryQuerysetTest(TestCase):
    def test_update(self):
        magic_mixer.blend(models.RuleTriggerHistory)
        with self.assertRaises(AssertionError):
            models.RuleTriggerHistory.objects.filter().update()

    def test_delete(self):
        magic_mixer.blend(models.RuleTriggerHistory)
        with self.assertRaises(AssertionError):
            models.RuleTriggerHistory.objects.filter().delete()


class RuleHistoryQuerysetTest(TestCase):
    def test_update(self):
        magic_mixer.blend(models.RuleHistory)
        with self.assertRaises(AssertionError):
            models.RuleHistory.objects.filter().update()

    def test_delete(self):
        magic_mixer.blend(models.RuleHistory)
        with self.assertRaises(AssertionError):
            models.RuleHistory.objects.filter().delete()
