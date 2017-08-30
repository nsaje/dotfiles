from functools import partial
import stats.constants

from utils import sort_helper, threads

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

    if stats.constants.get_target_dimension(breakdown) == stats.constants.DEVICE:
        return True

    if len(breakdown) == 1:
        if stats.constants.PUBLISHER in breakdown:
            return False

        return True

    if len(breakdown) == 2:
        if not set(breakdown) - {stats.constants.CAMPAIGN, stats.constants.AD_GROUP, stats.constants.SOURCE}:
            # these combinations should not produce too big results
            return True

    return False


def query(breakdown, constraints, parents, goals, order, offset, limit, use_publishers_view=False, is_reports=False):
    orders = [order, '-media_cost'] + breakdown

    target_dimension = stats.constants.get_target_dimension(breakdown)
    if target_dimension in stats.constants.TimeDimension._ALL:
        constraints = helpers.get_time_dimension_constraints(target_dimension, constraints, offset, limit)
        # offset is not needed anymore because constraints were set accordingly
        offset = 0

    if should_query_all(breakdown):
        all_rows = query_all(breakdown, constraints, parents, goals, use_publishers_view,
                             breakdown_for_name=breakdown, extra_name='all')

        rows = sort_helper.sort_results(all_rows, orders)
        if not is_reports:
            rows = postprocess.fill_in_missing_rows(rows, breakdown, constraints, parents, orders, offset, limit)

        # cut the resultset to size
        rows = sort_helper.apply_offset_limit_to_breakdown(
            stats.constants.get_parent_breakdown(breakdown), rows, offset, limit)
    else:
        if len(breakdown) == 1 or is_reports:
            sql, params = queries.prepare_query_joint_base(
                breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view,
                skip_performance_columns=is_reports)
        else:
            sql, params = queries.prepare_query_joint_levels(
                breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view)

        rows = db.execute_query(sql, params, helpers.get_query_name(breakdown))

        postprocess.postprocess_joint_query_rows(rows)
        if not is_reports:
            rows = postprocess.fill_in_missing_rows(rows, breakdown, constraints, parents, orders, offset, limit)

    postprocess.set_default_values(breakdown, rows)
    return rows


def query_stats_for_rows(rows, breakdown, constraints, goals, use_publishers_view=False):
    if should_query_all(breakdown):
        stats_rows = query_all(breakdown, constraints, None, goals, use_publishers_view,
                               breakdown_for_name=breakdown, extra_name='rows')
        rows = helpers.select_relevant_stats_rows(breakdown, rows, stats_rows)
    else:
        parents = helpers.create_parents(rows, breakdown)  # this limits the query to rows we are looking for
        rows = query_all(breakdown, constraints, parents, goals, use_publishers_view,
                         breakdown_for_name=breakdown, extra_name='rows')

    postprocess.set_default_values(breakdown, rows)
    return rows


def query_structure_with_stats(breakdown, constraints, use_publishers_view=False):
    sql, params = queries.prepare_query_structure_with_stats(breakdown, constraints, use_publishers_view)
    return db.execute_query(sql, params, helpers.get_query_name(breakdown, 'str_w_stats'))


def query_totals(breakdown, constraints, goals, use_publishers_view=False):
    rows = query_all([], constraints, None, goals, use_publishers_view,
                     breakdown_for_name=breakdown, extra_name='totals')
    postprocess.set_default_values([], rows)
    return rows


def query_all(breakdown, constraints, parents, goals, use_publishers_view,
              breakdown_for_name=[], extra_name='', metrics=None):

    t_base = None
    t_yesterday = None
    t_conversions = None
    t_touchpoints = None

    sql, params = queries.prepare_query_all_base(breakdown, constraints, parents, use_publishers_view)
    t_base = threads.AsyncFunction(
        partial(db.execute_query, sql, params, helpers.get_query_name(
            breakdown_for_name, '{}_base'.format(extra_name))))
    t_base.start()

    if not metrics or set(metrics).intersection(set(['yesterday_cost', 'e_yesterday_cost'])):
        sql, params = queries.prepare_query_all_yesterday(breakdown, constraints, parents, use_publishers_view)
        t_yesterday = threads.AsyncFunction(
            partial(db.execute_query, sql, params, helpers.get_query_name(
                breakdown_for_name, '{}_yesterday'.format(extra_name))))
        t_yesterday.start()

    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    support_conversions = view_selector.supports_conversions(needed_dimensions, use_publishers_view)

    if goals and support_conversions:
        if goals.conversion_goals:
            if not metrics or any(helpers.is_conversion_goal_metric(metric) for metric in metrics):
                sql, params = queries.prepare_query_all_conversions(
                    breakdown + ['slug'], constraints, parents, use_publishers_view)
                t_conversions = threads.AsyncFunction(
                    partial(db.execute_query, sql, params, helpers.get_query_name(
                        breakdown_for_name, '{}_conversions'.format(extra_name))))
                t_conversions.start()

        if goals.pixels:
            if not metrics or any(helpers.is_pixel_metric(metric) for metric in metrics):
                sql, params = queries.prepare_query_all_touchpoints(
                    breakdown + ['slug', 'window'], constraints, parents, use_publishers_view)
                t_touchpoints = threads.AsyncFunction(
                    partial(db.execute_query, sql, params, helpers.get_query_name(
                        breakdown_for_name, '{}_touchpoints'.format(extra_name))))
                t_touchpoints.start()

    base_rows = []
    if t_base is not None:
        base_rows = t_base.join_and_get_result()

    yesterday_rows = []
    if t_yesterday is not None:
        yesterday_rows = t_yesterday.join_and_get_result()

    conversions_rows = []
    if t_conversions is not None:
        conversions_rows = t_conversions.join_and_get_result()

    touchpoint_rows = []
    if t_touchpoints is not None:
        touchpoint_rows = t_touchpoints.join_and_get_result()

    rows = postprocess.merge_rows(
        breakdown, base_rows, yesterday_rows, touchpoint_rows, conversions_rows, goals)

    return rows
