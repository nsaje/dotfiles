from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import model


class RuleQuerySetTestCase(TestCase):
    def test_exclude_archived(self):
        rules = magic_mixer.cycle(10).blend(model.Rule)
        archived_rules = magic_mixer.cycle(7).blend(model.Rule, archived=True)

        self.assertEqual(set(model.Rule.objects.exclude_archived()), set(rules))
        self.assertEqual(
            set(model.Rule.objects.exclude_archived(show_archived=True)), set(rules).union(set(archived_rules))
        )
