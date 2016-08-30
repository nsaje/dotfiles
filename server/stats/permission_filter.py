from reports import api_helpers

import dash.campaign_goals
import dash.models
from dash.constants import Level
from dash.views.helpers import get_account, get_ad_group, get_campaign

from utils import exc

from stats import constants
from stats.constants import StructureDimension, DeliveryDimension, TimeDimension


DIMENSION_FIELDS = set(StructureDimension._ALL) | set(DeliveryDimension._ALL) | set(TimeDimension._ALL)
DIMENSION_FIELDS |= set(constants.SpecialDimensionNameKeys.values())
DIMENSION_FIELDS |= set([
    'url', 'title',
    'breakdown_name', 'breakdown_id', 'parent_breakdown_id',
])

DEFAULT_STATS = set([
    'ctr', 'cpc', 'clicks', 'impressions', 'billing_cost', 'cpm',
])

DEFAULT_FIELDS = DIMENSION_FIELDS | DEFAULT_STATS


def filter_columns_by_permission(user, rows, campaign_goal_values, conversion_goals, pixels):
    fields_to_keep = list(DEFAULT_FIELDS)

    fields_to_keep.extend(api_helpers.get_fields_to_keep(user))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_campaign_goals_fields(
        user, campaign_goal_values, conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_conversion_goals_fields(
        user, conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_pixels_fields(pixels))

    api_helpers.remove_fields(rows, fields_to_keep)


def update_allowed_objects_constraints(user, breakdown, constraints):
    """
    Sets constraints so that only objects for which user has proper permissions get queried.
    In case constraints are set to query objects that are not allowed an error gets raised.

    This function also sets parent objects.

    NOTE: we expect an abject for whom we demand a breakdown is already checked and allowed.
    """

    filtered_sources = constraints['filtered_sources']
    filtered_agencies = constraints.get('filtered_agencies')
    filtered_account_types = constraints.get('filtered_account_types')

    # these 2 queries do not get evaluated until they are converted into a list
    allowed_accounts = dash.models.Account.objects.all()\
                                                  .filter_by_user(user)\
                                                  .filter_by_sources(filtered_sources)\
                                                  .filter_by_agencies(filtered_agencies)\
                                                  .filter_by_account_types(filtered_account_types)

    allowed_campaigs = dash.models.Campaign.objects.all()\
                                                   .filter_by_user(user)\
                                                   .filter_by_sources(filtered_sources)\
                                                   .filter_by_agencies(filtered_agencies)\
                                                   .filter_by_account_types(filtered_account_types)

    if not any(key in ('account', 'campaign', 'ad_group') for key in constraints.keys()):
        constraints['allowed_accounts'] = allowed_accounts

        if StructureDimension.CAMPAIGN in breakdown:
            # When campaign breakdown is a part of requested breakdown
            # we need to limit that only to allowed campaigns.
            # Mind that this sets the structure level lower.
            constraints['allowed_campaigns'] = allowed_campaigs

    elif 'ad_group' in constraints.keys():
        ad_group = constraints['ad_group']
        constraints['campaign'] = ad_group.campaign
        constraints['account'] = ad_group.campaign.account

    elif 'campaign' in constraints.keys():
        campaign = constraints['campaign']
        constraints['account'] = campaign.account

    elif 'account' in constraints.keys():
        constraints['allowed_campaigns'] = allowed_campaigs
    else:
        # invalid level
        raise exc.MissingDataError()

    return constraints


def validate_breakdown_by_permissions(level, user, breakdown):
    base_dimension = constants.get_base_dimension(breakdown)

    if level == Level.ALL_ACCOUNTS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.ACCOUNT):
            raise exc.MissingDataError(1)
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.all_accounts_sources_view'):
            raise exc.MissingDataError(2)
        if base_dimension == StructureDimension.ACCOUNT and not user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError(3)

    elif level == Level.ACCOUNTS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.CAMPAIGN):
            raise exc.MissingDataError(4)
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.account_sources_view'):
            raise exc.MissingDataError(5)
        if base_dimension == StructureDimension.CAMPAIGN and not user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError(6)

    elif level == Level.CAMPAIGNS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.AD_GROUP):
            raise exc.MissingDataError(7)

    elif level == Level.AD_GROUPS:
        if base_dimension not in (
                StructureDimension.SOURCE, StructureDimension.CONTENT_AD, StructureDimension.PUBLISHER):
            raise exc.MissingDataError(8)

    if StructureDimension.PUBLISHER in breakdown and not user.has_perm('zemauth.can_see_publishers'):
        raise exc.MissingDataError(9)

    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if delivery_dimension is not None and not user.has_perm('zemauth.can_view_breakdown_by_delivery'):
        raise exc.MissingDataError(10)


def validate_breakdown_by_structure(breakdown):
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
