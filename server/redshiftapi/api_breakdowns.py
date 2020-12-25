import time
from functools import partial

from django.conf import settings

import dash.constants
import stats.constants
from utils import cache_helper
from utils import dates_helper
from utils import db_router
from utils import metrics_compat
from utils import sort_helper
from utils import threads

from . import background_cache
from . import db
from . import exceptions
from . import helpers
from . import postprocess
from . import queries
from . import view_selector

POSTGRES_MAX_DAYS = settings.STATS_DB_POSTGRES_MAX_DAYS
POSTGRES_EXCLUDE_VIEWS = ("mv_master", "mv_account_placement", "mv_campaign_placement", "mv_adgroup_placement")
POSTGRES_REPORTS_EXCLUDE_VIEWS = (
    "mv_account_pubs",
    "mv_campaign_pubs",
    "mv_adgroup_pubs",
    "mv_contentad_pubs",
    "mv_account_placement",
    "mv_campaign_placement",
    "mv_adgroup_placement",
)
HOT_CLUSTER_MAX_DAYS = settings.STATS_DB_HOT_CLUSTER_MAX_DAYS


def query_with_background_cache(*args, **kwargs):
    key = cache_helper.get_cache_key(args, kwargs)

    rows = background_cache.get(key)
    if rows is None:
        rows = query(*args, **kwargs)
        background_cache.set(key, rows, args, kwargs)

    return rows


def query(
    breakdown,
    constraints,
    parents,
    goals,
    order=None,
    offset=None,
    limit=None,
    use_publishers_view=False,
    is_reports=False,
    query_all=False,
    breakdown_for_name=None,
    extra_name="",
    metrics=None,
    query_counts=False,
):
    stats_database_type = _get_stats_database_type(breakdown, constraints, parents, use_publishers_view, is_reports)
    with db_router.use_stats_database(stats_database_type):
        orders = ["-media_cost"] + breakdown
        if order is not None:
            orders = [order] + orders

        target_dimension = stats.constants.get_target_dimension(breakdown)
        if not is_reports and target_dimension in stats.constants.TimeDimension._ALL:
            # NOTE: this optimization is breakdown specific and doesn't work when querying for reports
            constraints = helpers.get_time_dimension_constraints(target_dimension, constraints, offset, limit)
            # offset is not needed anymore because constraints were set accordingly
            offset = 0

        if breakdown_for_name is None:
            breakdown_for_name = breakdown

        db_alias = db.stats_db_router.db_for_read(None)
        t0 = time.time()

        if query_counts:
            query_type = "query_counts"
            if target_dimension in stats.constants.TimeDimension._ALL:
                rows = postprocess.generate_time_dimension_counts(breakdown, constraints, parents)
            else:
                sql, params, temp_tables = queries.prepare_query_counts(
                    breakdown, constraints, parents, use_publishers_view
                )
                rows = db.execute_query(
                    sql,
                    params,
                    helpers.get_query_name(breakdown_for_name, extra_name="{}_base".format(extra_name)),
                    temp_tables=temp_tables,
                )
        else:
            if query_all or _should_query_all(breakdown, is_reports):
                query_type = "query_all"
                all_rows = _query_all(
                    breakdown,
                    constraints,
                    parents,
                    goals,
                    use_publishers_view,
                    breakdown_for_name=breakdown_for_name,
                    extra_name=extra_name,
                    metrics=metrics,
                )

                rows = sort_helper.sort_results(all_rows, orders)
                if not is_reports:
                    rows = postprocess.fill_in_missing_rows(
                        rows, breakdown, constraints, parents, orders, offset, limit
                    )

                # cut the resultset to size
                rows = sort_helper.apply_offset_limit_to_breakdown(
                    stats.constants.get_parent_breakdown(breakdown), rows, offset, limit
                )
            else:
                if len(breakdown) == 1 or is_reports:
                    query_type = "query_joint"
                    sql, params, temp_tables = queries.prepare_query_joint_base(
                        breakdown,
                        constraints,
                        parents,
                        orders,
                        offset,
                        limit,
                        goals,
                        use_publishers_view,
                        skip_performance_columns=is_reports,
                    )
                else:
                    query_type = "query_joint_levels"
                    sql, params, temp_tables = queries.prepare_query_joint_levels(
                        breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view
                    )

                rows = db.execute_query(
                    sql, params, helpers.get_query_name(breakdown_for_name), temp_tables=temp_tables
                )

                postprocess.postprocess_joint_query_rows(rows)
                if not is_reports:
                    rows = postprocess.fill_in_missing_rows(
                        rows, breakdown, constraints, parents, orders, offset, limit
                    )

            postprocess.set_default_values(breakdown, rows)
            postprocess.remove_empty_rows_delivery_dimension(breakdown, rows)

        metrics_compat.incr("redshiftapi.api_breakdowns.query_type", 1, type=query_type, db_alias=db_alias)
        metrics_compat.timing(
            "redshiftapi.api_breakdowns.query_type_timer", (time.time() - t0), type=query_type, db_alias=db_alias
        )

        return rows


def query_stats_for_rows(rows, breakdown, constraints, goals, use_publishers_view=False):
    if _should_query_all(breakdown):
        stats_rows = query_with_background_cache(
            breakdown,
            constraints,
            None,
            goals,
            use_publishers_view=use_publishers_view,
            query_all=True,
            extra_name="rows",
        )
        rows = helpers.select_relevant_stats_rows(breakdown, rows, stats_rows)
    else:
        parents = helpers.create_parents(rows, breakdown)  # this limits the query to rows we are looking for
        rows = query_with_background_cache(
            breakdown,
            constraints,
            parents,
            goals,
            use_publishers_view=use_publishers_view,
            query_all=True,
            extra_name="rows",
        )

    postprocess.set_default_values(breakdown, rows)
    postprocess.remove_empty_rows_delivery_dimension(breakdown, rows)
    return rows


def query_structure_with_stats(breakdown, constraints, use_publishers_view=False):
    sql, params, temp_tables = queries.prepare_query_structure_with_stats(breakdown, constraints, use_publishers_view)
    return db.execute_query(sql, params, helpers.get_query_name(breakdown, "str_w_stats"), temp_tables=temp_tables)


def query_totals(breakdown, constraints, goals, use_publishers_view=False):
    rows = query_with_background_cache(
        [],
        constraints,
        None,
        goals,
        use_publishers_view=use_publishers_view,
        breakdown_for_name=breakdown,
        extra_name="totals",
    )
    return rows


def query_counts(breakdown, constraints, parents, goals, use_publishers_view=False):
    rows = query_with_background_cache(
        breakdown,
        constraints,
        parents,
        goals,
        use_publishers_view=use_publishers_view,
        breakdown_for_name=breakdown,
        extra_name="counts",
        query_counts=True,
    )
    return rows


def _should_query_all(breakdown, is_reports=False):
    if is_reports:
        return False

    if len(breakdown) == 0:
        return True

    if stats.constants.get_target_dimension(breakdown) in stats.constants.TimeDimension._ALL:
        return True

    if len(breakdown) == 1 and stats.constants.is_top_level_delivery_dimension(
        stats.constants.get_target_dimension(breakdown)
    ):
        return False

    if len(breakdown) == 1:
        if stats.constants.PUBLISHER in breakdown or stats.constants.is_placement_breakdown(breakdown):
            return False
        return True

    if len(breakdown) == 2:
        if not set(breakdown) - {stats.constants.CAMPAIGN, stats.constants.AD_GROUP, stats.constants.SOURCE}:
            # these combinations should not produce too big results
            return True

    return False


def _get_stats_database_type(
    breakdown, constraints, parents, use_publishers_view, is_reports
) -> dash.constants.StatsDatabaseType:
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    view = view_selector.get_best_view_base(needed_dimensions, use_publishers_view)
    date_constraint = constraints.get("date__gte") or constraints.get("date__gt") or constraints.get("date")
    date_in_postgres = dates_helper.days_before(dates_helper.local_today(), POSTGRES_MAX_DAYS)
    date_in_hot_clusters = dates_helper.days_before(dates_helper.local_today(), HOT_CLUSTER_MAX_DAYS)

    if is_reports and view in POSTGRES_REPORTS_EXCLUDE_VIEWS:
        if date_in_hot_clusters and date_constraint > date_in_hot_clusters:
            return dash.constants.StatsDatabaseType.HOT_CLUSTER
        return dash.constants.StatsDatabaseType.COLD_CLUSTER

    if date_constraint and date_constraint > date_in_postgres and view not in POSTGRES_EXCLUDE_VIEWS:
        return dash.constants.StatsDatabaseType.POSTGRES

    if date_in_hot_clusters and date_constraint > date_in_hot_clusters:
        return dash.constants.StatsDatabaseType.HOT_CLUSTER
    return dash.constants.StatsDatabaseType.COLD_CLUSTER


def _query_all(
    breakdown, constraints, parents, goals, use_publishers_view, breakdown_for_name=[], extra_name="", metrics=None
):
    t_base = None
    t_yesterday = None
    t_conversions = None
    t_touchpoints = None

    sql, params, temp_tables = queries.prepare_query_all_base(breakdown, constraints, parents, use_publishers_view)
    t_base = threads.AsyncFunction(
        partial(
            db.execute_query,
            sql,
            params,
            helpers.get_query_name(breakdown_for_name, "{}_base".format(extra_name)),
            temp_tables=temp_tables,
        )
    )
    t_base.start()

    if not metrics or set(metrics).intersection(set(["yesterday_at_cost", "yesterday_etfm_cost"])):
        sql, params, temp_tables = queries.prepare_query_all_yesterday(
            breakdown, constraints, parents, use_publishers_view
        )
        t_yesterday = threads.AsyncFunction(
            partial(
                db.execute_query,
                sql,
                params,
                helpers.get_query_name(breakdown_for_name, "{}_yesterday".format(extra_name)),
                temp_tables=temp_tables,
            )
        )
        t_yesterday.start()

    if goals and goals.conversion_goals:
        if not metrics or any(helpers.is_conversion_goal_metric(metric) for metric in metrics):

            try:
                sql, params, temp_tables = queries.prepare_query_all_conversions(
                    breakdown + ["slug"], constraints, parents
                )

                t_conversions = threads.AsyncFunction(
                    partial(
                        db.execute_query,
                        sql,
                        params,
                        helpers.get_query_name(breakdown_for_name, "{}_conversions".format(extra_name)),
                        temp_tables=temp_tables,
                    )
                )
                t_conversions.start()
            except exceptions.ViewNotAvailable:
                pass

    if goals and goals.pixels:
        if not metrics or any(helpers.is_pixel_metric(metric) for metric in metrics):
            try:
                sql, params, temp_tables = queries.prepare_query_all_touchpoints(
                    breakdown + ["slug", "window"], constraints, parents
                )

                t_touchpoints = threads.AsyncFunction(
                    partial(
                        db.execute_query,
                        sql,
                        params,
                        helpers.get_query_name(breakdown_for_name, "{}_touchpoints".format(extra_name)),
                        temp_tables=temp_tables,
                    )
                )
                t_touchpoints.start()
            except exceptions.ViewNotAvailable:
                pass

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

    rows = postprocess.merge_rows(breakdown, base_rows, yesterday_rows, touchpoint_rows, conversions_rows, goals)

    return rows
