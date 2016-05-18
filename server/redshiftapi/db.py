from collections import namedtuple

from django.conf import settings
from django.db import connections


def get_stats_cursor():
    return connections[settings.STATS_DB_NAME].cursor()

# C/P from django docs
# https://docs.djangoproject.com/en/1.9/topics/db/sql/#connections-and-cursors
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"

    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"

    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
