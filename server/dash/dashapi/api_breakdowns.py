import newrelic.agent

from functools import partial

from utils import sort_helper

from stats.constants import get_target_dimension
import stats.constraints_helper
import stats.helpers

from dash.dashapi import loaders
from dash.dashapi import augmenter
from dash.dashapi import helpers
from dash import threads


def query(level, breakdown, constraints, parents, order, offset, limit):
    query_threads = query_async_start(level, breakdown, constraints, parents)
    return query_async_get_results(query_threads, order, offset, limit)


def query_for_rows(rows, level, breakdown, constraints, parents, order, offset, limit, structure_w_stats):
    query_threads = query_async_start(level, breakdown, constraints, parents)
    return query_async_get_results_for_rows(query_threads, rows, breakdown, parents, order, offset, limit, structure_w_stats)


def query_async_start(level, breakdown, constraints, parents):
    query_threads = []
    for parent in (parents or [None]):
        fn = partial(query_section, level, breakdown, constraints, parent)
        thread = threads.AsyncFunction(fn)
        thread.start()

        query_threads.append(thread)

    return query_threads


def query_async_get_results(query_threads, order=None, offset=None, limit=None):
    rows = []
    for thread in query_threads:
        thread.join()
        thread_rows = thread.result

        if order:
            thread_rows = sort_helper.sort_rows_by_order_and_archived(thread_rows, order)
            thread_rows = helpers.apply_offset_limit(thread_rows, offset, limit)

        rows.extend(thread_rows)

    return rows


def query_async_get_results_for_rows(query_threads, rows, breakdown, parents, order, offset, limit, structure_w_stats):
    parent_breakdown = stats.constants.get_parent_breakdown(breakdown)
    target_dimension = stats.constants.get_target_dimension(breakdown)

    rows_by_parent = stats.helpers.group_rows_by_breakdown(parent_breakdown, rows)
    dash_rows_by_parent = stats.helpers.group_rows_by_breakdown(
        parent_breakdown,
        query_async_get_results(query_threads))
    structure_by_parent = stats.helpers.group_rows_by_breakdown(parent_breakdown, structure_w_stats)

    result = []

    for parent in (parents or [None]):
        parent_id_tuple = stats.helpers.get_breakdown_id_tuple(parent, parent_breakdown)

        rows_4p = rows_by_parent[parent_id_tuple]
        dash_rows_4p = dash_rows_by_parent[parent_id_tuple]

        rows_target_ids = [x[target_dimension] for x in rows_4p]
        selected_rows = [x for x in dash_rows_4p if x[target_dimension] in rows_target_ids]

        # check if we need to add some additional rows
        if len(rows_target_ids) < limit:
            # select additional rows from
            structure_4p = structure_by_parent[parent_id_tuple]
            all_used_ids = [x[target_dimension] for x in structure_4p]

            new_offset, new_limit = helpers.get_adjusted_limits_for_additional_rows(
                rows_target_ids, all_used_ids, offset, limit)

            extra_rows = [x for x in dash_rows_4p if x[target_dimension] not in all_used_ids]
            extra_rows = sort_helper.sort_rows_by_order_and_archived(extra_rows,
                                                                     get_default_order(target_dimension, order))
            selected_rows.extend(helpers.apply_offset_limit(extra_rows, new_offset, new_limit))

        result.extend(selected_rows)
    return result


@newrelic.agent.function_trace()
def query_section(level, breakdown, constraints, parent=None):
    target_dimension = get_target_dimension(breakdown)

    constraints = stats.constraints_helper.reduce_to_parent(breakdown, constraints, parent)
    loader_cls = loaders.get_loader_for_dimension(target_dimension)
    loader = loader_cls.from_constraints(level, constraints)

    rows = stats.helpers.make_rows(target_dimension, loader.objs_ids, parent)
    augmenter_fn = augmenter.get_augmenter_for_dimension(target_dimension)

    augmenter_fn(rows, loader, not bool(parent))

    return rows


@newrelic.agent.function_trace()
def get_totals(level, breakdown, constraints):
    target_dimension = get_target_dimension(breakdown)

    row = {}
    if breakdown == ['source_id']:
        loader = loaders.SourcesLoader.from_constraints(level, constraints)
        augmenter.augment_sources_totals(row, loader)

    elif breakdown == ['account_id']:
        loader = loaders.AccountsLoader.from_constraints(level, constraints)
        augmenter.augment_accounts_totals(row, loader)

    elif breakdown == ['campaign_id']:
        loader = loaders.CampaignsLoader.from_constraints(level, constraints)
        augmenter.augment_campaigns_totals(row, loader)

    return row


def get_default_order(target_dimension, order):
    prefix, order_field = sort_helper.dissect_order(order)

    return [prefix + 'name', prefix + target_dimension]
