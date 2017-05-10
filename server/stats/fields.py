from stats.constants import StructureDimension, DeliveryDimension, TimeDimension

DIMENSION_FIELDS = set(StructureDimension._ALL) | set(DeliveryDimension._ALL) | set(TimeDimension._ALL)
DIMENSION_FIELDS |= set([
    'name', 'status', 'state', 'archived',
    'account', 'campaign', 'ad_group', 'content_ad', 'source', 'publisher',
    'account_status', 'campaign_status', 'ad_group_status', 'content_ad_status',
    'source_status', 'publisher_status',
    'breakdown_name', 'breakdown_id', 'parent_breakdown_id',
])

CONTENT_ADS_FIELDS = [
    'url', 'title', 'display_url', 'brand_name', 'description', 'call_to_action', 'label', 'batch_name', 'batch_id',
    'upload_time', 'image_hash', 'image_urls', 'image_url', 'redirector_url', 'status_per_source'
]

SOURCE_FIELDS = [
    'min_bid_cpc', 'max_bid_cpc', 'daily_budget', 'maintenance', 'bid_cpc', 'current_bid_cpc',
    'current_daily_budget', 'supply_dash_url', 'supply_dash_disabled_message', 'editable_fields',
    'status_setting', 'id', 'notifications', 'source_slug',
]

PUBLISHER_FIELDS = [
    'source_name', 'exchange', 'domain', 'external_id', 'domain_link', 'can_blacklist_publisher', 'blacklisted',
    'blacklisted_level', 'blacklisted_level_description', 'source_slug',
]

OTHER_DASH_FIELDS = [
    'default_account_manager', 'default_sales_representative', 'default_cs_representative',
    'campaign_manager', 'account_type', 'agency', 'archived', 'maintenance', 'status_per_source'
]

PROJECTION_FIELDS = (
    'allocated_budgets', 'pacing', 'flat_fee', 'total_fee',
    'spend_projection', 'license_fee_projection', 'total_fee_projection',
)

# content ad fields
DIMENSION_FIELDS |= set(CONTENT_ADS_FIELDS)

DEFAULT_STATS = set([
    'ctr', 'cpc', 'clicks', 'impressions', 'billing_cost', 'cpm',
    'video_start', 'video_first_quartile', 'video_midpoint',
    'video_third_quartile', 'video_complete', 'video_progress_3s',
])

HELPER_FIELDS = set(['campaign_stop_inactive', 'campaign_has_available_budget', 'status_per_source'])

DEFAULT_FIELDS = DIMENSION_FIELDS | DEFAULT_STATS | set(SOURCE_FIELDS) | HELPER_FIELDS | set(PUBLISHER_FIELDS)

TRAFFIC_FIELDS = [
    'clicks', 'impressions', 'data_cost',
    'cpc', 'ctr', 'title', 'url',
    'media_cost', 'e_media_cost', 'e_data_cost',
    'license_fee', 'billing_cost',
    'margin', 'agency_total', 'cpm',
    'video_start', 'video_first_quartile', 'video_midpoint',
    'video_third_quartile', 'video_complete', 'video_progress_3s',
]
POSTCLICK_ACQUISITION_FIELDS = ['click_discrepancy', ]
POSTCLICK_ENGAGEMENT_FIELDS = [
    'percent_new_users', 'pv_per_visit', 'avg_tos', 'bounce_rate', 'goals', 'new_visits',
    'returning_users', 'unique_users', 'bounced_visits', 'total_seconds', 'non_bounced_visits',
    'new_users', 'pageviews', 'visits',
]
