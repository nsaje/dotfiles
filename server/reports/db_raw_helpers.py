from django.db import models
import collections
import types


def dictfetchall(cursor):
    desc = cursor.description

    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def get_obj_id(obj):
    if isinstance(obj, models.Model):
        return obj.pk
    return obj


def quote(field):
    if isinstance(field, collections.Sequence) and not isinstance(field, types.StringTypes):
        return [quote(f) for f in field]
    return '"{}"'.format(field)
