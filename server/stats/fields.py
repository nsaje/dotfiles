from stats.constants import DeliveryDimension
from stats.constants import StructureDimension
from stats.constants import TimeDimension

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
        "placement",
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
    "creative_type",
    "creative_size",
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
    "ad_tag",
    "redirector_url",
    "status_per_source",
    "tracker_urls",
    "amplify_promoted_link_id",
    "amplify_live_preview_link",
    "sspd_url",
    "bid_modifier",
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
    "domain_link",
    "blacklisted",
    "blacklisted_level",
    "blacklisted_level_description",
    "source_slug",
}

OTHER_DASH_FIELDS = {
    "default_account_manager",
    "default_sales_representative",
    "default_cs_representative",
    "ob_sales_representative",
    "ob_account_manager",
    "campaign_manager",
    "account_type",
    "campaign_type",
    "salesforce_url",
    "agency",
    "agency_id",
    "archived",
    "maintenance",
    "status_per_source",
}

CAMPAIGN_GOAL_PERFORMANCE_FIELDS = {"etfm_performance", "styles"}

# content ad fields
DIMENSION_FIELDS |= set(CONTENT_ADS_FIELDS)

DEFAULT_STATS = set(
    [
        "ctr",
        "etfm_cpc",
        "local_etfm_cpc",
        "clicks",
        "impressions",
        "etfm_cpm",
        "local_etfm_cpm",
        "etfm_cost",
        "local_etfm_cost",
        "yesterday_etfm_cost",
        "local_yesterday_etfm_cost",
        "avg_etfm_cost_per_minute",
        "local_avg_etfm_cost_per_minute",
        "avg_etfm_cost_per_non_bounced_visit",
        "local_avg_etfm_cost_per_non_bounced_visit",
        "avg_etfm_cost_per_pageview",
        "local_avg_etfm_cost_per_pageview",
        "avg_etfm_cost_per_new_visitor",
        "local_avg_etfm_cost_per_new_visitor",
        "avg_etfm_cost_per_visit",
        "local_avg_etfm_cost_per_visit",
        "avg_etfm_cost_per_unique_user",
        "local_avg_etfm_cost_per_unique_user",
        "video_start",
        "video_first_quartile",
        "video_midpoint",
        "video_third_quartile",
        "video_complete",
        "video_progress_3s",
        "video_etfm_cpv",
        "local_video_etfm_cpv",
        "video_etfm_cpcv",
        "local_video_etfm_cpcv",
        "video_start_percent",
        "video_first_quartile_percent",
        "video_midpoint_percent",
        "video_third_quartile_percent",
        "video_complete_percent",
        "video_progress_3s_percent",
    ]
)

PLATFORM_SPEND_REFUND_FIELDS = ["e_media_cost_refund", "media_cost_refund", "et_cost_refund", "at_cost_refund"]

SERVICE_FEE_REFUND_FIELDS = ["service_fee_refund"]

LICENSE_FEE_REFUND_FIELDS = ["license_fee_refund"]

MARGIN_REFUND_FIELDS = ["margin_refund"]

AGENCY_SPEND_REFUND_FIELDS = ["etf_cost_refund"]

TOTAL_SPEND_REFUND_FIELDS = ["etfm_cost_refund"]

REFUND_FIELDS = set(
    PLATFORM_SPEND_REFUND_FIELDS
    + SERVICE_FEE_REFUND_FIELDS
    + LICENSE_FEE_REFUND_FIELDS
    + MARGIN_REFUND_FIELDS
    + AGENCY_SPEND_REFUND_FIELDS
    + TOTAL_SPEND_REFUND_FIELDS
)


HELPER_FIELDS = set(["campaign_has_available_budget", "status_per_source"])

COST_FIELDS = {
    "media_cost",
    "local_media_cost",
    "data_cost",
    "local_data_cost",
    "b_media_cost",
    "local_b_media_cost",
    "b_data_cost",
    "local_b_data_cost",
    "e_media_cost",
    "local_e_media_cost",
    "e_data_cost",
    "local_e_data_cost",
    "etfm_cost",
    "local_etfm_cost",
    "service_fee",
    "local_service_fee",
    "license_fee",
    "local_license_fee",
    "margin",
    "local_margin",
    "at_cost",
    "local_at_cost",
    "bt_cost",
    "local_bt_cost",
    "et_cost",
    "local_et_cost",
    "etf_cost",
    "local_etf_cost",
    "yesterday_at_cost",
    "local_yesterday_at_cost",
}

TRAFFIC_FIELDS = [
    "clicks",
    "impressions",
    "etfm_cpc",
    "local_etfm_cpc",
    "etfm_cpm",
    "local_etfm_cpm",
    "ctr",
    "title",
    "url",
    "media_cost",
    "local_media_cost",
    "data_cost",
    "local_data_cost",
    "b_media_cost",
    "local_b_media_cost" "b_data_cost",
    "local_b_data_cost",
    "e_media_cost",
    "local_e_media_cost",
    "e_data_cost",
    "local_e_data_cost",
    "etfm_cost",
    "local_etfm_cost",
    "service_fee",
    "local_service_fee",
    "license_fee",
    "local_license_fee",
    "margin",
    "local_margin",
    "video_start",
    "video_first_quartile",
    "video_midpoint",
    "video_third_quartile",
    "video_complete",
    "video_progress_3s",
    "video_etfm_cpv",
    "local_video_etfm_cpv",
    "video_etfm_cpcv",
    "local_video_etfm_cpcv",
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

ENTITY_TAGS_FIELDS = {"agency_tags", "account_tags", "campaign_tags", "ad_group_tags", "source_tags"}

PLACEMENT_FIELDS = {"placement_id", "placement", "placement_type"}

VIEWABILITY_FIELDS = {
    "mrc50_measurable",
    "mrc50_viewable",
    "mrc50_non_measurable",
    "mrc50_non_viewable",
    "mrc50_measurable_percent",
    "mrc50_viewable_percent",
    "mrc50_viewable_distribution",
    "mrc50_non_measurable_distribution",
    "mrc50_non_viewable_distribution",
    "etfm_mrc50_vcpm",
    "local_etfm_mrc50_vcpm",
    "mrc100_measurable",
    "mrc100_viewable",
    "mrc100_non_measurable",
    "mrc100_non_viewable",
    "mrc100_measurable_percent",
    "mrc100_viewable_percent",
    "mrc100_viewable_distribution",
    "mrc100_non_measurable_distribution",
    "mrc100_non_viewable_distribution",
    "etfm_mrc100_vcpm",
    "local_etfm_mrc100_vcpm",
    "vast4_measurable",
    "vast4_viewable",
    "vast4_non_measurable",
    "vast4_non_viewable",
    "vast4_measurable_percent",
    "vast4_viewable_percent",
    "vast4_viewable_distribution",
    "vast4_non_measurable_distribution",
    "vast4_non_viewable_distribution",
    "etfm_vast4_vcpm",
    "local_etfm_vast4_vcpm",
}
