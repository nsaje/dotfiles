from stats.constants import StructureDimension, DeliveryDimension, TimeDimension

DIMENSION_FIELDS = set(StructureDimension._ALL) | set(DeliveryDimension._ALL) | set(TimeDimension._ALL)
DIMENSION_FIELDS |= set(
    [
        "name",
        "status",
        "state",
        "archived",
        "account",
        "campaign",
        "ad_group",
        "content_ad",
        "source",
        "publisher",
        "account_status",
        "campaign_status",
        "ad_group_status",
        "content_ad_status",
        "source_status",
        "publisher_status",
        "breakdown_name",
        "breakdown_id",
        "parent_breakdown_id",
    ]
)

CONTENT_ADS_FIELDS = {
    "url",
    "title",
    "display_url",
    "brand_name",
    "description",
    "call_to_action",
    "label",
    "batch_name",
    "batch_id",
    "upload_time",
    "image_hash",
    "image_urls",
    "image_url",
    "redirector_url",
    "status_per_source",
    "tracker_urls",
    "amplify_live_preview_link",
    "sspd_url",
}

SOURCE_FIELDS = {
    "min_bid_cpc",
    "max_bid_cpc",
    "min_bid_cpm",
    "max_bid_cpm",
    "daily_budget",
    "local_daily_budget",
    "maintenance",
    "bid_cpc",
    "local_bid_cpc",
    "current_bid_cpc",
    "local_current_bid_cpc",
    "bid_cpm",
    "local_bid_cpm",
    "current_bid_cpm",
    "local_current_bid_cpm",
    "current_daily_budget",
    "local_current_daily_budget",
    "supply_dash_url",
    "supply_dash_disabled_message",
    "editable_fields",
    "status_setting",
    "id",
    "notifications",
    "source_slug",
}

PUBLISHER_FIELDS = {
    "source_name",
    "exchange",
    "domain",
    "external_id",
    "domain_link",
    "can_blacklist_publisher",
    "blacklisted",
    "blacklisted_level",
    "blacklisted_level_description",
    "source_slug",
}

OTHER_DASH_FIELDS = {
    "default_account_manager",
    "default_sales_representative",
    "default_cs_representative",
    "campaign_manager",
    "account_type",
    "agency",
    "archived",
    "maintenance",
    "status_per_source",
}

PROJECTION_FIELDS = {
    "allocated_budgets",
    "pacing",
    "flat_fee",
    "total_fee",
    "spend_projection",
    "license_fee_projection",
    "total_fee_projection",
}

# content ad fields
DIMENSION_FIELDS |= set(CONTENT_ADS_FIELDS)

DEFAULT_STATS = set(
    [
        "ctr",
        "cpc",
        "local_cpc",
        "etfm_cpc",
        "local_etfm_cpc",
        "clicks",
        "impressions",
        "billing_cost",
        "local_billing_cost",
        "cpm",
        "local_cpm",
        "etfm_cpm",
        "local_etfm_cpm",
        "video_start",
        "video_first_quartile",
        "video_midpoint",
        "video_third_quartile",
        "video_complete",
        "video_progress_3s",
        "video_cpv",
        "local_video_cpv",
        "video_etfm_cpv",
        "local_video_etfm_cpv",
        "video_cpcv",
        "local_video_cpcv",
        "video_etfm_cpcv",
        "local_video_etfm_cpcv",
        "avg_cost_per_minute",
        "local_avg_cost_per_minute",
        "avg_cost_per_non_bounced_visit",
        "local_avg_cost_per_non_bounced_visit",
        "avg_cost_per_pageview",
        "local_avg_cost_per_pageview",
        "avg_cost_for_new_visitor",
        "local_avg_cost_for_new_visitor",
        "avg_cost_per_visit",
        "local_avg_cost_per_visit",
    ]
)

PLATFORM_SPEND_REFUND_FIELDS = ["e_media_cost_refund", "media_cost_refund", "et_cost_refund", "at_cost_refund"]

LICENSE_FEE_REFUND_FIELDS = ["license_fee_refund"]

MARGIN_REFUND_FIELDS = ["margin_refund"]

AGENCY_SPEND_REFUND_FIELDS = ["etf_cost_refund", "billing_cost_refund"]

TOTAL_SPEND_REFUND_FIELDS = ["etfm_cost_refund", "agency_cost_refund"]

REFUND_FIELDS = set(
    PLATFORM_SPEND_REFUND_FIELDS
    + LICENSE_FEE_REFUND_FIELDS
    + MARGIN_REFUND_FIELDS
    + AGENCY_SPEND_REFUND_FIELDS
    + TOTAL_SPEND_REFUND_FIELDS
)


HELPER_FIELDS = set(["campaign_has_available_budget", "status_per_source"])

TRAFFIC_FIELDS = [
    "clicks",
    "impressions",
    "data_cost",
    "local_data_cost",
    "cpc",
    "local_cpc",
    "ctr",
    "title",
    "url",
    "media_cost",
    "local_media_cost",
    "e_media_cost",
    "local_e_media_cost",
    "e_data_cost",
    "local_e_data_cost",
    "license_fee",
    "local_license_fee",
    "billing_cost",
    "local_billing_cost",
    "margin",
    "local_margin",
    "agency_cost",
    "local_agency_cost",
    "cpm",
    "local_cpm",
    "video_start",
    "video_first_quartile",
    "video_midpoint",
    "video_third_quartile",
    "video_complete",
    "video_progress_3s",
    "video_cpv",
    "local_video_cpv",
    "video_cpcv",
    "local_video_cpcv",
]
POSTCLICK_ACQUISITION_FIELDS = {"click_discrepancy"}
POSTCLICK_ENGAGEMENT_FIELDS = {
    "percent_new_users",
    "pv_per_visit",
    "avg_tos",
    "bounce_rate",
    "goals",
    "new_visits",
    "returning_users",
    "unique_users",
    "bounced_visits",
    "total_seconds",
    "non_bounced_visits",
    "new_users",
    "pageviews",
    "visits",
}
