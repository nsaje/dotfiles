from django.test import TestCase

from . import history_mixin


class MockHistoryMixin(history_mixin.HistoryMixin):
    def __init__(self, id=None, *args, **kwargs):
        self.id = id
        super().__init__(*args, **kwargs)

    def get_history_changes_text(self, changes):
        if changes:
            return str(changes)


class HistoryMixinTest(TestCase):
    def test_construct_changes_new(self):
        obj = MockHistoryMixin(id=None)
        changes, changes_text = obj.construct_changes("Created settings.", "Source X.", {"a": "b"})
        self.assertEqual(changes, {"a": "b"})
        self.assertEqual(changes_text, "Created settings. Source X. {'a': 'b'}")

    def test_construct_changes_existing_obj(self):
        obj = MockHistoryMixin(id=1)
        changes, changes_text = obj.construct_changes("Created settings.", "Source X.", {"a": "b"})
        self.assertEqual(changes, {"a": "b"})
        self.assertEqual(changes_text, "Source X. {'a': 'b'}")

    def test_construct_changes_no_changes(self):
        obj = MockHistoryMixin(id=1)
        changes, changes_text = obj.construct_changes("Created settings.", "Source X.", {})
        self.assertEqual(changes, {})
        self.assertEqual(changes_text, "")
