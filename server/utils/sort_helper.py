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

        if field.startswith('-'):
            reverse = True
            field = field[1:]

        def _key(item):
            value = item.get(field)

            if isinstance(value, basestring):
                value = value.lower()

            # here we use a tuple that will be used for comparison.
            # The first item is True if value is None - this is needed
            # to put all None values at the end of the list.
            # XOR is used to negate this value if sorting order is reversed.
            return ((item.get(field) is None) ^ reverse, value)

        rows = sorted(rows, key=_key, reverse=reverse)

    return rows


def map_by_breakdown(rows, breakdown, mapper):
    result = {}
    first_dimensions = breakdown[:-1]

    for row in rows:
        row_dict = result
        for dimension in first_dimensions:
            row_dict = row_dict.setdefault(row[dimension], {})
        row_dict[row[breakdown[-1]]] = mapper(row)

    return result
