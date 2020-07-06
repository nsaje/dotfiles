def get_bid_modifier_formatter(direction, target, get_mapping):
    def format(change_step, changes):
        mapping = get_mapping()
        return "{} bid modifier for {}% {}: {}".format(
            direction, change_step, target, ", ".join(_get_changes_breakdown(changes, mapping, True))
        )

    return format


def get_paused_formatter(target, get_mapping):
    def format(change_step, changes):
        mapping = get_mapping()
        return "Paused {}: {}".format(target, ", ".join(_get_changes_breakdown(changes, mapping)))

    return format


def get_bid_formatter(direction, target):
    def format(changes_step, changes):
        if changes is None:
            return "{} {} bid for ${}".format(direction, target, changes_step)

        values = next(iter(changes.values()))
        return "{} {} bid for ${} to ${}".format(direction, target, changes_step, values["new_value"])

    return format


def get_budget_formatter(direction, target):
    def format(changes_step, changes):
        if changes is None:
            return "{} {} daily budget".format(direction, target)

        values = next(iter(changes.values()))
        return "{} {} daily budget from ${} to ${}".format(direction, target, values["old_value"], values["new_value"])

    return format


def get_email_formatter(target):
    def format(changes_step, changes):
        return "Sent {} email".format(target)

    return format


def get_blacklist_formatter(target, get_mapping):
    def format(changes_step, changes):
        mapping = get_mapping()
        return "Blacklisted {}: {}".format(target, ", ".join(_get_changes_breakdown(changes, mapping)))

    return format


def get_add_to_publisher_formatter(get_mapping):
    def format(changes_step, changes):
        mapping = get_mapping()
        return "Added publisher to the publisher group: {}".format(", ".join(_get_changes_breakdown(changes, mapping)))

    return format


def _get_changes_breakdown(changes, mapping, with_values=False):
    if changes is None:
        return []

    items_breakdown = []

    for changed_item in changes:
        if with_values:
            items_breakdown.append(
                "{} ({}%)".format(_get_mapped_item(changed_item, mapping), round(changes[changed_item]["new_value"], 2))
            )
        else:
            items_breakdown.append(_get_mapped_item(changed_item, mapping))

    return items_breakdown


def _get_mapped_item(changed_item, mapping):
    if changed_item.isnumeric():
        return mapping.get(int(changed_item), changed_item)
    else:
        return mapping.get(changed_item, changed_item)
