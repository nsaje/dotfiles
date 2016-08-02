from utils import exc
from utils import sort_helper

import dash.models
import dash.campaign_goals

from reports.db_raw_helpers import is_collection

from stats import helpers
from stats import constants
from stats import augmenter
from stats import permission_filter

import redshiftapi.api_breakdowns


def query(user, breakdown, constraints, breakdown_page,
          order, offset, limit):

    """
    Get a breakdown report. Data is sourced from dash models and redshiftapi.

    All field names and values in breakdown, constraints, breakdown_page and order should
    use valid field names. Field names should match those of used dash and redshiftapi models.

    All values in constraints and breakdown_page should be object ids.
    """

    permission_filter.update_allowed_objects_constraints(user, breakdown, constraints)
    permission_filter.check_breakdown_allowed(user, breakdown)

    validate_breakdown(breakdown)
    validate_constraints(constraints)

    # FIXME: Hack to prevent sorting by fields not available in redshift
    order = get_supported_order(order)

    constraints = helpers.extract_stats_constraints(constraints)
    conversion_goals, campaign_goal_values = get_goals(breakdown, constraints)

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
    permission_filter.filter_columns_by_permission(user, rows, campaign_goal_values, conversion_goals)

    rows = sort_helper.sort_results(rows, [helpers.extract_order_field(order, breakdown)])

    return rows


def validate_breakdown(breakdown):
    base = constants.get_base_dimension(breakdown)
    if not base:
        return

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


def validate_constraints(constraints):
    for k, v in constraints.iteritems():
        if constants.get_dimension_identifier(k) != k:
            raise exc.UnknownFieldBreakdownError("Unknown dimension identifier '{}'".format(k))


# FIXME: Remove this hack
def get_supported_order(order):
    UNSUPPORTED_FIELDS = [
        "name", "state", "status", "performance",
        "min_bid_cpc", "max_bid_cpc", "daily_budget",
        "pacing", "allocated_budgets", "spend_projection",
        "license_fee_projection", "upload_time",
    ]

    unprefixed_order = order
    if order.startswith('-'):
        unprefixed_order = order[1:]

    if unprefixed_order in UNSUPPORTED_FIELDS:
        return "-clicks"

    return order


def get_goals(breakdown, constraints):
    campaign = None

    if constants.StructureDimension.AD_GROUP in constraints and not is_collection(constraints['ad_group_id']):
        campaign = dash.models.AdGroup.objects.get(
            pk=constraints['ad_group_id']).campaign

    elif constants.StructureDimension.CAMPAIGN in constraints and not is_collection(constraints['campaign_id']):
        campaign = dash.models.Campaign.objects.get(
            pk=constraints['campaign_id'])

    conversion_goals, campaign_goal_values = [], []
    if campaign:
        conversion_goals = campaign.conversiongoal_set.all()
        campaign_goal_values = dash.campaign_goals.get_campaign_goal_values(campaign)

    return conversion_goals, campaign_goal_values
