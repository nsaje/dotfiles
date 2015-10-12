from collections import OrderedDict

from dash import constants

import reports.api
import reports.api_helpers
import reports.api_contentads
import reports.api_touchpointconversions


def get_reports_api_module(user):
    if user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
        return reports.api_contentads
    else:
        return reports.api


def get_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=None,
        order=None,
        ignore_diff_rows=False,
        conversion_goals=None,
        constraints=None):
    can_see_redshift_stats = user.has_perm('zemauth.can_see_redshift_postclick_statistics')
    can_see_conversions = can_see_redshift_stats and user.has_perm('zemauth.conversion_reports')

    if conversion_goals is None:
        conversion_goals = []

    if breakdown is None:
        breakdown = []

    if order is None:
        order = []

    if constraints is None:
        constraints = {}

    report_conversion_goals = []
    touchpoint_conversion_goals = []
    if can_see_conversions:
        report_conversion_goals = [cg for cg in conversion_goals if cg.type != constants.ConversionGoalType.PIXEL]
        touchpoint_conversion_goals = [cg for cg in conversion_goals if cg.type == constants.ConversionGoalType.PIXEL]

    content_ad_stats = reports.api_helpers.filter_by_permissions(reports.api_contentads.query(
        start_date,
        end_date,
        order=order,
        breakdown=breakdown,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=[cg.get_stats_key() for cg in report_conversion_goals],
        **constraints), user)

    if not breakdown:
        content_ad_stats = [content_ad_stats]

    # use ordered dict to retain order from db
    ca_stats_by_breakdown = OrderedDict((tuple(s[b] for b in breakdown), s) for s in content_ad_stats)
    for ca_stat in ca_stats_by_breakdown.values():
        for conversion_goal in report_conversion_goals:
            key = conversion_goal.get_stats_key()
            ca_stat['conversion_goal_' + str(conversion_goal.id)] = ca_stat.get('conversions', {}).get(key)

    if not can_see_conversions or not touchpoint_conversion_goals:
        result = ca_stats_by_breakdown.values()
        if breakdown:
            return result

        return result[0]

    touchpoint_conversion_stats = reports.api_touchpointconversions.query(
        start_date,
        end_date,
        order=order,
        breakdown=breakdown + ['slug'],
        conversion_goals=touchpoint_conversion_goals,
        constraints=constraints
    )

    # add touchpoint conversions to existing content ad stats
    tp_conv_stats_by_breakdown = OrderedDict((tuple(s[b] for b in breakdown), s) for s in touchpoint_conversion_stats)
    for key, ca_stat in ca_stats_by_breakdown.iteritems():
        for conversion_goal in touchpoint_conversion_goals:
            tp_conv_key = tuple(list(key) + [conversion_goal.pixel.slug])
            ca_stat['conversion_goal_' + str(conversion_goal.id)] = None
            if tp_conv_key in tp_conv_stats_by_breakdown:
                ca_stat['conversion_goal_' + str(conversion_goal.id)] = tp_conv_stats_by_breakdown[tp_conv_key]

    # add rows that are only in touchpoint conversion stats to content ad stats
    for tp_conv_stat in touchpoint_conversion_stats:
        key = tuple(tp_conv_stat[b] for b in breakdown)
        if key in ca_stats_by_breakdown:
            continue

        ca_stats_by_breakdown[key] = {b: tp_conv_stat[b] for b in breakdown}
        ca_stat = ca_stats_by_breakdown[key]

        conversion_goal = conversion_goals.get(pixel__slug=tp_conv_stat['slug'])
        ca_stat['conversion_goal_' + str(conversion_goal.id)] = tp_conv_stat['conversion_count']

    result = ca_stats_by_breakdown.values()
    if breakdown:
        return result

    return result[0]
