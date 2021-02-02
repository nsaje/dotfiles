import concurrent.futures
from collections import defaultdict

import dash.campaign_goals
import dash.models
from dash.constants import CampaignGoalKPI
from dash.constants import Level
from stats import constants
from stats import fields
from stats.constants import StructureDimension
from stats.constants import is_extended_delivery_dimension
from stats.constants import is_top_level_delivery_dimension
from utils import exc
from zemauth.features.entity_permission import Permission

FIELD_PERMISSION_MAPPING = {
    # costs
    "media_cost": ("zemauth.can_view_actual_costs",),
    "local_media_cost": ("zemauth.can_view_actual_costs",),
    "data_cost": ("zemauth.can_view_actual_costs",),
    "local_data_cost": ("zemauth.can_view_actual_costs",),
    "at_cost": ("zemauth.can_view_actual_costs",),
    "local_at_cost": ("zemauth.can_view_actual_costs",),
    "et_cost": ("zemauth.can_view_platform_cost_breakdown_derived",),
    "local_et_cost": ("zemauth.can_view_platform_cost_breakdown_derived",),
    "yesterday_at_cost": ("zemauth.can_view_actual_costs",),
    "local_yesterday_at_cost": ("zemauth.can_view_actual_costs",),
    # other
    "default_account_manager": ("zemauth.can_see_managers_in_accounts_table",),
    "default_sales_representative": ("zemauth.can_see_managers_in_accounts_table",),
    "default_cs_representative": ("zemauth.can_see_managers_in_accounts_table",),
    "ob_sales_representative": ("zemauth.can_see_managers_in_accounts_table",),
    "ob_account_manager": ("zemauth.can_see_managers_in_accounts_table",),
    "campaign_manager": ("zemauth.can_see_managers_in_campaigns_table",),
    "account_type": ("zemauth.can_see_account_type",),
    "salesforce_url": ("zemauth.can_see_salesforce_url",),
    "sspd_url": ("zemauth.can_see_sspd_url",),
    # entity tags
    "agency_tags": ("zemauth.can_include_tags_in_reports",),
    "account_tags": ("zemauth.can_include_tags_in_reports",),
    "campaign_tags": ("zemauth.can_include_tags_in_reports",),
    "ad_group_tags": ("zemauth.can_include_tags_in_reports",),
    "source_tags": ("zemauth.can_include_tags_in_reports",),
    # viewability fields
    "mrc100_measurable": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_viewable": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_non_measurable": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_non_viewable": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_measurable_percent": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_viewable_percent": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_viewable_distribution": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_non_measurable_distribution": ("zemauth.can_see_mrc100_metrics",),
    "mrc100_non_viewable_distribution": ("zemauth.can_see_mrc100_metrics",),
    "etfm_mrc100_vcpm": ("zemauth.can_see_mrc100_metrics",),
    "local_etfm_mrc100_vcpm": ("zemauth.can_see_mrc100_metrics",),
    "vast4_measurable": ("zemauth.can_see_vast4_metrics",),
    "vast4_viewable": ("zemauth.can_see_vast4_metrics",),
    "vast4_non_measurable": ("zemauth.can_see_vast4_metrics",),
    "vast4_non_viewable": ("zemauth.can_see_vast4_metrics",),
    "vast4_measurable_percent": ("zemauth.can_see_vast4_metrics",),
    "vast4_viewable_percent": ("zemauth.can_see_vast4_metrics",),
    "vast4_viewable_distribution": ("zemauth.can_see_vast4_metrics",),
    "vast4_non_measurable_distribution": ("zemauth.can_see_vast4_metrics",),
    "vast4_non_viewable_distribution": ("zemauth.can_see_vast4_metrics",),
    "etfm_vast4_vcpm": ("zemauth.can_see_vast4_metrics",),
    "local_etfm_vast4_vcpm": ("zemauth.can_see_vast4_metrics",),
}

FIELD_ENTITY_PERMISSION_MAPPING = {
    # AGENCY_SPEND_MARGIN
    "margin": Permission.AGENCY_SPEND_MARGIN,
    "local_margin": Permission.AGENCY_SPEND_MARGIN,
    "etf_cost": Permission.AGENCY_SPEND_MARGIN,
    "local_etf_cost": Permission.AGENCY_SPEND_MARGIN,
    # MEDIA_COST_DATA_COST_LICENCE_FEE
    "e_media_cost": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    "local_e_media_cost": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    "e_data_cost": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    "local_e_data_cost": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    "license_fee": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    "local_license_fee": Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    # BASE_COSTS_SERVICE_FEE
    "b_media_cost": Permission.BASE_COSTS_SERVICE_FEE,
    "local_b_media_cost": Permission.BASE_COSTS_SERVICE_FEE,
    "b_data_cost": Permission.BASE_COSTS_SERVICE_FEE,
    "local_b_data_cost": Permission.BASE_COSTS_SERVICE_FEE,
    "bt_cost": Permission.BASE_COSTS_SERVICE_FEE,
    "local_bt_cost": Permission.BASE_COSTS_SERVICE_FEE,
    "service_fee": Permission.BASE_COSTS_SERVICE_FEE,
    "local_service_fee": Permission.BASE_COSTS_SERVICE_FEE,
    "service_fee_refund": Permission.BASE_COSTS_SERVICE_FEE,
}


def filter_columns_by_permission(user, constraints, rows, goals):
    constraints = _extract_constraints(constraints)
    fields_to_keep = _get_fields_to_keep(user, goals)

    if user.has_perm_on_all_entities(Permission.READ):
        for field, permission in FIELD_ENTITY_PERMISSION_MAPPING.items():
            if user.has_perm_on_all_entities(permission):
                fields_to_keep.add(field)
            else:
                fields_to_keep.discard(field)
    else:
        entity_permission_cache = _build_entity_permission_cache(user, constraints)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(_entity_permission_fields_cleanup, entity_permission_cache, row, fields_to_keep)
                for row in rows
            ]
            concurrent.futures.wait(futures)


def _extract_constraints(constraints):
    new_constraints = {}
    if "account" in constraints:
        new_constraints["accounts"] = [constraints["account"]]
    elif "allowed_accounts" in constraints:
        new_constraints["accounts"] = list(constraints["allowed_accounts"])
    return new_constraints


def _get_fields_to_keep(user, goals):
    fields_to_keep = set(fields.DIMENSION_FIELDS)
    fields_to_keep |= fields.SOURCE_FIELDS
    fields_to_keep |= fields.HELPER_FIELDS
    fields_to_keep |= fields.PUBLISHER_FIELDS
    fields_to_keep |= fields.DEFAULT_STATS
    fields_to_keep |= fields.COST_FIELDS
    fields_to_keep |= fields.OTHER_DASH_FIELDS
    fields_to_keep |= fields.CAMPAIGN_GOAL_PERFORMANCE_FIELDS
    fields_to_keep |= fields.ENTITY_TAGS_FIELDS
    fields_to_keep |= fields.PLACEMENT_FIELDS
    fields_to_keep |= fields.VIEWABILITY_FIELDS
    fields_to_keep |= fields.POSTCLICK_ACQUISITION_FIELDS
    fields_to_keep |= fields.REFUND_FIELDS
    fields_to_keep |= fields.POSTCLICK_ENGAGEMENT_FIELDS

    _add_dynamic_fields(user, goals, fields_to_keep)
    _user_permission_fields_cleanup(user, fields_to_keep)

    return fields_to_keep


def _add_dynamic_fields(user, goals, fields_to_keep):
    fields_to_keep |= _get_allowed_campaign_goals_fields(
        user, goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals
    )
    fields_to_keep |= _get_allowed_conversion_goals_fields(user, goals.conversion_goals)
    fields_to_keep |= _get_allowed_pixels_fields(user, goals.pixels)


def _user_permission_fields_cleanup(user, fields_to_keep):
    for field, permissions in FIELD_PERMISSION_MAPPING.items():
        if not permissions or user.has_perms(permissions):
            fields_to_keep.add(field)
        if permissions and not user.has_perms(permissions):
            fields_to_keep.discard(field)


def _build_entity_permission_cache(user, constraints):
    entity_permission_cache = defaultdict(dict)
    accounts = constraints.get("accounts")
    for account in accounts:
        for field, permission in FIELD_ENTITY_PERMISSION_MAPPING.items():
            entity_permission_cache[account.id][field] = user.has_perm_on(permission, account)
    return entity_permission_cache


def _entity_permission_fields_cleanup(entity_permission_cache, row, fields_to_keep):
    fields_to_keep_per_row = fields_to_keep.copy()
    account_id = row.get("account_id")
    for field in FIELD_ENTITY_PERMISSION_MAPPING.keys():
        if _has_entity_permission_on_field(field, entity_permission_cache, account_id):
            fields_to_keep_per_row.add(field)
        else:
            fields_to_keep_per_row.discard(field)
    _remove_fields([row], fields_to_keep_per_row)


def _has_entity_permission_on_field(field, entity_permission_cache, account_id):
    if not account_id:
        return all(value.get(field, False) for value in entity_permission_cache.values())
    return entity_permission_cache[account_id].get(field, False)


def _remove_fields(rows, fields_to_keep):
    for row in rows:
        for row_field in list(row.keys()):
            if row_field not in fields_to_keep:
                row.pop(row_field, None)


def _get_allowed_campaign_goals_fields(user, campaign_goals, campaign_goal_values, conversion_goals):
    """
    Returns campaign goal field names that should be kept if user has
    proper permissions.
    """

    allowed_fields = set()
    included_campaign_goals = [x.campaign_goal.type for x in campaign_goal_values]
    for goal in included_campaign_goals:
        relevant_fields = dash.campaign_goals.RELEVANT_GOAL_ETFM_FIELDS_MAP.get(goal, [])
        allowed_fields |= set(relevant_fields)

    if CampaignGoalKPI.CPA in included_campaign_goals:
        allowed_fields |= set(
            "avg_etfm_cost_per_{}".format(cg.get_view_key(conversion_goals)) for cg in conversion_goals
        )
        allowed_fields |= set(
            "local_avg_etfm_cost_per_{}".format(cg.get_view_key(conversion_goals)) for cg in conversion_goals
        )

    allowed_fields |= set("etfm_performance_" + x.get_view_key() for x in campaign_goals)
    return allowed_fields


def _get_allowed_conversion_goals_fields(user, conversion_goals):
    """
    Returns conversion goal column names that should be kept if user has
    proper permissions.
    """

    allowed_fields = set(cg.get_view_key(conversion_goals) for cg in conversion_goals)
    allowed_fields |= set("conversion_rate_per_{}".format(cg.get_view_key(conversion_goals)) for cg in conversion_goals)
    return allowed_fields


def _get_allowed_pixels_fields(user, pixels):
    """
    Returns pixel column names and average costs column names that should be kept for all users.
    """

    click_conversion_windows = dash.constants.ConversionWindowsLegacy.get_all()
    view_conversion_windows = dash.constants.ConversionWindowsViewthrough.get_all()

    allowed_pixel_fields = _generate_allowed_pixel_fields(user, pixels, click_conversion_windows)
    allowed_pixel_fields = allowed_pixel_fields.union(
        _generate_allowed_pixel_fields(user, pixels, view_conversion_windows, suffix="_view")
    )

    return allowed_pixel_fields


def _generate_allowed_pixel_fields(user, pixels, conversion_windows, suffix=None):
    allowed = set()

    for pixel in pixels:
        for conversion_window in conversion_windows:
            view_key = pixel.get_view_key(conversion_window) + (suffix or "")
            allowed.add(view_key)
            allowed.add("conversion_rate_per_{}".format(view_key))
            allowed.add("avg_etfm_cost_per_" + view_key)
            allowed.add("local_avg_etfm_cost_per_" + view_key)
            allowed.add("etfm_roas_" + view_key)

    return allowed


def validate_breakdown_by_permissions(level, user, breakdown):
    base_dimension = constants.get_base_dimension(breakdown)

    if len(breakdown) == 1 and is_top_level_delivery_dimension(base_dimension):
        return

    if level == Level.ALL_ACCOUNTS:
        if base_dimension not in (
            StructureDimension.SOURCE,
            StructureDimension.ACCOUNT,
            StructureDimension.PUBLISHER,
            StructureDimension.PLACEMENT,
        ):
            raise exc.MissingDataError()

    elif level == Level.ACCOUNTS:
        if base_dimension not in (
            StructureDimension.SOURCE,
            StructureDimension.CAMPAIGN,
            StructureDimension.PUBLISHER,
            StructureDimension.PLACEMENT,
        ):
            raise exc.MissingDataError()

    elif level == Level.CAMPAIGNS:
        if base_dimension not in (
            StructureDimension.SOURCE,
            StructureDimension.AD_GROUP,
            StructureDimension.PUBLISHER,
            StructureDimension.PLACEMENT,
        ):
            raise exc.MissingDataError()

    elif level == Level.AD_GROUPS:
        if base_dimension not in (
            StructureDimension.SOURCE,
            StructureDimension.CONTENT_AD,
            StructureDimension.PUBLISHER,
            StructureDimension.PLACEMENT,
        ):
            raise exc.MissingDataError()

    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if is_extended_delivery_dimension(delivery_dimension) and not user.has_perm(
        "zemauth.can_view_breakdown_by_delivery_extended"
    ):
        raise exc.MissingDataError()


def validate_breakdown_by_structure(breakdown):
    base = constants.get_base_dimension(breakdown)
    if not base:
        return

    if len(breakdown) == 1 and is_top_level_delivery_dimension(base):
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

    if "publisher_id" in breakdown and "source_id" in breakdown:
        raise exc.InvalidBreakdownError("Unsupported breakdown - publishers are broken down by source by default")

    if constants.is_placement_breakdown(breakdown) and "content_ad_id" in breakdown:
        raise exc.InvalidBreakdownError("Unsupported breakdown - content ads can not be broken down by placement")

    if delivery and constants.is_placement_breakdown(breakdown):
        raise exc.InvalidBreakdownError(
            "Unsupported breakdown - placements can not be broken down by {}".format(delivery)
        )

    unsupported_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupported_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns: {}".format(", ".join(unsupported_breakdowns)))

    for i in range(len(clean_breakdown) - 1):
        if clean_breakdown[i] == clean_breakdown[i + 1]:
            raise exc.InvalidBreakdownError("Wrong breakdown order")

    if breakdown != clean_breakdown:
        raise exc.InvalidBreakdownError("Wrong breakdown order")
