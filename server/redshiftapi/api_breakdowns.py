import influx
import logging

from django.core.cache import caches

from redshiftapi import db
from redshiftapi import models
from redshiftapi import queries
from redshiftapi import postprocess
from redshiftapi import helpers

from stats import constants
from stats.helpers import group_rows_by_breakdown
from utils import exc
from utils import cache_helper

logger = logging.getLogger(__name__)


"""
NOTE: caching in this module is of experimental nature. Patterns used are
very rudimentary and would need a facelift (for example: cursor middleware for caching to make
the code less verbose) for proper production code.
"""


def query(breakdown, constraints, parents, goals, order, offset, limit):
    """
    Returns an array of rows that are represented as dicts.
    """

    model = models.MVMaster(goals.conversion_goals, goals.pixels, goals.campaign_goals, goals.campaign_goal_values)
    query, params = queries.prepare_breakdown_query(model, breakdown, constraints, parents,
                                                    order, offset, limit)

    def postprocess_fn(rows, empty_row):
        return postprocess.postprocess_breakdown_query(rows, empty_row, breakdown, constraints, parents,
                                                       order, offset, limit)

    results = execute_query(query, params, breakdown, postprocess_fn)

    return results


def query_structure_with_stats(breakdown, constraints):
    """
    Returns all structure rows that have stats. Does not return stats, just dimensions.
    """

    model = models.MVMaster()
    query, params = queries.prepare_query_structure_with_stats_query(model, breakdown, constraints)

    rows = execute_query(query, params, breakdown)

    return rows


def augment(rows, breakdown, constraints, goals):
    model = models.MVMaster(goals.conversion_goals, goals.pixels, goals.campaign_goals, goals.campaign_goal_values)

    parents = helpers.create_parents(rows, breakdown)
    query, params = queries.prepare_augment_query(model, breakdown, constraints, parents)

    stats_rows = execute_query(query, params, breakdown)

    return helpers.merge_rows(breakdown, rows, stats_rows)


def execute_query(query, params, breakdown, postprocess_fn=None):
    cache_key = cache_helper.get_cache_key(query, params)
    cache = caches['breakdowns_rs']
    results = cache.get(cache_key, None)

    if not results:
        influx.incr('redshiftapi.api_breakdowns.cache_miss', 1)
        logger.info('Cache miss %s', cache_key)

        with influx.block_timer('redshiftapi.api_breakdowns.query', breakdown="__".join(breakdown)):
            with db.get_stats_cursor() as cursor:
                cursor.execute(query, params)
                results = db.dictfetchall(cursor)

                empty_row = db.get_empty_row_dict(cursor.description)

        if postprocess_fn:
            results = postprocess_fn(results, empty_row)
        helpers.remove_postclick_values(breakdown, results)

        with influx.block_timer('redshiftapi.api_breakdowns.set_cache_value_overhead'):
            cache.set(cache_key, results)
    else:
        influx.incr('redshiftapi.api_breakdowns.cache_hit', 1)
        logger.info('Cache hit %s', cache_key)

    return results
