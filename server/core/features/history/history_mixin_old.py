# -*- coding: utf-8 -*-
from collections import OrderedDict


class HistoryMixinOld(object):
    _snapshot_on_setattr = False

    # In some cases we want to disable snapshots because they can be heavy.
    # One case where this happens is when we snapshot a model with related models -
    # in that case snapshot will be created and data will be fetched before any
    # `select_related` is applied. Use only when you are sure no data will be modified.
    SNAPSHOT_HISTORY = True

    def __init__(self):
        self.snapshotted_state = None
        # signifies whether this particular history object is created anew
        # or does it have a previous object from which it potentially
        # differs in some settings
        self.post_init_newly_created = self.id is None
        # from this point on, create a snapshot when the first attribute is
        # changed
        self._snapshot_on_setattr = True

    def __setattr__(self, name, value):
        if self._should_take_snapshot(name, value):
            self.snapshot()
        super(HistoryMixinOld, self).__setattr__(name, value)

    def _should_take_snapshot(self, name, value):
        if not self._snapshot_on_setattr:
            return False
        if self.snapshotted_state:
            return False
        if name.startswith("_"):
            return False
        return True

    def snapshot(self, previous=None):
        if not self.SNAPSHOT_HISTORY:
            return

        # first, turn off the setattr snapshot trigger
        self.__dict__["_snapshot_on_setattr"] = False
        if previous:
            self.post_init_newly_created = previous.id is None
        else:
            previous = self

        self.snapshotted_state = self.get_history_dict()

    def _check_history_snapshot_allowed(self):
        if not self.SNAPSHOT_HISTORY:
            raise Exception("Editing and snapshotting not allowed")

    def get_history_dict(self):
        self._check_history_snapshot_allowed()
        return {settings_key: getattr(self, settings_key) for settings_key in self.history_fields}

    def get_model_state_changes(self, new_dict, current_dict=None):
        self._check_history_snapshot_allowed()
        if not self.snapshotted_state:
            self.snapshot()
        current_dict = current_dict or self.snapshotted_state

        # we want to display sensible defaults in case a new settings
        # objects was created
        if self.post_init_newly_created:
            # remove defaults from changes
            # this means that new settings changes for newly created settings
            # will always include defaults as fields that were changed:
            for key in self.get_defaults_dict():
                if key not in current_dict:
                    continue
                del current_dict[key]

        changes = OrderedDict()
        for field_name in self.history_fields:
            if field_name not in new_dict:
                continue
            new_value = new_dict[field_name]
            if current_dict.get(field_name) != new_value:
                changes[field_name] = new_value
        return changes

    def get_history_changes_text(self, changes, separator=", "):
        self._check_history_snapshot_allowed()

        change_strings = []
        for key, value in changes.items():
            prop = self.get_human_prop_name(key)
            if not prop:
                continue
            val = self.get_human_value(key, value)
            change_strings.append(self._extract_value_diff_text(key, prop, val))
        return separator.join(change_strings)

    def _extract_value_diff_text(self, key, prop, val):
        previous_value = None
        previous_value_raw = self.snapshotted_state.get(key) if self.snapshotted_state else None
        if previous_value_raw:
            previous_value = self.get_human_value(key, previous_value_raw)

        if previous_value and previous_value != val:
            return '{} set from "{}" to "{}"'.format(prop, previous_value, val)
        else:
            return '{} set to "{}"'.format(prop, val)

    def get_changes_text_from_dict(self, changes, separator=", "):
        self._check_history_snapshot_allowed()

        statements = []
        if not changes or self.post_init_newly_created and changes:
            statements.append("Created settings")
        changes_text = self.get_history_changes_text(changes, separator=separator)
        if changes_text:
            statements.append(changes_text)
        return ". ".join(statements)

    def construct_changes(self, created_text, created_text_id, changes):
        """
        Created text of form - (created_text) created_text_id (changes)
        Values in braces are situational.
        """
        self._check_history_snapshot_allowed()

        parts = []
        if self.post_init_newly_created:
            parts.append(created_text)

        if created_text_id:
            parts.append(created_text_id)
        text = self.get_history_changes_text(changes)
        if text:
            parts.append(text)
        changes_text = " ".join(parts)
        return changes, changes_text
