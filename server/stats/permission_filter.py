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

FIELD_PERMISSION_MAPPING = {
    "media_cost": ("zemauth.can_view_actual_costs",),
    "local_media_cost": ("zemauth.can_view_actual_costs",),
    "b_media_cost": ("zemauth.can_see_service_fee",),
    "local_b_media_cost": ("zemauth.can_see_service_fee",),
    "e_media_cost": ("zemauth.can_view_platform_cost_breakdown",),
    "local_e_media_cost": ("zemauth.can_view_platform_cost_breakdown",),
    "data_cost": ("zemauth.can_view_actual_costs",),
    "local_data_cost": ("zemauth.can_view_actual_costs",),
    "b_data_cost": ("zemauth.can_see_service_fee",),
    "local_b_data_cost": ("zemauth.can_see_service_fee",),
    "e_data_cost": ("zemauth.can_view_platform_cost_breakdown",),
    "local_e_data_cost": ("zemauth.can_view_platform_cost_breakdown",),
    "at_cost": ("zemauth.can_view_actual_costs",),
    "local_at_cost": ("zemauth.can_view_actual_costs",),
    "bt_cost": ("zemauth.can_see_service_fee",),
    "local_bt_cost": ("zemauth.can_see_service_fee",),
    "et_cost": ("zemauth.can_view_platform_cost_breakdown_derived",),
    "local_et_cost": ("zemauth.can_view_platform_cost_breakdown_derived",),
    "etf_cost": ("zemauth.can_view_agency_cost_breakdown",),
    "local_etf_cost": ("zemauth.can_view_agency_cost_breakdown",),
    "service_fee": ("zemauth.can_see_service_fee",),
    "local_service_fee": ("zemauth.can_see_service_fee",),
    "license_fee": ("zemauth.can_view_platform_cost_breakdown",),
    "local_license_fee": ("zemauth.can_view_platform_cost_breakdown",),
    "margin": ("zemauth.can_view_agency_margin",),
    "local_margin": ("zemauth.can_view_agency_margin",),
    "yesterday_at_cost": ("zemauth.can_view_actual_costs",),
    "local_yesterday_at_cost": ("zemauth.can_view_actual_costs",),
    "service_fee_refund": ("zemauth.can_see_credit_refunds", "zemauth.can_see_service_fee"),
    # projections
    "pacing": ("zemauth.can_view_platform_cost_breakdown",),
    "allocated_budgets": ("zemauth.can_see_projections",),
    "spend_projection": ("zemauth.can_view_platform_cost_breakdown",),
    "license_fee_projection": ("zemauth.can_view_platform_cost_breakdown",),
    "total_fee": ("zemauth.can_view_flat_fees",),
    "flat_fee": ("zemauth.can_view_flat_fees",),
    "total_fee_projection": ("zemauth.can_view_flat_fees",),
    "default_account_manager": ("zemauth.can_see_managers_in_accounts_table",),
    "default_sales_representative": ("zemauth.can_see_managers_in_accounts_table",),
    "default_cs_representative": ("zemauth.can_see_managers_in_accounts_table",),
    "ob_sales_representative": ("zemauth.can_see_managers_in_accounts_table",),
    "ob_account_manager": ("zemauth.can_see_managers_in_accounts_table",),
    "campaign_manager": ("zemauth.can_see_managers_in_campaigns_table",),
    "account_type": ("zemauth.can_see_account_type",),
    "salesforce_url": ("zemauth.can_see_salesforce_url",),
    "agency": ("zemauth.can_view_account_agency_information",),
    "agency_id": ("zemauth.can_view_account_agency_information",),
    "etfm_performance": ("zemauth.campaign_goal_performance"),
    "styles": ("zemauth.campaign_goal_performance",),
    "bid_modifier": ("zemauth.can_use_publisher_bid_modifiers_in_ui",),
    "sspd_url": ("zemauth.can_see_sspd_url",),
    "campaign_type": ("zemauth.can_see_campaign_type_in_breakdowns",),
    # entity tags
    "agency_tags": ("zemauth.can_include_tags_in_reports",),
    "account_tags": ("zemauth.can_include_tags_in_reports",),
    "campaign_tags": ("zemauth.can_include_tags_in_reports",),
    "ad_group_tags": ("zemauth.can_include_tags_in_reports",),
    "source_tags": ("zemauth.can_include_tags_in_reports",),
    # placement fields
    "placement_id": ("zemauth.can_use_placement_targeting",),
    "placement": ("zemauth.can_use_placement_targeting",),
    "placement_type": ("zemauth.can_use_placement_targeting",),
    # viewability fields
    "mrc50_measurable": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_viewable": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_non_measurable": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_non_viewable": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_measurable_percent": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_viewable_percent": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_viewable_distribution": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_non_measurable_distribution": ("zemauth.can_see_mrc50_metrics",),
    "mrc50_non_viewable_distribution": ("zemauth.can_see_mrc50_metrics",),
    "etfm_mrc50_vcpm": ("zemauth.can_see_mrc50_metrics",),
    "local_etfm_mrc50_vcpm": ("zemauth.can_see_mrc50_metrics",),
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


def filter_columns_by_permission(user, rows, goals):
    fields_to_keep = _get_fields_to_keep(user, goals)
    _remove_fields(rows, fields_to_keep)
    _custom_cleanup(user, rows)


def _get_fields_to_keep(user, goals):
    fields_to_keep = set(fields.DIMENSION_FIELDS)
    fields_to_keep |= fields.SOURCE_FIELDS
    fields_to_keep |= fields.HELPER_FIELDS
    fields_to_keep |= fields.PUBLISHER_FIELDS
    fields_to_keep |= fields.DEFAULT_STATS

    if user.has_perm("zemauth.content_ads_postclick_acquisition") or user.has_perm(
        "zemauth.aggregate_postclick_acquisition"
    ):
        fields_to_keep |= fields.POSTCLICK_ACQUISITION_FIELDS

    if user.has_perm("zemauth.can_see_credit_refunds"):
        fields_to_keep |= fields.REFUND_FIELDS

    if user.has_perm("zemauth.aggregate_postclick_engagement"):
        fields_to_keep |= fields.POSTCLICK_ENGAGEMENT_FIELDS

    for field, permissions in FIELD_PERMISSION_MAPPING.items():
        if not permissions or user.has_perms(permissions):
            fields_to_keep.add(field)
        if permissions and not user.has_perms(permissions) and field in fields_to_keep:
            fields_to_keep.remove(field)

    # add allowed dynamically generated goals fields
    fields_to_keep |= _get_allowed_campaign_goals_fields(
        user, goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals
    )
    fields_to_keep |= _get_allowed_conversion_goals_fields(user, goals.conversion_goals)
    fields_to_keep |= _get_allowed_pixels_fields(user, goals.pixels)

    return fields_to_keep


def _remove_fields(rows, fields_to_keep):
    for row in rows:
        for row_field in list(row.keys()):
            if row_field not in fields_to_keep:
                row.pop(row_field, None)


def _custom_cleanup(user, rows):
    """
    Put here custom logics for cleaning fields that doesn't fit '_remove_fields'.
    """

    remove_content_ad_source_status = not user.has_perm("zemauth.can_see_media_source_status_on_submission_popover")

    if remove_content_ad_source_status:
        for row in rows:
            if row.get("status_per_source"):
                for source_status in list(row["status_per_source"].values()):
                    source_status.pop("source_status", None)


def _get_allowed_campaign_goals_fields(user, campaign_goals, campaign_goal_values, conversion_goals):
    """
    Returns campaign goal field names that should be kept if user has
    proper permissions.
    """

    allowed_fields = set()
    included_campaign_goals = []

    if user.has_perm("zemauth.campaign_goal_optimization"):
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

    if user.has_perm("zemauth.campaign_goal_performance"):
        allowed_fields |= set("etfm_performance_" + x.get_view_key() for x in campaign_goals)

    return allowed_fields


def _get_allowed_conversion_goals_fields(user, conversion_goals):
    """
    Returns conversion goal column names that should be kept if user has
    proper permissions.
    """

    if user.has_perm("zemauth.can_see_redshift_postclick_statistics"):
        allowed_fields = set(cg.get_view_key(conversion_goals) for cg in conversion_goals)
        allowed_fields |= set(
            "conversion_rate_per_{}".format(cg.get_view_key(conversion_goals)) for cg in conversion_goals
        )
        return allowed_fields

    return set()


def _get_allowed_pixels_fields(user, pixels):
    """
    Returns pixel column names and average costs column names that should be kept for all users.
    """

    click_conversion_windows = dash.constants.ConversionWindowsLegacy.get_all()
    view_conversion_windows = dash.constants.ConversionWindowsViewthrough.get_all()

    allowed_pixel_fields = _generate_allowed_pixel_fields(user, pixels, click_conversion_windows)
    if user.has_perm("zemauth.can_see_viewthrough_conversions"):
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
        if not user.has_perm("zemauth.can_see_top_level_delivery_breakdowns"):
            raise exc.MissingDataError()
        return

    if level == Level.ALL_ACCOUNTS:
        if base_dimension not in (
            StructureDimension.SOURCE,
            StructureDimension.ACCOUNT,
            StructureDimension.PUBLISHER,
            StructureDimension.PLACEMENT,
        ):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm("zemauth.all_accounts_sources_view"):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.ACCOUNT and not user.has_perm("zemauth.all_accounts_accounts_view"):
            raise exc.MissingDataError()

    elif level == Level.ACCOUNTS:
        if base_dimension not in (
            StructureDimension.SOURCE,
            StructureDimension.CAMPAIGN,
            StructureDimension.PUBLISHER,
            StructureDimension.PLACEMENT,
        ):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm("zemauth.account_sources_view"):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.CAMPAIGN and not user.has_perm("zemauth.account_campaigns_view"):
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

    if StructureDimension.PUBLISHER in breakdown and not user.has_perm("zemauth.can_see_publishers"):
        raise exc.MissingDataError()

    if constants.is_placement_breakdown(breakdown) and not user.has_perm("zemauth.can_use_placement_targeting"):
        raise exc.MissingDataError()

    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if delivery_dimension is not None and not user.has_perm("zemauth.can_view_breakdown_by_delivery"):
        raise exc.MissingDataError()

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
