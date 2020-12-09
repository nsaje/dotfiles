def get_bid_modifier_formatter(direction, target, get_mapping, no_changes_text):
    def format(change_step, changes):
        if not changes:
            return no_changes_text

        values_dict = {key: round((val["new_value"] - 1) * 100, 2) for key, val in changes.items()}

        mapping = get_mapping()
        message = "{} bid modifier for {}% {}: {}".format(
            direction,
            round(change_step * 100, 2),
            target,
            ", ".join(_get_changes_breakdown(changes, mapping, values_dict)),
        )
        return message

    return format


def get_paused_formatter(target, get_mapping, no_changes_text):
    def format(change_step, changes):
        if not changes:
            return no_changes_text

        mapping = get_mapping()
        message = "Paused {}: {}".format(target, ", ".join(_get_changes_breakdown(changes, mapping)))
        return message

    return format


def get_bid_formatter(direction, target, no_changes_text):
    def format(changes_step, changes):
        if not changes:
            return no_changes_text

        values = next(iter(changes.values()))
        message = "{} {} bid for ${} to ${}".format(direction, target, changes_step, values["new_value"])
        return message

    return format


def get_budget_formatter(direction, target, no_changes_text):
    def format(changes_step, changes):
        if not changes:
            return no_changes_text

        values = next(iter(changes.values()))
        message = "{} {} daily budget from ${} to ${}".format(
            direction, target, values["old_value"], values["new_value"]
        )
        return message

    return format


def get_email_formatter(target, no_changes_text):
    def format(changes_step, changes):
        if not changes:
            return no_changes_text

        message = "Sent {} email".format(target)
        return message

    return format


def get_blacklist_formatter(target, get_mapping, no_changes_text):
    def format(changes_step, changes):
        if not changes:
            return no_changes_text

        mapping = get_mapping()
        message = "Blacklisted {}: {}".format(target, ", ".join(_get_changes_breakdown(changes, mapping)))
        return message

    return format


def get_add_to_publisher_formatter(target, get_mapping, no_changes_text):
    def format(changes_step, changes):
        if not changes:
            return no_changes_text

        mapping = get_mapping()
        message = "Added {} to the publisher group: {}".format(
            target, ", ".join(_get_changes_breakdown(changes, mapping))
        )
        return message

    return format


def _get_changes_breakdown(changes, mapping, values_dict=None):
    if changes is None:
        return []

    items_breakdown = []

    for changed_item in changes:
        if values_dict:
            items_breakdown.append(
                "{} ({}%)".format(_get_mapped_item(changed_item, mapping), values_dict[changed_item])
            )
        else:
            items_breakdown.append(_get_mapped_item(changed_item, mapping))

    return items_breakdown


def _get_mapped_item(changed_item, mapping):
    if changed_item.isnumeric():
        return mapping.get(int(changed_item), changed_item)
    else:
        return mapping.get(changed_item, changed_item)
