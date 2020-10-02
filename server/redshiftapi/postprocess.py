import collections
import datetime

from dateutil import relativedelta
from dateutil import rrule

import dash.models
import stats.helpers
from dash import constants as dash_constants
from stats import constants
from stats import fields
from utils import sort_helper

"""
Apply any modifications to reports that should be returned by redshiftapi as data source
but are easier to do in python than in sql.
"""

POSTCLICK_FIELDS = [
    "visits",
    "click_discrepancy",
    "pageviews",
    "new_visits",
    "percent_new_users",
    "bounce_rate",
    "pv_per_visit",
    "avg_tos",
    "returning_users",
    "unique_users",
    "new_users",
    "bounced_visits",
    "total_seconds",
    "avg_etfm_cost_per_minute",
    "non_bounced_visits",
    "avg_etfm_cost_per_non_bounced_visit",
    "total_pageviews",
    "avg_etfm_cost_per_pageview",
    "avg_etfm_cost_per_new_visitor",
    "avg_etfm_cost_per_visit",
    "avg_etfm_cost_per_unique_user",
]


CONVERSION_WINDOWS_PER_SUFFIX = [
    (None, sorted(dash.constants.ConversionWindowsLegacy.get_all())),
    ("_view", sorted(dash.constants.ConversionWindowsViewthrough.get_all())),
]


def fill_in_missing_rows(rows, breakdown, constraints, parents, orders, offset, limit):
    target_dimension = constants.get_target_dimension(breakdown)

    if target_dimension in constants.TimeDimension._ALL:
        _fill_in_missing_rows_time_dimension(target_dimension, rows, breakdown, constraints, parents)
        rows = sort_helper.sort_results(rows, orders)

    return rows


def generate_time_dimension_counts(breakdown, constraints, parents):
    target_dimension = constants.get_target_dimension(breakdown)
    all_dates = _get_representative_dates(target_dimension, constraints)

    rows = []
    for parent in parents:
        row = {"count": len(all_dates)}
        row.update(**parent)
        rows.append(row)

    return rows


def _fill_in_missing_rows_time_dimension(target_dimension, rows, breakdown, constraints, parent):
    """
    When querying time dimensions add rows that are missing from a query
    so that result is a nice constant time series.
    """

    all_dates = _get_representative_dates(target_dimension, constraints)
    _fill_in_missing_rows(target_dimension, rows, breakdown, parent, all_dates)


def _fill_in_missing_rows(target_dimension, rows, breakdown, parent, all_values):
    parent_breakdown = constants.get_parent_breakdown(breakdown)

    rows_per_parent_breakdown = collections.defaultdict(list)
    for row in rows:
        parent_br_key = sort_helper.get_breakdown_key(row, parent_breakdown)
        rows_per_parent_breakdown[parent_br_key].append(row)

    if not parent:
        assert len(list(rows_per_parent_breakdown.keys())) <= 1
        parent = [sort_helper.get_breakdown_key({}, parent_breakdown)]

    for bc in parent:
        parent_br_key = sort_helper.get_breakdown_key(bc, parent_breakdown)

        # collect used constants for rows returned
        used = set(row[target_dimension] for row in rows_per_parent_breakdown[parent_br_key])

        for x in all_values:
            if x not in used:
                new_row = {target_dimension: x}
                new_row.update(bc)  # update with parent

                rows_per_parent_breakdown[parent_br_key].append(new_row)
                rows.append(new_row)

        # cut rows that are not a part of the final collection
        for x in used:
            if x not in all_values:
                excess_row = [row for row in rows_per_parent_breakdown[parent_br_key] if row[target_dimension] == x][0]

                rows.remove(excess_row)


def _get_representative_dates(time_dimension, constraints):
    """
    Returns dates that represent time dimension values within constraints.
    This logics should be synced with how we query time dimensions from
    database.
    """

    start_date = constraints["date__gte"]
    end_date = constraints.get("date__lte")
    if end_date is None:
        end_date = constraints["date__lt"] - datetime.timedelta(days=1)

    if time_dimension == constants.TimeDimension.DAY:
        dates = rrule.rrule(rrule.DAILY, start_date, until=end_date)
    elif time_dimension == constants.TimeDimension.WEEK:
        # all weeks in the span starting monday
        dates = rrule.rrule(
            rrule.WEEKLY,
            start_date + relativedelta.relativedelta(weekday=relativedelta.MO(-1)),
            until=end_date,
            byweekday=rrule.MO,
        )
    else:
        # all months starting 1st
        dates = rrule.rrule(rrule.MONTHLY, start_date + relativedelta.relativedelta(day=1), until=end_date)

    return list(x.date() for x in dates)


def _is_row_empty(row):
    for key, value in list(row.items()):
        if key not in fields.DIMENSION_FIELDS and value:
            return False
    return True


def set_default_values(breakdown, rows):
    remove_postclicks = constants.get_delivery_dimension(breakdown) is not None

    for row in rows:
        if remove_postclicks:
            # HACK: Temporary hack that removes postclick data when we breakdown by delivery
            for key in POSTCLICK_FIELDS:
                if key in row:
                    row[key] = None


def remove_empty_rows_delivery_dimension(breakdown, rows):
    if constants.get_target_dimension(breakdown) not in constants.DeliveryDimension._ALL:
        return
    rows[:] = [row for row in rows if not _is_row_empty(row)]


def postprocess_joint_query_rows(rows):
    for row in rows:
        for column in [x for x in list(row.keys()) if x.startswith("etfm_performance_")]:
            # this is specific to joint queries - performance returned needs to be converted to category
            row[column] = dash.campaign_goals.get_goal_performance_category(row[column])


def merge_rows(breakdown, base_rows, yesterday_rows, touchpoint_rows, conversion_rows, goals):
    """
    Applies conversions, pixels and goals columns to rows. Equivalent to what redshiftapi joint model
    does, the only difference is that joint model calculates this in SQL directly.

    Since touchpoint conversions must be joined with an outer join, it's possible that additional rows get created
    for conversions that don't have a matching base row.
    """

    rows = stats.helpers.merge_rows(breakdown, base_rows, yesterday_rows)

    if goals:
        if goals.conversion_goals:
            apply_conversion_goal_columns(breakdown, rows, goals.conversion_goals, conversion_rows)
        if goals.pixels:
            apply_pixel_columns(breakdown, rows, goals.pixels, touchpoint_rows)
        if goals.campaign_goals:
            apply_performance_columns(
                breakdown, rows, goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals, goals.pixels
            )
    return rows


def apply_conversion_goal_columns(breakdown, rows, conversion_goals, conversion_rows):
    if not conversion_goals:
        return

    conversion_breakdown = breakdown + ["slug"]
    conversion_rows_map = sort_helper.group_rows_by_breakdown_key(conversion_breakdown, conversion_rows, max_1=True)

    for conversion_goal in conversion_goals:
        if conversion_goal.type not in dash_constants.REPORT_GOAL_TYPES:
            continue

        stats_key = conversion_goal.get_stats_key()
        conversion_key = conversion_goal.get_view_key(conversion_goals)

        for row in rows:
            conversion_breakdown_id = sort_helper.get_breakdown_key(row, breakdown) + (stats_key,)
            conversion_row = conversion_rows_map.get(conversion_breakdown_id)

            if conversion_row:
                count = conversion_row["count"] if conversion_row else None
                conversion_rate = count / row["clicks"] * 100.0 if count is not None and row["clicks"] else None
                avg_etfm_cost = (float(row["etfm_cost"] or 0) / count) if count else None
                local_avg_etfm_cost = (float(row["local_etfm_cost"] or 0) / count) if count else None
            else:
                count = None
                conversion_rate = None
                avg_etfm_cost = None
                local_avg_etfm_cost = None

            row.update(
                {
                    conversion_key: count,
                    "conversion_rate_per_" + conversion_key: conversion_rate,
                    "avg_etfm_cost_per_" + conversion_key: avg_etfm_cost,
                    "local_avg_etfm_cost_per_" + conversion_key: local_avg_etfm_cost,
                }
            )


def apply_pixel_columns(breakdown, rows, pixels, touchpoint_rows):
    if not pixels:
        return

    pixel_breakdown = breakdown + ["slug"]
    pixel_rows_map = sort_helper.group_rows_by_breakdown_key(pixel_breakdown, touchpoint_rows, max_1=False)

    _join_to_existing_rows(breakdown, rows, pixels, pixel_rows_map)
    _add_unjoined_conversions(breakdown, rows, pixels, pixel_rows_map)


def _join_to_existing_rows(breakdown, rows, pixels, pixel_rows_map):
    for row in rows:
        breakdown_key = sort_helper.get_breakdown_key(row, breakdown)
        for pixel in pixels:
            pixel_breakdown_key = breakdown_key + (pixel.slug,)
            pixel_rows = pixel_rows_map.pop(pixel_breakdown_key, None)
            if pixel_rows:
                _add_pixel_columns_to_row(row, pixel, pixel_rows)


def _add_unjoined_conversions(breakdown, rows, pixels, pixel_rows_map):
    additional_rows = {}
    for pixel_breakdown_key, pixel_rows in pixel_rows_map.items():
        slug = pixel_breakdown_key[-1]
        breakdown_key = pixel_breakdown_key[:-1]
        pixel = next((p for p in pixels if p.slug == slug), None)
        if not pixel:
            continue
        row = additional_rows.setdefault(breakdown_key, dict(zip(breakdown, breakdown_key)))
        _add_pixel_columns_to_row(row, pixel, pixel_rows)
    rows.extend(additional_rows.values())


def _add_pixel_columns_to_row(row, pixel, pixel_rows):
    etfm_cost = row.get("etfm_cost") or 0
    local_etfm_cost = row.get("local_etfm_cost") or 0
    clicks = row.get("clicks") or 0

    for suffix, conversion_windows in CONVERSION_WINDOWS_PER_SUFFIX:
        for conversion_window in conversion_windows:
            if pixel_rows:
                count = sum(x["count" + (suffix or "")] for x in pixel_rows if x["window"] <= conversion_window)
                conversion_rate = count / clicks * 100.0 if clicks else None
                avg_etfm_cost = float(etfm_cost) / count if count else None
                local_avg_etfm_cost = float(local_etfm_cost) / count if count else None

                value = float(
                    sum(
                        x["conversion_value" + (suffix or "")]
                        for x in pixel_rows
                        if x["window"] <= conversion_window
                        if x["conversion_value"]
                    )
                )
                etfm_roas = value / float(local_etfm_cost) if local_etfm_cost else None
            else:
                count = None
                conversion_rate = None
                avg_etfm_cost = None
                local_avg_etfm_cost = None
                etfm_roas = None

            pixel_key = pixel.get_view_key(conversion_window) + (suffix or "")

            row.update(
                {
                    pixel_key: count,
                    "conversion_rate_per_" + pixel_key: conversion_rate,
                    "avg_etfm_cost_per_" + pixel_key: avg_etfm_cost,
                    "local_avg_etfm_cost_per_" + pixel_key: local_avg_etfm_cost,
                    "etfm_roas_" + pixel_key: etfm_roas,
                }
            )


def apply_performance_columns(breakdown, rows, campaign_goals, campaign_goal_values, conversion_goals, pixels):
    if len(rows) < 1:
        return

    map_camp_goal_vals = {x.campaign_goal_id: x for x in campaign_goal_values or []}
    map_conversion_goals = {x.id: x for x in conversion_goals or []}
    pixel_ids = [x.id for x in pixels] if pixels else []

    campaign_goals_by_campaign_id = collections.defaultdict(list)
    for campaign_goal in campaign_goals:
        campaign_goals_by_campaign_id[campaign_goal.campaign_id].append(campaign_goal)

    for row in rows:
        if "campaign_id" in row:
            campaign_goals = campaign_goals_by_campaign_id[row["campaign_id"]]
        for campaign_goal in campaign_goals:
            if campaign_goal.type == dash.constants.CampaignGoalKPI.CPA:
                if campaign_goal.conversion_goal_id not in map_conversion_goals:
                    # if conversion goal is not amongst campaign goals do not calculate performance
                    continue

                conversion_goal = map_conversion_goals[campaign_goal.conversion_goal_id]

                if conversion_goal.pixel_id not in pixel_ids:
                    # in case pixel is not part of this query (eg archived etc)
                    continue

                conversion_key = conversion_goal.get_view_key(conversion_goals)

                def metric_value_fn(row, cost_column):
                    return (float(row.get(cost_column) or 0) / row[conversion_key]) if row.get(conversion_key) else None

            else:

                def metric_value_fn(row, cost_column):
                    # cost_column not used, but this fn should be compatible with the above metric_value_fn
                    # with_local_prefix=False because USD metric values should be used to calculate performance
                    primary_metric_map = dash.campaign_goals.get_goal_to_primary_metric_map(with_local_prefix=False)
                    metric = primary_metric_map[campaign_goal.type]
                    return row.get(metric)

            campaign_goal_value = map_camp_goal_vals.get(campaign_goal.pk)

            if campaign_goal_value and campaign_goal_value.value:
                planned_value = campaign_goal_value.value
            else:
                planned_value = None

            goal_key = campaign_goal.get_view_key()

            row["etfm_performance_" + goal_key] = dash.campaign_goals.get_goal_performance_status(
                campaign_goal.type, metric_value_fn(row, "etfm_cost"), planned_value, row.get("etfm_cost")
            )
