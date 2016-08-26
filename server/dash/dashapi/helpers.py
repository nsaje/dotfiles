
def apply_offset_limit(qs, offset, limit):
    if offset and limit:
        return qs[offset:offset + limit]

    if offset:
        return qs[offset:]

    if limit:
        return qs[:limit]

    return qs


def apply_parents_to_rows(parents, rows):
    for row in rows:
        row.update(parents)
