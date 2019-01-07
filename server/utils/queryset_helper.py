def simplify_query(qs):
    return qs.model.objects.filter(pk__in=get_pk_list(qs))


def get_pk_list(qs):
    return list(qs.values_list("pk", flat=True))


def chunk_iterator(qs, chunk_size=2000):
    """
    Iterate QuerySet results in chunks.
    :param qs: the QuerySet
    :param chunk_size: the size of a chunk
    """
    chunk = []
    for record in qs.iterator(chunk_size=chunk_size):
        chunk.append(record)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk
