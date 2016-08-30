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


def validate_breakdown_allowed(level, user, breakdown):
    permission_filter.validate_breakdown_by_structure(breakdown)
    permission_filter.validate_breakdown_by_permissions(level, user, breakdown)


def query(level, user, breakdown, constraints, parents, order, offset, limit):
    """
    Get a breakdown report. Data is sourced from dash models and redshift.

    All field names and values in breakdown, constraints, parents and order should
    use valid field names. Field names should match those of used in dash and redshiftapi models.
    """

    permission_filter.update_allowed_objects_constraints(user, breakdown, constraints)
    helpers.check_constraints_are_supported(constraints)

    order = helpers.get_supported_order(helpers.extract_order_field(order, breakdown))
    parents = helpers.decode_parents(breakdown, parents)

    conversion_goals, campaign_goal_values, pixels = get_goals(breakdown, constraints)

    rows = redshiftapi.api_breakdowns.query(
        breakdown,
        helpers.extract_stats_constraints(constraints),
        parents,
        conversion_goals,
        pixels,
        order,
        offset,
        limit)

    """
    TODO when fields get replaced with augmented values their sorted position might change
    and this can lead to duplicated and missed items in "load more" requests when we request
    number of items + offset.
    Example: Ad group ids in DB: 1, 2, 3, 4 (by name: 1, 3, 4, 2)
            Request first 2 + overflow: 1, 2, 3
            Order by name: 1, 3, 2
            Cut overflow: 1, 3
            Load more, offset 2: 3, 4
            Resulting collection: 1, 3, 3, 4
    Possible solutions: cut overflow before sorting and report the count, order before augmentation (current solution)
    """

    rows = sort_helper.sort_results(rows, [order])

    augmenter.augment(breakdown, rows, constants.get_target_dimension(breakdown))
    permission_filter.filter_columns_by_permission(user, rows, campaign_goal_values, conversion_goals, pixels)

    return rows


def get_goals(breakdown, constraints):

    campaign = constraints.get('campaign')
    account = constraints.get('account')

    conversion_goals, campaign_goal_values, pixels = [], [], []
    if campaign:
        conversion_goals = campaign.conversiongoal_set.all()
        campaign_goal_values = dash.campaign_goals.get_campaign_goal_values(campaign)

    if account:
        pixels = account.conversionpixel_set.filter(archived=False)

    return conversion_goals, campaign_goal_values, pixels
