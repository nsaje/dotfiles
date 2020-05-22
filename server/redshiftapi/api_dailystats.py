import dash.constants
import stats.constants
from redshiftapi import api_breakdowns

__all__ = ["query"]


def query(breakdown, metrics, constraints, goals, order, use_publishers_view=False):
    constraints = extract_constraints(constraints, breakdown, use_publishers_view)

    rows = api_breakdowns.query_with_background_cache(
        breakdown,
        constraints,
        None,
        goals,
        order,
        metrics=metrics,
        use_publishers_view=use_publishers_view,
        extra_name="dailystats_all",
        query_all=True,
    )

    return rows


def extract_constraints(constraints, breakdown, use_publishers_view):
    new_constraints = {
        "date__gte": constraints["date__gte"],
        "date__lte": constraints["date__lte"],
        "source_id": list(constraints["filtered_sources"].values_list("pk", flat=True).order_by("pk")),
    }

    if "account" in constraints:
        new_constraints["account_id"] = constraints["account"].id
    elif "allowed_accounts" in constraints:
        new_constraints["account_id"] = list(
            constraints["allowed_accounts"].values_list("pk", flat=True).order_by("pk")
        )

    if "campaign" in constraints:
        new_constraints["campaign_id"] = constraints["campaign"].id
    elif "allowed_campaigns" in constraints and "account" in constraints:
        new_constraints["campaign_id"] = list(
            constraints["allowed_campaigns"].values_list("pk", flat=True).order_by("pk")
        )

    if "ad_group" in constraints:
        new_constraints["ad_group_id"] = constraints["ad_group"].id
    elif "allowed_ad_groups" in constraints and "campaign" in constraints:
        new_constraints["ad_group_id"] = list(
            constraints["allowed_ad_groups"].values_list("pk", flat=True).order_by("pk")
        )

    if not use_publishers_view:
        # NOTE: publishers view doesn't support breakdown by content ad
        if "content_ad" in constraints:
            new_constraints["content_ad_id"] = constraints["content_ad"].id
        elif "allowed_content_ads" in constraints and "ad_group" in constraints:
            new_constraints["content_ad_id"] = list(
                constraints["allowed_content_ads"].values_list("pk", flat=True).order_by("pk")
            )

    if (
        use_publishers_view
        and constraints["publisher_blacklist_filter"] != dash.constants.PublisherBlacklistFilter.SHOW_ALL
    ):
        is_placement = stats.constants.is_placement_breakdown(breakdown)
        constraints_entry_field = "placement_id" if is_placement else "publisher_id"
        if constraints["publisher_blacklist_filter"] == dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE:
            new_constraints[f"{constraints_entry_field}__neq"] = list(
                constraints["publisher_blacklist"]
                .filter_publisher_or_placement(is_placement)
                .annotate_entry_id(is_placement=is_placement)
                .values_list("entry_id", flat=True)
            )
        elif constraints["publisher_blacklist_filter"] == dash.constants.PublisherBlacklistFilter.SHOW_BLACKLISTED:
            new_constraints[constraints_entry_field] = list(
                constraints["publisher_blacklist"]
                .filter_publisher_or_placement(is_placement)
                .annotate_entry_id(is_placement=is_placement)
                .values_list("entry_id", flat=True)
            )
        elif constraints["publisher_blacklist_filter"] == dash.constants.PublisherBlacklistFilter.SHOW_WHITELISTED:
            new_constraints[constraints_entry_field] = list(
                constraints["publisher_whitelist"]
                .filter_publisher_or_placement(is_placement)
                .annotate_entry_id(is_placement=is_placement)
                .values_list("entry_id", flat=True)
            )

    return new_constraints
