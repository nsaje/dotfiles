from utils import exc
from utils import sort_helper

import dash.models

from stats import helpers
from stats import constants
from stats import augmenter

import redshiftapi.api_breakdowns


def query(user, breakdown, constraints, breakdown_page,
          order, offset, limit):

    validate_breakdown(breakdown)

    # FIXME: Hack to prevent sorting by fields not available in redshift
    order = get_supported_order(order)

    breakdown = helpers.extract_stats_breakdown(breakdown)
    constraints = helpers.extract_stats_constraints(constraints)

    conversion_goals = get_conversion_goals(breakdown, constraints)

    rows = redshiftapi.api_breakdowns.query(
        breakdown,
        constraints,
        helpers.extract_stats_breakdown_constraints(breakdown, breakdown_page),
        conversion_goals,
        order,
        offset,
        limit)

    target_dimension = constants.get_target_dimension(breakdown)

    augmenter.augment(breakdown, rows, target_dimension)
    augmenter.filter_columns_by_permission(user, rows)

    rows = sort_helper.sort_results(rows, helpers.extract_order_field(order, breakdown))

    return rows


def validate_breakdown(breakdown):
    # translation needed because of inconsistent handling of dimension identifiers
    # TODO needs to be fixed when @greginvm comes back
    breakdown = [constants.get_dimension_identifier(b) for b in breakdown]

    base = constants.get_base_dimension(breakdown)
    if not base:
        raise exc.InvalidBreakdownError("Breakdown requires at least 1 dimension")

    clean_breakdown = [base]
    structure = constants.get_structure_dimension(breakdown)
    if structure:
        clean_breakdown.append(structure)

    delivery = constants.get_delivery_dimension(breakdown)
    if delivery:
        clean_breakdown.append(delivery)

    time = constants.get_time_dimension(breakdown)
    if time:
        clean_breakdown.append(time)

    unsupperted_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupperted_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns {}".format(unsupperted_breakdowns))

    if breakdown != clean_breakdown:
        raise exc.InvalidBreakdownError("Wrong breakdown order")


# FIXME: Remove this hack
def get_supported_order(order):
    UNSUPPORTED_FIELDS = [
        "name", "state", "status", "performance",
        "yesterday_cost", "e_yesterday_cost", "min_bid_cpc",
        "max_bid_cpc", "daily_budget",
    ]

    unprefixed_order = order
    if order.startswith('-'):
        unprefixed_order = order[1:]

    if unprefixed_order in UNSUPPORTED_FIELDS:
        return "-clicks"

    return order


def get_conversion_goals(breakdown, constraints):
    conversion_goals = []

    level = constants.get_level_dimension(constraints)

    if level == 'ad_group_id':
        return dash.models.AdGroup.objects.get(pk=constraints['ad_group_id']).campaign.conversiongoal_set.all()
    elif level == 'campaign_id':
        return dash.models.Campaign.objects.get(pk=constraints['campaign_id']).conversiongoal_set.all()

    return []
