import collections
import datetime
from dateutil import rrule, relativedelta

import newrelic.agent

from utils import sort_helper
from dash import conversions_helper

from dash import constants as dash_constants
import dash.models

import stats.helpers
from stats import constants


"""
Apply any modifications to reports that should be returned by redshiftapi as data source
but are easier to do in python than in sql.
"""


POSTCLICK_FIELDS = [
    'visits', 'click_discrepancy', 'pageviews', 'new_visits', 'percent_new_users', 'bounce_rate',
    'pv_per_visit', 'avg_tos', 'returning_users', 'unique_users', 'new_users', 'bounced_visits',
    'total_seconds', 'avg_cost_per_minute', 'non_bounced_visits', 'avg_cost_per_non_bounced_visit',
    'total_pageviews', 'avg_cost_per_pageview', 'avg_cost_for_new_visitor', 'avg_cost_per_visit',
]


def fill_in_missing_rows(rows, breakdown, constraints, parents, orders, offset, limit):
    target_dimension = constants.get_target_dimension(breakdown)

    if target_dimension in constants.TimeDimension._ALL:
        _fill_in_missing_rows_time_dimension(target_dimension, rows, breakdown, constraints, parents)
        rows = sort_helper.sort_results(rows, orders)

    if target_dimension == 'device_type':
        _fill_in_missing_rows_device_type_dimension(target_dimension, rows, breakdown, parents, offset, limit)
        rows = sort_helper.sort_results(rows, orders)

    return rows


def _fill_in_missing_rows_time_dimension(target_dimension, rows, breakdown, constraints, parent):
    """
    When querying time dimensions add rows that are missing from a query
    so that result is a nice constant time series.
    """

    all_dates = _get_representative_dates(target_dimension, constraints)
    _fill_in_missing_rows(target_dimension, rows, breakdown, parent, all_dates)


def _fill_in_missing_rows_device_type_dimension(target_dimension, rows, breakdown, parent, offset, limit):
    all_values = sorted(dash_constants.DeviceType._VALUES.keys())

    _fill_in_missing_rows(
        target_dimension, rows, breakdown, parent,
        all_values[offset:offset + limit]
    )


def _fill_in_missing_rows(target_dimension, rows, breakdown, parent, all_values):
    parent_breakdown = constants.get_parent_breakdown(breakdown)

    rows_per_parent_breakdown = collections.defaultdict(list)
    for row in rows:
        parent_br_key = sort_helper.get_breakdown_key(row, parent_breakdown)
        rows_per_parent_breakdown[parent_br_key].append(row)

    if not parent:
        assert len(rows_per_parent_breakdown.keys()) == 1

    for bc in parent or [rows_per_parent_breakdown.keys()[0]]:
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

    start_date = constraints['date__gte']
    end_date = constraints.get('date__lte')
    if end_date is None:
        end_date = constraints['date__lt'] - datetime.timedelta(days=1)

    if time_dimension == constants.TimeDimension.DAY:
        dates = rrule.rrule(rrule.DAILY, start_date, until=end_date)
    elif time_dimension == constants.TimeDimension.WEEK:
        # all weeks in the span starting monday
        dates = rrule.rrule(
            rrule.WEEKLY,
            start_date + relativedelta.relativedelta(weekday=relativedelta.MO(-1)),
            until=end_date, byweekday=rrule.MO)
    else:
        # all months starting 1st
        dates = rrule.rrule(
            rrule.MONTHLY,
            start_date + relativedelta.relativedelta(day=1),
            until=end_date
        )

    return list(x.date() for x in dates)


def set_default_values(breakdown, rows):
    remove_postclicks = constants.get_delivery_dimension(breakdown) is not None

    for row in rows:
        row.update({
            'yesterday_cost': row.get('yesterday_cost') or 0,  # default to 0
            'e_yesterday_cost': row.get('e_yesterday_cost') or 0,
        })

        if remove_postclicks:
            # HACK: Temporary hack that removes postclick data when we breakdown by delivery
            for key in POSTCLICK_FIELDS:
                if key in row:
                    row[key] = None


def postprocess_joint_query_rows(rows):
    for row in rows:
        for column in [x for x in row.keys() if x.startswith('performance_')]:
            # this is specific to joint queries - performance returned needs to be converted to category
            row[column] = dash.campaign_goals.get_goal_performance_category(row[column])


def merge_rows(breakdown, base_rows, yesterday_rows, touchpoint_rows, conversion_rows, goals):
    """
    Applys conversions, pixels and goals columns to rows. Equivalent to what redshiftapi joint model
    does, the only difference is that joint model calculates this in SQL directly.
    """

    rows = base_rows
    rows = stats.helpers.merge_rows(breakdown, base_rows, yesterday_rows)

    # set others to 0
    for row in rows:
        if row.get('yesterday_cost') is None:
            row['yesterday_cost'] = 0
        if row.get('e_yesterday_cost') is None:
            row['e_yesterday_cost'] = 0

    row_by_breakdown = sort_helper.group_rows_by_breakdown_key(breakdown, rows, max_1=True)

    if goals.conversion_goals:
        apply_conversion_goal_columns(breakdown, row_by_breakdown, goals.conversion_goals, conversion_rows)
    if goals.pixels:
        apply_pixel_columns(breakdown, row_by_breakdown, goals.pixels, touchpoint_rows)
    if goals.campaign_goals:
        apply_performance_columns(breakdown, row_by_breakdown, goals.campaign_goals, goals.campaign_goal_values,
                                  goals.conversion_goals, goals.pixels)
    return rows


def apply_conversion_goal_columns(breakdown, row_by_breakdown, conversion_goals, conversion_rows):
    if not conversion_goals:
        return

    conversion_breakdown = breakdown + ['slug']
    conversion_rows_map = sort_helper.group_rows_by_breakdown_key(
        conversion_breakdown, conversion_rows, max_1=True)

    for breakdown_key, row in row_by_breakdown.iteritems():
        for conversion_goal in conversion_goals:
            if conversion_goal.type not in conversions_helper.REPORT_GOAL_TYPES:
                continue

            stats_key = conversion_goal.get_stats_key()

            conversion_breakdown_id = breakdown_key + (stats_key,)
            conversion_row = conversion_rows_map.get(conversion_breakdown_id)

            if conversion_row:
                count = conversion_row['count'] if conversion_row else None
                cost = row['e_media_cost'] or 0

                avg_cost = (float(cost) / count) if count else None
            else:
                count = None
                avg_cost = None

            conversion_key = conversion_goal.get_view_key(conversion_goals)
            row.update({
                conversion_key: count,
                'avg_cost_per_' + conversion_key: avg_cost,
            })


def apply_pixel_columns(breakdown, row_by_breakdown, pixels, touchpoint_rows):
    if not pixels:
        return

    pixel_breakdown = breakdown + ['slug']
    pixel_rows_map = sort_helper.group_rows_by_breakdown_key(pixel_breakdown, touchpoint_rows, max_1=False)

    conversion_windows = sorted(dash.constants.ConversionWindows.get_all())

    for breakdown_key, row in row_by_breakdown.iteritems():
        for pixel in pixels:
            pixel_breakdown_key = breakdown_key + (pixel.slug,)
            pixel_rows = pixel_rows_map.get(pixel_breakdown_key)

            for conversion_window in conversion_windows:

                if pixel_rows:
                    count = sum(x['count'] for x in pixel_rows if x['window'] <= conversion_window)
                    cost = row['e_media_cost'] or 0
                    avg_cost = float(cost) / count if count else None
                else:
                    count = None
                    avg_cost = None

                pixel_key = pixel.get_view_key(conversion_window)

                row.update({
                    pixel_key: count,
                    'avg_cost_per_' + pixel_key: avg_cost,
                })


def apply_performance_columns(breakdown, row_by_breakdown, campaign_goals, campaign_goal_values,
                              conversion_goals, pixels):
    map_camp_goal_vals = {x.campaign_goal_id: x for x in campaign_goal_values or []}
    map_conversion_goals = {x.id: x for x in conversion_goals or []}
    pixel_ids = [x.id for x in pixels] if pixels else []

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

            def metric_value_fn(row):
                return (float(row['e_media_cost'] or 0) / row[conversion_key]) if row.get(conversion_key) else None
        else:
            def metric_value_fn(row):
                return row.get(dash.campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP[campaign_goal.type])

        campaign_goal_value = map_camp_goal_vals.get(campaign_goal.pk)

        if campaign_goal_value and campaign_goal_value.value:
            planned_value = campaign_goal_value.value
        else:
            planned_value = None

        goal_key = campaign_goal.get_view_key()

        for _, row in row_by_breakdown.iteritems():
            cost = row['e_media_cost']
            metric_value = metric_value_fn(row)
            goal_category = dash.campaign_goals.get_goal_performance_status(
                campaign_goal.type, metric_value, planned_value, cost)
            row['performance_' + goal_key] = goal_category
