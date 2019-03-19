from django.utils.text import slugify

import dash.dashapi.api_reports
import redshiftapi.api_reports
from stats import api_breakdowns
from stats import constants
from stats import helpers
from stats import permission_filter
from utils import columns
from utils import sort_helper


def query(
    user,
    breakdown,
    constraints,
    goals,
    order,
    offset,
    limit,
    level,
    include_items_with_no_spend=False,
    dashapi_cache=None,
):

    order = extract_order(order)
    stats_rows = redshiftapi.api_reports.query(
        breakdown,
        constraints,
        goals,
        order,
        offset,
        limit,
        use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown),
    )

    helpers.remap_delivery_stats_keys(stats_rows, constants.get_target_dimension(breakdown))

    if include_items_with_no_spend:
        if len(stats_rows) == limit:
            # if this happens offset and limit will have to be implemented for dashapi.query
            raise Exception("Too many rows for option include items with no spend")
        dash_rows = dash.dashapi.api_reports.query(user, breakdown, constraints, level)
        rows = helpers.merge_rows(breakdown, dash_rows, stats_rows)
        rows = sort_helper.sort_results(rows, [order])
    else:
        rows = stats_rows
        dash.dashapi.api_reports.annotate(rows, user, breakdown, constraints, level, dashapi_cache)

    permission_filter.filter_columns_by_permission(user, rows, goals, constraints, level)

    return rows


def totals(user, breakdown, constraints, goals, level):
    rows = redshiftapi.api_reports.query_totals(
        breakdown, constraints, goals, use_publishers_view=api_breakdowns.should_use_publishers_view(breakdown)
    )

    assert len(rows) == 1

    dash.dashapi.api_reports.annotate_totals(rows[0], user, breakdown, constraints, level)
    permission_filter.filter_columns_by_permission(user, rows, goals, constraints, level)

    return rows[0]


def get_filename(breakdown, constraints):

    if constraints["allowed_accounts"].count() == 1:
        account_name = slugify(constraints["allowed_accounts"][0].name)
    else:
        account_name = "ZemantaOne"

    campaign_name = None
    if constraints["allowed_campaigns"] is not None and constraints["allowed_campaigns"].count() == 1:
        campaign_name = slugify(constraints["allowed_campaigns"][0].name)

    ad_group_name = None
    if constraints["allowed_ad_groups"] is not None and constraints["allowed_ad_groups"].count() == 1:
        ad_group_name = slugify(constraints["allowed_ad_groups"][0].name)

    breakdown = ["by_" + columns.get_column_name(constants.get_dimension_name_key(x)).lower() for x in breakdown]
    return "_".join(
        [
            _f
            for _f in [
                account_name,
                campaign_name,
                ad_group_name,
                "_".join(breakdown),
                "report",
                constraints["date__gte"].isoformat(),
                constraints["date__lte"].isoformat(),
            ]
            if _f
        ]
    )


# This API can only return rows sorted by columns in redshift and as sort by the following fields default
# to some default order
UNABLE_TO_SORT = (
    "campaign",
    "brand_name",
    "bid_cpc",
    "bid_cpm",
    "batch_name",
    "source",
    "blacklisted_level",
    "content_ad",
    "account_type",
    "salesforce_url",
    "content_ad_status",
    "flat_fee",
    "source_slug",
    "account",
    "ad_group_status",
    "daily_budget",
    "call_to_action",
    "default_cs_representative",
    "placement_type",
    "image_url",
    "tracker_urls",
    "publisher_status",
    "account_status",
    "video_playback_method",
    "upload_time",
    "domain_link",
    "agency",
    "label",
    "spend_projection",
    "allocated_budgets",
    "license_fee_projection",
    "status",
    "image_hash",
    "description",
    "image_urls",
    "campaign_manager",
    "supply_dash_url",
    "total_fee_projection",
    "display_url",
    "url",
    "external_id",
    "source_status",
    "pacing",
    "default_sales_representative",
    "ad_group",
    "default_account_manager",
    "total_fee",
    "campaign_status",
    "e_media_cost_refund",
    "license_fee_refund",
    "etfm_cost_refund",
    "billing_cost_refund",
)


def extract_order(order):
    prefix, fieldname = sort_helper.dissect_order(order)
    if fieldname in UNABLE_TO_SORT:
        fieldname = "e_media_cost"
    return prefix + fieldname
