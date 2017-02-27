from collections import OrderedDict

import reports.api
import reports.api_contentads
import reports.api_helpers
import utils.sort_helper
from dash import conversions_helper, constants
from reports import api_touchpointconversions


def get_reports_api_module(can_see_redshift_stats):
    if can_see_redshift_stats:
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
        pixels=None,
        constraints=None,
        filter_by_permissions=True):
    can_see_redshift_stats = not filter_by_permissions or user.has_perm('zemauth.can_see_redshift_postclick_statistics')
    can_see_conversions = not filter_by_permissions or can_see_redshift_stats

    return _get_stats_with_conversions(
        user,
        can_see_redshift_stats,
        can_see_conversions,
        start_date,
        end_date,
        breakdown=breakdown,
        order=order,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        pixels=pixels,
        constraints=constraints,
        filter_by_permissions=filter_by_permissions,
    )


def get_content_ad_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=None,
        order=None,
        ignore_diff_rows=False,
        conversion_goals=None,
        pixels=None,
        constraints=None):
    # a workaround for content ads tab where all users can see redshift stats
    can_see_redshift_stats = True
    can_see_conversions = True

    return _get_stats_with_conversions(
        user,
        can_see_redshift_stats,
        can_see_conversions,
        start_date,
        end_date,
        breakdown=breakdown,
        order=order,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        pixels=pixels,
        constraints=constraints
    )


def _get_stats_with_conversions(
        user,
        can_see_redshift_stats,
        can_see_conversions,
        start_date,
        end_date,
        breakdown=None,
        order=None,
        ignore_diff_rows=False,
        conversion_goals=None,
        pixels=None,
        constraints=None,
        filter_by_permissions=True):

    if conversion_goals is None:
        conversion_goals = []

    if breakdown is None:
        breakdown = []

    if order is None:
        order = []

    if constraints is None:
        constraints = {}

    report_conversion_goals = []
    if can_see_conversions:
        report_conversion_goals = [cg for cg in conversion_goals if cg.type in conversions_helper.REPORT_GOAL_TYPES]

    reports_api = get_reports_api_module(can_see_redshift_stats)
    content_ad_stats = reports_api.query(
        start_date,
        end_date,
        order=order,
        breakdown=breakdown,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=[cg.get_stats_key() for cg in report_conversion_goals],
        **constraints)
    if filter_by_permissions:
        content_ad_stats = reports.api_helpers.filter_by_permissions(content_ad_stats, user)

    if not breakdown:
        content_ad_stats = [content_ad_stats]

    ca_stats_by_breakdown = OrderedDict((tuple(s[b] for b in breakdown), s) for s in content_ad_stats)

    if not pixels:
        result = ca_stats_by_breakdown.values()
        conversions_helper.transform_to_conversion_goals(result, conversion_goals, pixels)
        if breakdown:
            return result

        return result[0]

    touchpoint_conversion_stats = api_touchpointconversions.query(
        start_date,
        end_date,
        breakdown=breakdown,
        pixels=pixels,
        constraints=constraints
    )

    for tp_conv_stat in touchpoint_conversion_stats:
        row_key = tuple(tp_conv_stat[b] for b in breakdown)

        ca_stat = ca_stats_by_breakdown.get(row_key)
        if ca_stat is None:
            ca_stat = {b: tp_conv_stat[b] for b in breakdown}

        for conversion_window in constants.ConversionWindows.get_all():
            pixel_key = (tp_conv_stat['slug'], tp_conv_stat['account'], conversion_window)
            ca_stat.setdefault('conversions', {})
            ca_stat['conversions'][pixel_key] = tp_conv_stat['conversion_count_' + str(conversion_window)]
            ca_stats_by_breakdown[row_key] = ca_stat

    result = ca_stats_by_breakdown.values()
    conversions_helper.transform_to_conversion_goals(result, conversion_goals, pixels)

    if order:
        # sorting needed since it's a join of data from two tables
        result = utils.sort_helper.sort_results(result, order_fields=order)

    if breakdown:
        return result

    return result[0]
