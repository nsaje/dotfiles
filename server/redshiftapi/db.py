import influx
import logging
from collections import namedtuple

from django.db import connections, transaction
from django.core.cache import caches

from utils import cache_helper
import utils.db_for_reads

logger = logging.getLogger(__name__)

CACHE_MISS_FLAG = None


stats_db_router = utils.db_for_reads.UseStatsReadReplicaRouter()


def get_stats_cursor(db_alias=None):
    if not db_alias:
        db_alias = stats_db_router.db_for_read(None)
    influx.incr('redshiftapi.cursor', 1, db_alias=db_alias, type='read')
    return connections[db_alias].cursor()


def get_write_stats_cursor(db_alias=None):
    if not db_alias:
        db_alias = stats_db_router.db_for_write(None)
    influx.incr('redshiftapi.cursor', 1, db_alias=db_alias, type='write')
    return connections[db_alias].cursor()


def get_write_stats_transaction(db_alias=None):
    if not db_alias:
        db_alias = stats_db_router.db_for_write(None)
    return transaction.atomic(using=db_alias)


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

        with get_stats_cursor() as cursor:
            with influx.block_timer('redshiftapi.api_breakdowns.query', breakdown=query_name, db_alias=cursor.db.alias):
                cursor.execute(sql, params)
                results = dictfetchall(cursor)

        with influx.block_timer('redshiftapi.api_breakdowns.set_cache_value_overhead'):
            cache.set(cache_key, results)
    else:
        influx.incr('redshiftapi.cache', 1, outcome='hit')
        logger.info('Cache hit %s (%s)', cache_key, query_name)

    return results
