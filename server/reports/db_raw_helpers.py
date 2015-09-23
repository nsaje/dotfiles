from django.db import models


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


class MyCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, statement, params):
        self.cursor.execute(statement, params)

    def dictfetchall(self):
        return dictfetchall(self)

    def close(self):
        self.cursor.close()
