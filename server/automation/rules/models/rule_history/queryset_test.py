from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import model


class RuleHistoryQuerysetTest(TestCase):
    def test_update(self):
        magic_mixer.blend(model.RuleHistory)
        with self.assertRaises(AssertionError):
            model.RuleHistory.objects.filter().update()

    def test_delete(self):
        magic_mixer.blend(model.RuleHistory)
        with self.assertRaises(AssertionError):
            model.RuleHistory.objects.filter().delete()

    def test_exclude_without_changes(self):
        magic_mixer.cycle(5).blend(model.RuleHistory, changes={})

        rule_history_with_changes = model.RuleHistory.objects.exclude_without_changes()
        self.assertEqual(len(rule_history_with_changes), 0)
