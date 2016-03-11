from collections import OrderedDict

import reports.api
import reports.api_contentads
import reports.api_helpers
import reports.api_touchpointconversions
import utils.sort_helper
from dash import conversions_helper


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
        constraints=None):
    can_see_redshift_stats = user.has_perm('zemauth.can_see_redshift_postclick_statistics')
    can_see_conversions = can_see_redshift_stats and user.has_perm('zemauth.conversion_reports')

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
        constraints=constraints
    )


def get_content_ad_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=None,
        order=None,
        ignore_diff_rows=False,
        conversion_goals=None,
        constraints=None):
    # a workaround for content ads tab where all users can see redshift stats
    can_see_redshift_stats = True
    can_see_conversions = can_see_redshift_stats and user.has_perm('zemauth.conversion_reports')

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
        constraints=constraints
    )


def get_publishers_data_and_conversion_goals(user, query_func, start_date, end_date, constraints,
                                             conversion_goals, total, publisher_breakdown_fields=[],
                                             touchpoint_breakdown_fields=[], order_fields=[], constraints_list=None):
    report_conversion_goals = []
    touchpoint_conversion_goals = []
    if user.has_perm('zemauth.view_pubs_conversion_goals'):
        report_conversion_goals = [cg for cg in conversion_goals if cg.type in conversions_helper.REPORT_GOAL_TYPES]
        touchpoint_conversion_goals = [cg for cg in conversion_goals if cg.type == conversions_helper.PIXEL_GOAL_TYPE]

    if constraints_list is None:
        publishers_data = query_func(
            start_date, end_date,
            breakdown_fields=publisher_breakdown_fields,
            order_fields=order_fields,
            constraints=constraints,
            conversion_goals=[cg.get_stats_key() for cg in report_conversion_goals],
        )
        # touchpoint_data = api_touchpointconversions.query(
        #     start_date, end_date,
        #     breakdown=touchpoint_breakdown_fields,
        #     conversion_goals=touchpoint_conversion_goals,
        #     constraints=constraints,
        # )
    else:
        publishers_data = query_func(
            start_date, end_date,
            breakdown_fields=publisher_breakdown_fields,
            order_fields=order_fields,
            constraints=constraints,
            conversion_goals=[cg.get_stats_key() for cg in report_conversion_goals],
            constraints_list=constraints_list,
        )
        # touchpoint_data = api_touchpointconversions.query(
        #     start_date, end_date,
        #     breakdown=touchpoint_breakdown_fields,
        #     conversion_goals=touchpoint_conversion_goals,
        #     constraints=constraints,
        #     constraints_list=constraints_list,
        # )

    # if total:
    #     merge_touchpoint_conversion_to_publishers_for_total(publishers_data[0], touchpoint_data)
    # else:
    #     merge_touchpoint_conversions_to_publishers_data(publishers_data, touchpoint_data)

    conversions_helper.transform_conversion_goals(publishers_data, conversion_goals)

    return publishers_data


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
        constraints=None):

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
        report_conversion_goals = [cg for cg in conversion_goals if cg.type in conversions_helper.REPORT_GOAL_TYPES]
        touchpoint_conversion_goals = [cg for cg in conversion_goals if cg.type == conversions_helper.PIXEL_GOAL_TYPE]

    reports_api = get_reports_api_module(can_see_redshift_stats)
    content_ad_stats = reports.api_helpers.filter_by_permissions(reports_api.query(
        start_date,
        end_date,
        order=order,
        breakdown=breakdown,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=[cg.get_stats_key() for cg in report_conversion_goals],
        **constraints), user)

    if not breakdown:
        content_ad_stats = [content_ad_stats]

    ca_stats_by_breakdown = OrderedDict((tuple(s[b] for b in breakdown), s) for s in content_ad_stats)
    for ca_stat in ca_stats_by_breakdown.values():
        for conversion_goal in report_conversion_goals:
            key = conversion_goal.get_stats_key()
            ca_stat[conversion_goal.get_view_key(conversion_goals)] = ca_stat.get('conversions', {}).get(key)

        for tp_conversion_goal in touchpoint_conversion_goals:
            # set the default - if tp_conv_stats result won't contain value, assume it's 0
            ca_stat[tp_conversion_goal.get_view_key(conversion_goals)] = 0

        if 'conversions' in ca_stat:
            # mapping done, this is not needed anymore
            del ca_stat['conversions']

    if not can_see_conversions or not touchpoint_conversion_goals:
        result = ca_stats_by_breakdown.values()
        if breakdown:
            return result

        return result[0]

    touchpoint_conversion_stats = reports.api_touchpointconversions.query(
        start_date,
        end_date,
        breakdown=breakdown,
        conversion_goals=touchpoint_conversion_goals,
        constraints=constraints
    )

    tp_conv_goals_by_slug = {(cg.pixel.slug, cg.pixel.account_id): cg for cg in touchpoint_conversion_goals}
    for tp_conv_stat in touchpoint_conversion_stats:
        key = tuple(tp_conv_stat[b] for b in breakdown)
        conversion_goal = tp_conv_goals_by_slug[(tp_conv_stat['slug'], tp_conv_stat['account'])]

        if key in ca_stats_by_breakdown:
            ca_stats_by_breakdown[key][conversion_goal.get_view_key(conversion_goals)] = tp_conv_stat['conversion_count']
            continue

        ca_stat = {b: tp_conv_stat[b] for b in breakdown}
        ca_stat[conversion_goal.get_view_key(conversion_goals)] = tp_conv_stat['conversion_count']
        ca_stats_by_breakdown[key] = ca_stat

    result = ca_stats_by_breakdown.values()

    if order:
        # sorting needed since it's a join of data from two tables
        result = utils.sort_helper.sort_results(result, order_fields=order)

    if breakdown:
        return result

    return result[0]
