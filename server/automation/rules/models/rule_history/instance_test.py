from django.test import TestCase

from utils.magic_mixer import magic_mixer

from ... import constants
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

    def test_failure_reason(self):
        history = magic_mixer.blend(model.RuleHistory, status=constants.ApplyStatus.FAILURE)
        for failure_reason in constants.RuleFailureReason.get_all():
            history.failure_reason = failure_reason
            if failure_reason == constants.RuleFailureReason.UNEXPECTED_ERROR:
                self.assertEqual(
                    "Automation rule failed to be applied because of an unforeseen error.",
                    history.get_formatted_changes(),
                )
            else:
                self.assertNotEqual("N/A", history.get_formatted_changes())
