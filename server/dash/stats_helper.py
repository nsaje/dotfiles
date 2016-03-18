from collections import OrderedDict

import reports.api
import reports.api_contentads
import reports.api_helpers
import reports.api_touchpointconversions
import utils.sort_helper
from dash import conversions_helper, constants
from reports import api_touchpointconversions, api_publishers
from utils import sort_helper


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


def get_publishers_data_and_conversion_goals(
        user,
        query_func,
        start_date,
        end_date,
        constraints,
        conversion_goals,
        publisher_breakdown_fields=[],
        touchpoint_breakdown_fields=[],
        order_fields=[],
        show_blacklisted_publishers=None,
        adg_blacklisted_publishers=None):
    can_see_conversion_goals = user.has_perm('zemauth.view_pubs_conversion_goals')

    report_conversion_goals = []
    touchpoint_conversion_goals = []
    if can_see_conversion_goals:
        report_conversion_goals = [cg for cg in conversion_goals if cg.type in conversions_helper.REPORT_GOAL_TYPES]
        touchpoint_conversion_goals = [cg for cg in conversion_goals if cg.type == conversions_helper.PIXEL_GOAL_TYPE]

    publishers_data = _get_publishers_data(query_func,
                                           start_date,
                                           end_date,
                                           publisher_breakdown_fields,
                                           order_fields,
                                           report_conversion_goals,
                                           constraints,
                                           show_blacklisted_publishers,
                                           adg_blacklisted_publishers)

    if publishers_data and can_see_conversion_goals:
        touchpoint_data = _get_conversion_goals(start_date,
                                                end_date,
                                                touchpoint_breakdown_fields,
                                                touchpoint_conversion_goals,
                                                constraints,
                                                show_blacklisted_publishers,
                                                adg_blacklisted_publishers)
        publishers_data = _transform_and_merge_conversion_goals(publishers_data,
                                                                touchpoint_data,
                                                                publisher_breakdown_fields,
                                                                touchpoint_breakdown_fields,
                                                                conversion_goals,
                                                                order_fields)
    return publishers_data


def _get_publishers_data(query_func,
                         start_date,
                         end_date,
                         publisher_breakdown_fields,
                         order_fields,
                         report_conversion_goals,
                         constraints,
                         show_blacklisted_publishers,
                         adg_blacklisted_publishers):
    publisher_constraints_list = []
    if show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ACTIVE:
        publisher_constraints_list = reports.api_publishers.prepare_active_publishers_constraint_list(
            adg_blacklisted_publishers, False)
    elif show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_BLACKLISTED:
        publisher_constraints_list = api_publishers.prepare_blacklisted_publishers_constraint_list(
            adg_blacklisted_publishers, publisher_breakdown_fields, False)

    publishers_data = query_func(
        start_date, end_date,
        breakdown_fields=publisher_breakdown_fields,
        order_fields=order_fields,
        conversion_goals=[cg.get_stats_key() for cg in report_conversion_goals],
        constraints=constraints,
        constraints_list=publisher_constraints_list,
    )
    return publishers_data


def _get_conversion_goals(start_date,
                          end_date,
                          touchpoint_breakdown_fields,
                          touchpoint_conversion_goals,
                          constraints,
                          show_blacklisted_publishers,
                          adg_blacklisted_publishers):
    touchpoint_constraints_list = []
    if show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_ACTIVE:
        touchpoint_constraints_list = reports.api_publishers.prepare_active_publishers_constraint_list(
            adg_blacklisted_publishers, True)
    elif show_blacklisted_publishers == constants.PublisherBlacklistFilter.SHOW_BLACKLISTED:
        touchpoint_constraints_list = api_publishers.prepare_blacklisted_publishers_constraint_list(
            adg_blacklisted_publishers, touchpoint_breakdown_fields, True)

    touchpoint_data = api_touchpointconversions.query(
            start_date, end_date,
            breakdown=touchpoint_breakdown_fields,
            conversion_goals=touchpoint_conversion_goals,
            constraints=constraints,
            constraints_list=touchpoint_constraints_list,
    )
    return touchpoint_data


def _transform_and_merge_conversion_goals(publishers_data,
                                          touchpoint_data,
                                          publisher_breakdown_fields,
                                          touchpoint_breakdown_fields,
                                          conversion_goals,
                                          order_fields):
    merged_data, reorder = conversions_helper.merge_touchpoint_conversions_to_publishers_data(
        publishers_data,
        touchpoint_data,
        publisher_breakdown_fields,
        touchpoint_breakdown_fields)
    conversions_helper.transform_to_conversion_goals(merged_data, conversion_goals)

    if reorder:
        merged_data = sort_helper.sort_results(merged_data, order_fields)
    return merged_data


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
    if can_see_conversions:
        conversions_helper.transform_to_conversion_goals(ca_stats_by_breakdown.values(), conversion_goals)

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
