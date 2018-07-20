from operator import itemgetter


def get_changes_text_from_dict(self, changes, separator=", "):
    if changes is None:
        return "Created settings"
    change_strings = []
    for key, value in sorted(changes.items(), key=itemgetter(0)):
        prop = self.get_human_prop_name(key)
        val = self.get_human_value(key, value)
        change_strings.append('{} set to "{}"'.format(prop, val))
    return separator.join(change_strings)
