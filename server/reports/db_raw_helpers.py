import collections

from django.db import models
from django.db.models.query import QuerySet


def dictfetchall(cursor):
    desc = cursor.description

    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def is_collection(value):
    return ((isinstance(value, collections.Iterable) or isinstance(value, QuerySet))
            and type(value) not in (str, unicode))


def extract_obj_ids(objects):

    if isinstance(objects, dict):
        for key, value in objects.items():
            if is_collection(value):
                objects[key] = [get_obj_id(item) for item in value]
            else:
                objects[key] = get_obj_id(value)

    elif is_collection(objects):
        return [get_obj_id(item) for item in objects]

    return objects


def get_obj_id(obj):
    if isinstance(obj, models.Model):
        return obj.pk
    return obj


class MyCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, statement, params):
        self.cursor.execute(statement, params)

    def fetchall(self):
        return self.cursor.fetchall()

    def dictfetchall(self):
        return dictfetchall(self.cursor)

    def close(self):
        self.cursor.close()

    def mogrify(self, *args, **kwargs):
        return self.cursor.mogrify(*args, **kwargs)
