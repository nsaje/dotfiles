import collections


def sort_results(results, order_fields=None):

    # when there is only a single item passed
    # in instead of a list, return it immediately
    if not isinstance(results, collections.Sequence):
        return results

    # make a copy to prevent changing original sequence
    rows = results[:]

    if not order_fields or not len(order_fields):
        return rows

    for field in reversed(order_fields):
        reverse = False

        if field.startswith("-"):
            reverse = True
            field = field[1:]

        def _key(item):
            value = item.get(field)

            if isinstance(value, str):
                value = value.lower()

            # here we use a tuple that will be used for comparison.
            # The first item is True if value is None - this is needed
            # to put all None values at the end of the list.
            # XOR is used to negate this value if sorting order is reversed.
            return ((item.get(field) is None) ^ reverse, value)

        rows = sorted(rows, key=_key, reverse=reverse)

    return rows


def sort_rows_by_order_and_archived(rows, order_fields, archived_field="archived"):
    if isinstance(order_fields, str):
        order_fields = [order_fields]

    order_fields = [archived_field] + order_fields

    return sort_results(rows, order_fields)


def map_by_breakdown(rows, breakdown, mapper):
    result = {}
    first_dimensions = breakdown[:-1]

    for row in rows:
        row_dict = result
        for dimension in first_dimensions:
            row_dict = row_dict.setdefault(row[dimension], {})
        row_dict[row[breakdown[-1]]] = mapper(row)

    return result


def dissect_order(order):
    prefix = ""
    field_name = order
    if order.startswith("-"):
        prefix = order[0]
        field_name = order[1:]

    return prefix, field_name


def get_breakdown_key(row, breakdown):
    # returns a pickable breakdown identifier
    return tuple(row[dim] for dim in breakdown)


def group_rows_by_breakdown_key(breakdown, rows, max_1=False):
    """
    Groups rows by breakdown keys. Returns an OrderedDict where keys
    are ordered by the order they first appeared in rows.
    """

    groups = collections.OrderedDict()

    for row in rows:
        key = get_breakdown_key(row, breakdown)
        if key not in groups:
            groups[key] = []

        groups[key].append(row)

    if max_1:
        for breakdown_id, rows in groups.items():
            if len(rows) > 1:
                raise Exception("Expected 1 row per breakdown got {}".format(len(rows)))
            groups[breakdown_id] = rows[0]

    return groups


def apply_offset_limit(rows, offset, limit):
    if offset and limit:
        return rows[offset : offset + limit]

    if offset:
        return rows[offset:]

    if limit:
        return rows[:limit]

    return rows


def apply_offset_limit_to_breakdown(breakdown, rows, offset, limit):
    groups = group_rows_by_breakdown_key(breakdown, rows)
    rows = []
    for group_rows in list(groups.values()):
        rows.extend(apply_offset_limit(group_rows, offset, limit))

    return rows
