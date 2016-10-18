import copy
import backtosql

import dash.models
import dash.constants
import dash.campaign_goals

import stats.helpers

from utils import dates_helper

from redshiftapi import newbase_models


def prepare_base_level_query(breakdown, constraints, parents, use_publishers_view=False):
    model = newbase_models.MVMasterPublishers() if (use_publishers_view or 'publisher_id' in breakdown) else newbase_models.MVMaster()
    context = model.get_default_context(breakdown, constraints, parents, use_publishers_view)

    sql = backtosql.generate_sql('newbase_breakdown.sql', context)
    params = context['constraints'].get_params()
    return sql, params


def prepare_base_level_conversions_query(breakdown, constraints, parents, use_publishers_view=False):
    model = newbase_models.MVConversions()
    context = model.get_default_context(breakdown + ['slug'], constraints, parents, use_publishers_view)

    sql = backtosql.generate_sql('newbase_breakdown.sql', context)
    params = context['constraints'].get_params()
    return sql, params


def prepare_base_level_touchpoint_conversions_query(breakdown, constraints, parents, use_publishers_view=False):
    model = newbase_models.MVTouchpointConversions()
    context = model.get_default_context(breakdown + ['slug', 'window'], constraints, parents, use_publishers_view)

    sql = backtosql.generate_sql('newbase_breakdown.sql', context)
    params = context['constraints'].get_params()
    return sql, params


def prepare_base_level_yesterday_spend_query(breakdown, constraints, parents, use_publishers_view=False):
    model = newbase_models.MVMasterYesterday()

    constraints = copy.copy(constraints)
    constraints.pop('date__gte', None)
    constraints.pop('date__lte', None)
    constraints['date'] = dates_helper.local_yesterday()

    context = model.get_default_context(breakdown, constraints, parents, use_publishers_view)

    sql = backtosql.generate_sql('newbase_breakdown.sql', context)
    params = context['constraints'].get_params()
    return sql, params


def calculate_stats(breakdown, base_rows, yesterday_rows,
                    touchpoint_rows, conversion_rows, goals):

    rows = base_rows
    rows = stats.helpers.merge_rows(breakdown, base_rows, yesterday_rows)

    # set others to 0
    for row in rows:
        if row.get('yesterday_cost') is None:
            row['yesterday_cost'] = 0
        if row.get('e_yesterday_cost') is None:
            row['e_yesterday_cost'] = 0

    row_by_breakdown = stats.helpers.group_rows_by_breakdown(breakdown, rows, max_1=True)

    if goals.conversion_goals:
        calc_conversion_goals(breakdown, row_by_breakdown, goals.conversion_goals, conversion_rows)
    if goals.pixels:
        calc_pixel_columns(breakdown, row_by_breakdown, goals.pixels, touchpoint_rows)
    if goals.campaign_goals:
        calc_performance_columns(breakdown, row_by_breakdown, goals.campaign_goals, goals.campaign_goal_values,
                                 goals.conversion_goals, goals.pixels)
    return rows


def calc_conversion_goals(breakdown, row_by_breakdown, conversion_goals, conversion_rows):
    conversion_breakdown = breakdown + ['slug']
    conversion_rows_map = stats.helpers.group_rows_by_breakdown(conversion_breakdown, conversion_rows, max_1=True)

    for breakdown_id, row in row_by_breakdown.iteritems():
        for conversion_goal in conversion_goals:
            conversion_key = conversion_goal.get_view_key(conversion_goals)
            conversion_breakdown_id = breakdown_id + (conversion_key,)

            conversion_row = conversion_rows_map.get(conversion_breakdown_id)

            if conversion_row:
                count = conversion_row['count'] if conversion_row else None
                cost = row['e_media_cost'] or 0

                avg_cost = cost / count if count else None
            else:
                count = None
                avg_cost = None

            row.update({
                conversion_key: count,
                'avg_cost_per_' + conversion_key: avg_cost,
            })


def calc_pixel_columns(breakdown, row_by_breakdown, pixels, touchpoint_rows):
    pixel_breakdown = breakdown + ['slug']
    pixel_rows_map = stats.helpers.group_rows_by_breakdown(pixel_breakdown, touchpoint_rows, max_1=False)

    conversion_windows = sorted(dash.constants.ConversionWindows.get_all())

    for breakdown_id, row in row_by_breakdown.iteritems():
        for pixel in pixels:
            pixel_breakdown_id = breakdown_id + (pixel.slug,)
            pixel_rows = pixel_rows_map.get(pixel_breakdown_id)

            for conversion_window in conversion_windows:

                if pixel_rows:
                    count = sum(x['count'] for x in pixel_rows if x['window'] <= conversion_window)
                    cost = row['e_media_cost'] or 0
                    avg_cost = cost / count if count else None
                else:
                    count = None
                    avg_cost = None

                pixel_key = pixel.get_view_key(conversion_window)

                row.update({
                    pixel_key: count,
                    'avg_cost_per_' + pixel_key: avg_cost,
                })


def calc_performance_columns(breakdown, row_by_breakdown, campaign_goals, campaign_goal_values, conversion_goals, pixels):
    map_camp_goal_vals = {x.campaign_goal_id: x for x in campaign_goal_values or []}
    map_conversion_goals = {x.id: x for x in conversion_goals or []}
    pixel_ids = [x.id for x in pixels] if pixels else []

    category_to_performance = {
        dash.constants.CampaignGoalPerformance.AVERAGE: None,
        dash.constants.CampaignGoalPerformance.UNDERPERFORMING: 0.0,
        dash.constants.CampaignGoalPerformance.SUPERPERFORMING: 1.0,
    }

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
                return (row['e_media_cost'] / row[conversion_key]) if row.get(conversion_key) else None
        else:
            def metric_value_fn(row):
                return row.get(dash.campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP[campaign_goal.type])

        campaign_goal_value = map_camp_goal_vals.get(campaign_goal.pk)
        if campaign_goal_value and campaign_goal_value.value:
            planned_value = campaign_goal_value.value
        else:
            planned_value = None

        goal_key = campaign_goal.get_view_key()

        for breakdown_id, row in row_by_breakdown.iteritems():
            cost = row['e_media_cost']
            metric_value = metric_value_fn(row)
            goal_category = dash.campaign_goals.get_goal_performance_status(
                campaign_goal.type, metric_value, planned_value, cost)
            performance = category_to_performance.get(goal_category)
            row['performance_' + goal_key] = performance
