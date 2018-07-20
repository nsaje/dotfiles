import newrelic.agent

from functools import partial

from utils import sort_helper, threads

from stats.constants import get_target_dimension
import stats.constraints_helper
import stats.helpers

from dash.dashapi import loaders
from dash.dashapi import augmenter
from dash.dashapi import helpers


def query(level, user, breakdown, constraints, parents, order, offset, limit):
    query_threads = query_async_start(level, user, breakdown, constraints, parents)
    return query_async_get_results(query_threads, breakdown, order, offset, limit)


def query_for_rows(rows, level, user, breakdown, constraints, parents, order, offset, limit, structure_w_stats):
    query_threads = query_async_start(level, user, breakdown, constraints, parents)
    return query_async_get_results_for_rows(
        query_threads, rows, breakdown, parents, order, offset, limit, structure_w_stats
    )


def query_async_start(level, user, breakdown, constraints, parents):
    query_threads = []
    for parent in parents or [None]:
        fn = partial(query_section, level, user, breakdown, constraints, parent)
        thread = threads.AsyncFunction(fn)
        thread.start()

        query_threads.append(thread)

    return query_threads


def query_async_get_results(query_threads, breakdown, order, offset=None, limit=None):
    target_dimension = stats.constants.get_target_dimension(breakdown)

    rows = []
    for thread in query_threads:
        thread.join()
        thread_rows = thread.get_result()["rows"]

        thread_rows = sort_helper.sort_rows_by_order_and_archived(
            thread_rows, [order] + get_default_order(target_dimension, order)
        )
        thread_rows = sort_helper.apply_offset_limit(thread_rows, offset, limit)

        rows.extend(thread_rows)

    return rows


def query_async_get_results_for_rows(query_threads, rows, breakdown, parents, order, offset, limit, structure_w_stats):
    parent_breakdown = stats.constants.get_parent_breakdown(breakdown)
    target_dimension = stats.constants.get_target_dimension(breakdown)

    rows_by_parent = sort_helper.group_rows_by_breakdown_key(parent_breakdown, rows)
    structure_by_parent = sort_helper.group_rows_by_breakdown_key(parent_breakdown, structure_w_stats)

    augment_fn = augmenter.get_augmenter_for_dimension(target_dimension)

    result = []

    for thread in query_threads:
        thread.join()

        thread_result = thread.get_result()

        parent = thread_result["parent"]
        loader = thread_result["loader"]
        dash_rows = thread_result["rows"]

        parent_key = sort_helper.get_breakdown_key(parent, parent_breakdown)

        stat_rows = rows_by_parent.get(parent_key, [])

        rows_target_ids = [x[target_dimension] for x in stat_rows]
        selected_rows = [x for x in dash_rows if x[target_dimension] in rows_target_ids]

        dash_rows_by_id = {x[target_dimension]: x for x in dash_rows}

        selected_rows = []
        for row in stat_rows:
            if row[target_dimension] in dash_rows_by_id:
                selected_rows.append(dash_rows_by_id[row[target_dimension]])

            elif target_dimension == "publisher_id":
                # when dealing with publishers create dash rows from stats rows - not everything can be queried out
                # out dash database as in other dimensions that are augmented by dash.

                dash_row = augmenter.make_row(target_dimension, row[target_dimension], parent)
                augment_fn([dash_row], loader, not bool(parent_breakdown))
                selected_rows.append(dash_row)

        # add dash rows that were not included in stats. publisher dimension is excluded here
        # as we should not add those rows
        if len(rows_target_ids) < limit and target_dimension != "publisher_id":
            # select additional rows from
            structure_4p = structure_by_parent.get(parent_key, [])
            all_used_ids = [x[target_dimension] for x in structure_4p]

            new_offset, new_limit = helpers.get_adjusted_limits_for_additional_rows(
                rows_target_ids, all_used_ids, offset, limit
            )

            extra_rows = [x for x in dash_rows if x[target_dimension] not in all_used_ids]
            extra_rows = sort_helper.sort_rows_by_order_and_archived(
                extra_rows, get_default_order(target_dimension, order)
            )
            selected_rows.extend(sort_helper.apply_offset_limit(extra_rows, new_offset, new_limit))

        result.extend(selected_rows)
    return result


@newrelic.agent.function_trace()
def query_section(level, user, breakdown, constraints, parent=None):
    """
    Create dash rows for one breakdown section. Eg. if breakdown is campaign_id, ad_group_id
    a section will be ad groups of a single campaign. When breakdown is 1 level only, a section
    is whole 1st level.
    """

    target_dimension = get_target_dimension(breakdown)

    constraints = stats.constraints_helper.reduce_to_parent(breakdown, constraints, parent)
    loader_cls = loaders.get_loader_for_dimension(target_dimension, level)
    loader = loader_cls.from_constraints(user, constraints)

    rows = augmenter.make_dash_rows(target_dimension, loader.objs_ids, parent)
    augmenter_fn = augmenter.get_augmenter_for_dimension(target_dimension)

    augmenter_fn(rows, loader, not bool(parent))

    return {"rows": rows, "loader": loader, "parent": parent}


@newrelic.agent.function_trace()
def get_totals(level, user, breakdown, constraints):
    row = {}
    if len(breakdown) == 1:
        loader_cls = loaders.get_loader_for_dimension(stats.constants.get_target_dimension(breakdown), level)
        if breakdown == ["source_id"]:
            loader = loader_cls.from_constraints(user, constraints)
            augmenter.augment_sources_totals(row, loader)

        elif breakdown == ["account_id"]:
            loader = loader_cls.from_constraints(user, constraints)
            augmenter.augment_accounts_totals(row, loader)

        elif breakdown == ["campaign_id"]:
            loader = loader_cls.from_constraints(user, constraints)
            augmenter.augment_campaigns_totals(row, loader)

    return row


def get_default_order(target_dimension, order):
    """
    Order that is applied to rows whose primary order field value is None.
    """

    prefix, _ = sort_helper.dissect_order(order)

    return [prefix + "name", prefix + target_dimension]
