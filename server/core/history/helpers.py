def get_changes_text_from_dict(cls, changes, separator=', '):
    if changes is None:
        return 'Created settings'
    change_strings = []
    for key, value in changes.iteritems():
        prop = cls.get_human_prop_name(key)
        val = cls.get_human_value(key, value)
        change_strings.append(
            u'{} set to "{}"'.format(prop, val)
        )
    return separator.join(change_strings)
