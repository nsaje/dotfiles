
def apply_offset_limit(qs, offset, limit):
    if offset and limit:
        return qs[offset:offset + limit]

    if offset:
        return qs[offset:]

    if limit:
        return qs[:limit]

    return qs


def apply_breakdown_page_to_rows(breakdown_page, rows):
    for row in rows:
        row.update(breakdown_page)
