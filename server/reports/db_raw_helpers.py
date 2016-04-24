import collections

from django.db import models
from django.db.models.query import QuerySet


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


