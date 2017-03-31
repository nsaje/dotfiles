from reports import api_helpers

import dash.campaign_goals
import dash.models
from dash.constants import Level

from utils import exc

from stats import constants
from stats.helpers import CONTENT_ADS_FIELDS, SOURCE_FIELDS, PUBLISHER_FIELDS
from stats.constants import StructureDimension, DeliveryDimension, TimeDimension


DIMENSION_FIELDS = set(StructureDimension._ALL) | set(DeliveryDimension._ALL) | set(TimeDimension._ALL)
DIMENSION_FIELDS |= set([
    'name', 'status', 'state', 'archived',
    'account', 'campaign', 'ad_group', 'content_ad', 'source', 'publisher',
    'account_status', 'campaign_status', 'ad_group_status', 'content_ad_status',
    'source_status', 'publisher_status',
    'breakdown_name', 'breakdown_id', 'parent_breakdown_id',
])

# content ad fields
DIMENSION_FIELDS |= set(CONTENT_ADS_FIELDS)

DEFAULT_STATS = set([
    'ctr', 'cpc', 'clicks', 'impressions', 'billing_cost', 'cpm',
])

HELPER_FIELDS = set(['campaign_stop_inactive', 'campaign_has_available_budget', 'status_per_source'])

DEFAULT_FIELDS = DIMENSION_FIELDS | DEFAULT_STATS | set(SOURCE_FIELDS) | HELPER_FIELDS | set(PUBLISHER_FIELDS)


def filter_columns_by_permission(user, rows, goals):
    fields_to_keep = list(DEFAULT_FIELDS)

    fields_to_keep.extend(api_helpers.get_fields_to_keep(user))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_campaign_goals_fields(
        user, goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_conversion_goals_fields(
        user, goals.conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_pixels_fields(goals.pixels))

    api_helpers.remove_fields(rows, fields_to_keep)
    api_helpers.custom_cleanup(user, rows)


def validate_breakdown_by_permissions(level, user, breakdown):
    base_dimension = constants.get_base_dimension(breakdown)

    if level == Level.ALL_ACCOUNTS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.ACCOUNT):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.all_accounts_sources_view'):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.ACCOUNT and not user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

    elif level == Level.ACCOUNTS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.CAMPAIGN):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.account_sources_view'):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.CAMPAIGN and not user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError()

    elif level == Level.CAMPAIGNS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.AD_GROUP):
            raise exc.MissingDataError()

    elif level == Level.AD_GROUPS:
        if base_dimension not in (
                StructureDimension.SOURCE, StructureDimension.CONTENT_AD, StructureDimension.PUBLISHER):
            raise exc.MissingDataError()

    if StructureDimension.PUBLISHER in breakdown and not user.has_perm('zemauth.can_see_publishers'):
        raise exc.MissingDataError()

    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if delivery_dimension is not None and not user.has_perm('zemauth.can_view_breakdown_by_delivery'):
        raise exc.MissingDataError()


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

    if 'publisher_id' in breakdown and 'source_id' in breakdown:
        raise exc.InvalidBreakdownError("Unsupported breakdown - publishers are broken down by source by default")

    unsupperted_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupperted_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns: {}".format(', '.join(unsupperted_breakdowns)))

    if breakdown != clean_breakdown:
        raise exc.InvalidBreakdownError("Wrong breakdown order")
