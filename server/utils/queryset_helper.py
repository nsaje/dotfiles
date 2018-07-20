def simplify_query(qs):
    return qs.model.objects.filter(pk__in=get_pk_list(qs))


def get_pk_list(qs):
    return list(qs.values_list("pk", flat=True))
