# -*- coding: utf-8 -*-
from collections import OrderedDict


class HistoryMixin(object):
    def __init__(self):
        self.post_init_newly_created = self.id is None

    def get_history_dict(self):
        return {settings_key: getattr(self, settings_key) for settings_key in self.history_fields}

    def get_model_state_changes(self, new_dict, current_dict=None):
        current_dict = current_dict or self.get_history_dict()

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
        previous_value_raw = getattr(self, key)
        if previous_value_raw:
            previous_value = self.get_human_value(key, previous_value_raw)

        if previous_value and previous_value != val:
            return '{} set from "{}" to "{}"'.format(prop, previous_value, val)
        else:
            return '{} set to "{}"'.format(prop, val)

    def get_changes_text_from_dict(self, changes, separator=", "):
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
        parts = []
        if self.post_init_newly_created:
            parts.append(created_text)
        text = self.get_history_changes_text(changes)
        if self.post_init_newly_created or text:
            if created_text_id:
                parts.append(created_text_id)
            if text:
                parts.append(text)
        changes_text = " ".join(parts)
        return changes, changes_text
