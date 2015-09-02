from django.db import models
import collections
import types


def dictfetchall(cursor):
    desc = cursor.description
    fetch_results = cursor.fetchall()

    return [
        dict(zip([col[0] for col in desc], row))
        for row in fetch_results
    ]


def get_obj_id(obj):
    if isinstance(obj, models.Model):
        return obj.pk
    return obj


def _quote(field):
    if isinstance(field, collections.Sequence) and not isinstance(field, types.StringTypes):
        return [_quote(f) for f in field]
    return '"{}"'.format(field)
