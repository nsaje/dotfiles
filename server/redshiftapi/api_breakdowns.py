import influx
import logging
from functools import partial

from django.core.cache import caches

from redshiftapi import db
from redshiftapi import models
from redshiftapi import queries
from redshiftapi import postprocess
from redshiftapi import helpers
from redshiftapi import newbase

from stats import constants
from stats.helpers import group_rows_by_breakdown
from utils import exc
from utils import cache_helper
from utils import sort_helper
from dash import threads

logger = logging.getLogger(__name__)

CACHE_MISS_FLAG = None

"""
NOTE: caching in this module is of experimental nature. Patterns used are
very rudimentary and would need a facelift (for example: cursor middleware for caching to make
the code less verbose) for proper production code.
"""


def query(breakdown, constraints, parents, goals, order, offset, limit, use_publishers_view=False, use_experimental_calls=False):
    """
    Returns an array of rows that are represented as dicts.
    """

    if use_experimental_calls:
        return query_all(breakdown, constraints, parents, goals, order, offset, limit, use_publishers_view)

    model = models.MVMaster(goals.conversion_goals, goals.pixels, goals.campaign_goals, goals.campaign_goal_values)
    query, params = queries.prepare_breakdown_query(model, breakdown, constraints, parents,
                                                    order, offset, limit, use_publishers_view=use_publishers_view)

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


def query_stats_for_rows(rows, breakdown, constraints, goals, use_experimental_calls=False):
    model = models.MVMaster(goals.conversion_goals, goals.pixels, goals.campaign_goals, goals.campaign_goal_values)

    parents = helpers.create_parents(rows, breakdown)

    if use_experimental_calls:
        stats_rows = query_all_for_rows(rows, breakdown, constraints, parents, goals)
    else:
        query, params = queries.prepare_augment_query(model, breakdown, constraints, parents)
        stats_rows = execute_query(query, params, breakdown)

    return helpers.merge_rows(breakdown, rows, stats_rows)


def query_all(breakdown, constraints, parents, goals, order, offset, limit, use_publishers_view=False):
    """
    Experimantal base level - query all.
    """

    sql, params = newbase.prepare_base_level_query(breakdown, constraints, parents, use_publishers_view)
    t_base = threads.AsyncFunction(partial(execute_query, sql, params, breakdown, extra_name='__base'))
    t_base.start()

    sql, params = newbase.prepare_base_level_yesterday_spend_query(breakdown, constraints, parents, use_publishers_view)
    t_yesterday = threads.AsyncFunction(partial(execute_query, sql, params, breakdown, extra_name='__yesterday'))
    t_yesterday.start()

    t_conversions = None
    if goals.conversion_goals:
        sql, params = newbase.prepare_base_level_conversions_query(breakdown, constraints, parents, use_publishers_view)
        t_conversions = threads.AsyncFunction(partial(execute_query, sql, params, breakdown, extra_name='__conversions'))
        t_conversions.start()

    t_touchpoints = None
    if goals.pixels:
        sql, params = newbase.prepare_base_level_touchpoint_conversions_query(breakdown, constraints, parents, use_publishers_view)
        t_touchpoints = threads.AsyncFunction(partial(execute_query, sql, params, breakdown, extra_name='__touchpoints'))
        t_touchpoints.start()

    t_base.join()
    base_rows = t_base.get_result()

    t_yesterday.join()
    yesterday_rows = t_yesterday.get_result()

    conversions_rows = []
    if t_conversions is not None:
        t_conversions.join()
        conversions_rows = t_conversions.get_result()

    touchpoint_rows = []
    if t_touchpoints is not None:
        t_touchpoints.join()
        touchpoint_rows = t_touchpoints.get_result()

    rows = newbase.calculate_stats(breakdown, base_rows, yesterday_rows, touchpoint_rows, conversions_rows, goals)

    rows = sort_helper.sort_results(rows, order)
    rows = sort_helper.apply_offset_limit(rows, offset, limit)

    return rows


def query_all_for_rows(rows, breakdown, constraints, parents, goals, use_publishers_view=False):
    """
    Experimantal base level - query all.
    """

    sql, params = newbase.prepare_base_level_query(breakdown, constraints, parents, use_publishers_view)
    t_base = threads.AsyncFunction(partial(execute_query, sql, params, breakdown, extra_name='__base'))
    t_base.start()

    sql, params = newbase.prepare_base_level_yesterday_spend_query(breakdown, constraints, parents, use_publishers_view)
    t_yesterday = threads.AsyncFunction(partial(execute_query, sql, params, breakdown, extra_name='__yesterday'))
    t_yesterday.start()

    t_conversions = None
    if goals.conversion_goals:
        sql, params = newbase.prepare_base_level_conversions_query(breakdown, constraints, parents, use_publishers_view)
        t_conversions = threads.AsyncFunction(
            partial(execute_query, sql, params, breakdown, extra_name='__conversions'))
        t_conversions.start()

    t_touchpoints = None
    if goals.pixels:
        sql, params = newbase.prepare_base_level_touchpoint_conversions_query(
            breakdown, constraints, parents, use_publishers_view)
        t_touchpoints = threads.AsyncFunction(
            partial(execute_query, sql, params, breakdown, extra_name='__touchpoints'))
        t_touchpoints.start()

    t_base.join()
    base_rows = t_base.get_result()

    t_yesterday.join()
    yesterday_rows = t_yesterday.get_result()

    conversions_rows = []
    if t_conversions is not None:
        t_conversions.join()
        conversions_rows = t_conversions.get_result()

    touchpoint_rows = []
    if t_touchpoints is not None:
        t_touchpoints.join()
        touchpoint_rows = t_touchpoints.get_result()

    stats_rows = newbase.calculate_stats(breakdown, base_rows, yesterday_rows, touchpoint_rows, conversions_rows, goals)

    rows_by_breakdown = group_rows_by_breakdown(breakdown, rows, max_1=True)
    stats_rows_by_breakdown = group_rows_by_breakdown(breakdown, stats_rows, max_1=True)

    print "I'm here"
    return [row for breakdown_id, row in stats_rows_by_breakdown.iteritems() if breakdown_id in rows_by_breakdown]


def execute_query(query, params, breakdown, postprocess_fn=None, extra_name=''):
    cache_key = cache_helper.get_cache_key(query, params)
    cache = caches['breakdowns_rs']

    results = cache.get(cache_key, CACHE_MISS_FLAG)
    query_name = "__".join(breakdown) + extra_name

    if results is CACHE_MISS_FLAG:
        influx.incr('redshiftapi.api_breakdowns.cache_miss', 1)
        logger.info('Cache miss %s (%s)', cache_key, query_name)

        with influx.block_timer('redshiftapi.api_breakdowns.query', breakdown=query_name):
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
        logger.info('Cache hit %s (%s)', cache_key, query_name)

    return results
