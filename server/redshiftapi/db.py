import influx
import logging
from collections import namedtuple

from django.conf import settings
from django.db import connections, transaction
from django.core.cache import caches

from utils import cache_helper

logger = logging.getLogger(__name__)

CACHE_MISS_FLAG = None


def get_stats_cursor():
    return connections[settings.STATS_DB_NAME].cursor()


def get_write_stats_cursor():
    return connections[settings.STATS_DB_NAME].cursor()


def get_write_stats_transaction():
    return transaction.atomic(using=settings.STATS_DB_NAME)


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict

    C/P from django docs
    https://docs.djangoproject.com/en/1.9/topics/db/sql/#connections-and-cursors
    """

    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def namedtuplefetchall(cursor):
    """
    Return all rows from a cursor as a namedtuple
    """

    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def xnamedtuplefetchall(cursor):
    """
    Returns a generator of rows as a namedtuple
    """

    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    for row in cursor:
        yield nt_result(*row)


def execute_query(sql, params, query_name, cache_name='breakdowns_rs', refresh_cache=False):
    cache_key = cache_helper.get_cache_key(sql, params)
    cache = caches[cache_name]

    results = cache.get(cache_key, CACHE_MISS_FLAG)

    if results is CACHE_MISS_FLAG or refresh_cache:
        influx.incr('redshiftapi.cache', 1, outcome='miss')
        logger.info('Cache miss %s (%s)', cache_key, query_name)

        with influx.block_timer('redshiftapi.api_breakdowns.query', breakdown=query_name):
            with get_stats_cursor() as cursor:
                cursor.execute(sql, params)
                results = dictfetchall(cursor)

        with influx.block_timer('redshiftapi.api_breakdowns.set_cache_value_overhead'):
            cache.set(cache_key, results)
    else:
        influx.incr('redshiftapi.cache', 1, outcome='hit')
        logger.info('Cache hit %s (%s)', cache_key, query_name)

    return results
