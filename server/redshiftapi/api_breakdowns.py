import backtosql
from functools import partial
from dash import threads
import stats.constants

from utils import sort_helper

from redshiftapi import db
from redshiftapi import helpers
from redshiftapi import postprocess
from redshiftapi import queries
from redshiftapi import view_selector


def should_query_all(breakdown):
    if len(breakdown) == 0:
        return True

    if stats.constants.get_target_dimension(breakdown) in stats.constants.TimeDimension._ALL:
        return True

    if len(breakdown) == 1:
        if stats.constants.PUBLISHER in breakdown:
            return False

        return True

    if len(breakdown) == 2:
        if not {stats.constants.CAMPAIGN, stats.constants.AD_GROUP, stats.constants.SOURCE} - set(breakdown):
            # these combinations should not produce too big results
            return True

    return False


def query(breakdown, constraints, parents, goals, order, offset, limit, use_publishers_view=False):

    target_dimension = stats.constants.get_target_dimension(breakdown)
    if target_dimension in stats.constants.TimeDimension._ALL:
        constraints = helpers.get_time_dimension_constraints(target_dimension, constraints, offset, limit)

    if should_query_all(breakdown):
        all_rows = _query_all(breakdown, constraints, parents, goals, use_publishers_view,
                              breakdown_for_name=breakdown, extra_name='all')
        rows = sort_helper.sort_results(all_rows, order)
        rows = sort_helper.apply_offset_limit(rows, offset, limit)
    elif len(breakdown) == 1:
        sql, params = queries.prepare_query_joint_base(
            breakdown, constraints, parents, order, offset, limit, goals, use_publishers_view)
        rows = db.execute_query(sql, params, helpers.get_query_name(breakdown))
        postprocess.postprocess_joint_query(rows)
    else:
        sql, params = queries.prepare_query_joint_levels(
            breakdown, constraints, parents, order, offset, limit, goals, use_publishers_view)
        rows = db.execute_query(sql, params, helpers.get_query_name(breakdown))
        postprocess.postprocess_joint_query(rows)

    rows = postprocess.postprocess_breakdown_query(rows, breakdown, constraints, parents, order, offset, limit)
    postprocess.remove_postclick_values(breakdown, rows)
    return rows


def query_stats_for_rows(rows, breakdown, constraints, goals, use_publishers_view=False):
    if should_query_all(breakdown):
        stats_rows = _query_all(breakdown, constraints, None, goals, use_publishers_view,
                                breakdown_for_name=breakdown, extra_name='rows')
        rows = helpers.select_relevant_rows(breakdown, rows, stats_rows)
    else:
        parents = helpers.create_parents(rows, breakdown)  # this limits the query to rows we are looking for
        rows = _query_all(breakdown, constraints, parents, goals, use_publishers_view,
                          breakdown_for_name=breakdown, extra_name='rows')

    postprocess.remove_postclick_values(breakdown, rows)
    return rows


def query_structure_with_stats(breakdown, constraints, use_publishers_view=False):
    sql, params = queries.prepare_query_structure_with_stats(breakdown, constraints, use_publishers_view)
    return db.execute_query(sql, params, helpers.get_query_name(breakdown, 'str_w_stats'))


def query_totals(breakdown, constraints, goals, use_publishers_view=False):
    return _query_all([], constraints, None, goals, use_publishers_view,
                      breakdown_for_name=breakdown, extra_name='totals')


def _query_all(breakdown, constraints, parents, goals, use_publishers_view,
               breakdown_for_name=[], extra_name=''):

    sql, params = queries.prepare_query_all_base(breakdown, constraints, parents, use_publishers_view)
    t_base = threads.AsyncFunction(
        partial(db.execute_query, sql, params, helpers.get_query_name(
            breakdown_for_name, '{}_base'.format(extra_name))))
    t_base.start()

    sql, params = queries.prepare_query_all_yesterday(breakdown, constraints, parents, use_publishers_view)
    t_yesterday = threads.AsyncFunction(
        partial(db.execute_query, sql, params, helpers.get_query_name(
            breakdown_for_name, '{}_yesterday'.format(extra_name))))
    t_yesterday.start()

    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    support_conversions = view_selector.supports_conversions(needed_dimensions)

    t_conversions = None
    t_touchpoints = None
    if support_conversions:
        if goals.conversion_goals:
            sql, params = queries.prepare_query_all_conversions(
                breakdown + ['slug'], constraints, parents, use_publishers_view)
            t_conversions = threads.AsyncFunction(
                partial(db.execute_query, sql, params, helpers.get_query_name(
                    breakdown_for_name, '{}_conversions'.format(extra_name))))
            t_conversions.start()

        if goals.pixels:
            sql, params = queries.prepare_query_all_touchpoints(
                breakdown + ['slug', 'window'], constraints, parents, use_publishers_view)
            t_touchpoints = threads.AsyncFunction(
                partial(db.execute_query, sql, params, helpers.get_query_name(
                    breakdown_for_name, '{}_touchpoints'.format(extra_name))))
            t_touchpoints.start()

    base_rows = t_base.join_and_get_result()
    yesterday_rows = t_yesterday.join_and_get_result()

    conversions_rows = []
    if t_conversions is not None:
        conversions_rows = t_conversions.join_and_get_result()

    touchpoint_rows = []
    if t_touchpoints is not None:
        touchpoint_rows = t_touchpoints.join_and_get_result()

    rows = postprocess.postprocess_join_rows(
        breakdown, base_rows, yesterday_rows, touchpoint_rows, conversions_rows, goals)

    return rows
