import dash.constants
import stats.constants
from redshiftapi import api_breakdowns
from utils import queryset_helper

__all__ = ["query", "query_totals"]


def query(breakdown, constraints, goals, order, offset, limit, use_publishers_view=False):
    constraints = extract_constraints(constraints, breakdown)

    rows = api_breakdowns.query(
        breakdown,
        constraints,
        None,
        goals,
        order,
        offset,
        limit,
        use_publishers_view=use_publishers_view,
        is_reports=True,
        extra_name="report_all",
    )

    return rows


def query_totals(breakdown, constraints, goals, use_publishers_view=False):
    constraints = extract_constraints(constraints, breakdown)

    rows = api_breakdowns.query(
        [],
        constraints,
        None,
        goals,
        use_publishers_view=use_publishers_view,
        breakdown_for_name=breakdown,
        extra_name="report_total",
    )
    return rows


def extract_constraints(constraints, breakdown):
    new_constraints = {"date__gte": constraints["date__gte"], "date__lte": constraints["date__lte"]}

    mapping = {
        "allowed_accounts": "account_id",
        "allowed_campaigns": "campaign_id",
        "allowed_ad_groups": "ad_group_id",
        "allowed_content_ads": "content_ad_id",
        "filtered_sources": "source_id",
    }

    for key, column in list(mapping.items()):
        if constraints.get(key) is not None:
            new_constraints[column] = queryset_helper.get_pk_list(constraints[key])

    if (
        "publisher_blacklist_filter" in constraints
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
