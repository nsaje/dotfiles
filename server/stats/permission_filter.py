from reports import api_helpers

import dash.campaign_goals
import dash.models
from dash.views.helpers import get_account, get_ad_group, get_campaign

from utils import exc

from stats import constants


DIMENSION_FIELDS = set(constants.StructureDimension._ALL) | set(constants.DeliveryDimension._ALL) | set(constants.TimeDimension._ALL)
DIMENSION_FIELDS |= set(constants.SpecialDimensionNameKeys.values())
DIMENSION_FIELDS |= set([
    'url', 'title',
    'breakdown_name', 'breakdown_id', 'parent_breakdown_id',
])

DEFAULT_STATS = set([
    'cost', 'ctr', 'cpc', 'clicks', 'impressions',
])

DEFAULT_FIELDS = DIMENSION_FIELDS | DEFAULT_STATS


def filter_columns_by_permission(user, rows, campaign_goal_values, conversion_goals):
    fields_to_keep = list(DEFAULT_FIELDS)

    fields_to_keep.extend(api_helpers.get_fields_to_keep(user))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_campaign_goals_fields(
        user, campaign_goal_values, conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_conversion_goals_fields(
        user, conversion_goals
    ))

    api_helpers.remove_fields(rows, fields_to_keep)


def update_allowed_objects_constraints(user, breakdown, constraints):
    """
    Sets constraints so that only objects for which user has proper permissions get queried.
    In case constraints are set to query objects that are not allowed an error gets raised.

    By default we expect that single object id is to the level dimension (account_id, campaign_id ...).
    """

    level_dimension = constants.get_lowest_level_structure_dimension(constraints)

    if level_dimension is None:
        allowed_account_ids = dash.models.Account.objects.all().filter_by_user(user).values_list('id', flat=True)
        constraints['account_id'] = allowed_account_ids

        # when campaign breakdown is a part of requested breakdown we need to limit that only to allowed
        # campaigns
        if constants.StructureDimension.CAMPAIGN in breakdown:
            allowed_campaig_ids = dash.models.Campaign.objects.all().filter_by_user(user).values_list('id', flat=True)

            # mind that this sets the structure level lower
            constraints['campaign_id'] = allowed_campaig_ids

    elif level_dimension == constants.StructureDimension.ACCOUNT:
        account = get_account(user, constraints['account_id'])
        constraints['account_id'] = account.id

        allowed_campaig_ids = dash.models.Campaign.objects.all().filter_by_user(user).values_list('id', flat=True)
        constraints['campaign_id'] = allowed_campaig_ids

    elif level_dimension == constants.StructureDimension.CAMPAIGN:
        campaign = get_campaign(user, constraints['campaign_id'])
        constraints['campaign_id'] = campaign.id
        constraints['account_id'] = campaign.account_id

    elif level_dimension == constants.StructureDimension.AD_GROUP:
        ad_group = get_ad_group(user, constraints['ad_group_id'], select_related=True)
        constraints['ad_group_id'] = ad_group.id
        constraints['campaign_id'] = ad_group.campaign_id
        constraints['account_id'] = ad_group.campaign.account_id
    else:
        # invalid level
        raise exc.MissingDataError()

    return constraints


def check_breakdown_allowed(user, breakdown):
    target_dimension = constants.get_target_dimension(breakdown)

    if (target_dimension == constants.StructureDimension.PUBLISHER and not user.has_perm('zemauth.can_see_publishers')):
        raise exc.MissingDataError()
