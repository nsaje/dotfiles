import collections

import dash.constants
from utils import dates_helper

from . import exceptions

_FIELD_MAPPING = {
    "date": ("Date",),
    "day": ("Day",),
    "week": ("Week",),
    "month": ("Month",),
    "currency": ("Currency",),
    "agency": ("Agency",),
    "agency_id": ("Agency Id", "Agency ID"),
    "account_id": ("Account Id", "Account ID"),
    "account": ("Account",),
    "campaign_id": ("Campaign Id", "Campaign ID"),
    "campaign": ("Campaign",),
    "ad_group_id": ("Ad Group Id", "Ad Group ID"),
    "ad_group": ("Ad Group",),
    "content_ad_id": ("Content Ad Id", "Content Ad ID"),
    "content_ad": ("Content Ad",),
    "creative_type": ("Creative Type",),
    "batch_name": ("Batch Name",),
    "brand_name": ("Brand Name",),
    "call_to_action": ("Call to action",),
    "description": ("Description",),
    "creative_size": ("Creative Size",),
    "display_url": ("Display URL",),
    "image_urls": ("Thumbnail",),
    "image_hash": ("Image Hash",),
    "ad_tag": ("Ad Tag",),
    "tracker_urls": ("Impression trackers",),
    "image_url": ("Image URL",),
    "icon_url": ("Brand Logo URL",),
    "icon_hash": ("Brand Logo Hash",),
    "label": ("Label",),
    "upload_time": ("Uploaded",),
    "url": ("URL",),
    "publisher_id": ("Publisher Id",),
    "publisher": ("Publisher",),
    "blacklisted_level": ("Blacklisted Level",),
    "source": ("Media Source",),
    "source_id": ("Media Source Id", "Media Source ID", "Source ID"),
    "source_slug": ("Media Source Slug", "Source Slug"),
    "bid_cpc": ("Bid CPC",),
    "bid_cpm": ("Bid CPM",),
    "daily_budget": ("Daily Spend Cap", "Daily Budget"),
    "supply_dash_url": ("Link",),
    "status": ("Status",),
    "account_status": ("Account Status",),
    "campaign_status": ("Campaign Status",),
    "ad_group_status": ("Ad Group Status",),
    "content_ad_status": ("Content Ad Status",),
    "source_status": ("Media Source Status",),
    "publisher_status": ("Publisher Status",),
    "campaign_manager": ("Campaign Manager",),
    "account_type": ("Account Type",),
    "business": ("Business",),
    "default_sales_representative": ("Sales Representative",),
    "default_cs_representative": ("CS Representative",),
    "ob_sales_representative": ("OB sales Representative",),
    "ob_account_manager": ("OB account manager",),
    "default_account_manager": ("Account Manager",),
    "salesforce_url": ("SalesForce Link",),
    "age": ("Age",),
    "gender": ("Gender",),
    "age_gender": ("Age and Gender",),
    "country": ("Country",),
    "region": ("State", "State / Region"),
    "dma": ("DMA",),
    "device_type": ("Device",),
    "device_os": ("Operating System",),
    "environment": ("Environment",),
    "browser": ("Browser",),
    "connection_type": ("Connection Type",),
    "zem_placement_type": ("Zemanta Placement Type",),
    "placement_id": ("Placement Id",),
    "placement": ("Placement",),
    "placement_type": ("Placement Type",),
    "video_playback_method": ("Video Playback Method",),
    "avg_etfm_cost_per_new_visitor": ("Avg. Cost per New Visitor", "Avg. Cost for New Visitor"),
    "avg_etfm_cost_per_minute": ("Avg. Cost per Minute",),
    "avg_etfm_cost_per_non_bounced_visit": ("Avg. Cost per Non-Bounced Visit",),
    "avg_etfm_cost_per_pageview": ("Avg. Cost per Pageview",),
    "avg_etfm_cost_per_visit": ("Avg. Cost per Visit",),
    "avg_etfm_cost_per_unique_user": ("Avg. Cost per Unique User",),
    "avg_tos": ("Time on Site",),
    "at_cost": ("Actual Base Platform Spend",),
    "at_cost_refund": ("Actual Base Platform Spend Refund",),
    "bt_cost": ("Base Platform Spend",),
    "et_cost": ("Platform Spend",),
    "et_cost_refund": ("Platform Spend Refund",),
    "etf_cost": ("Agency Spend",),
    "etf_cost_refund": ("Agency Spend Refund",),
    "etfm_cost": ("Total Spend",),
    "etfm_cost_refund": ("Total Spend Refund",),
    "bounce_rate": ("Bounce Rate",),
    "bounced_visits": ("Bounced Visits",),
    "click_discrepancy": ("Click Discrepancy",),
    "clicks": ("Clicks",),
    "etfm_cpc": ("Avg. CPC",),
    "etfm_cpm": ("Avg. CPM",),
    "ctr": ("CTR",),
    "data_cost": ("Actual Base Data Cost", "Actual Base Data Spend"),
    "b_data_cost": ("Base Data Cost", "Base Data Spend"),
    "e_data_cost": ("Data Cost", "Data Spend"),
    "b_media_cost": ("Base Media Spend",),
    "e_media_cost": ("Media Spend",),
    "e_media_cost_refund": ("Media Spend Refund",),
    "yesterday_at_cost": ("Actual Yesterday Spend",),
    "yesterday_etfm_cost": ("Yesterday Spend",),
    "impressions": ("Impressions",),
    "service_fee": ("Service Fee",),
    "license_fee": ("License Fee",),
    "service_fee_refund": ("Service Fee Refund",),
    "license_fee_refund": ("License Fee Refund",),
    "margin": ("Margin",),
    "margin_refund": ("Margin Refund",),
    "media_cost": ("Actual Base Media Spend",),
    "media_cost_refund": ("Actual Base Media Spend Refund",),
    "new_users": ("New Users",),
    "non_bounced_visits": ("Non-Bounced Visits",),
    "pageviews": ("Pageviews",),
    "percent_new_users": ("% New Users",),
    "pv_per_visit": ("Pageviews per Visit",),
    "returning_users": ("Returning Users",),
    "total_seconds": ("Total Seconds",),
    "unique_users": ("Unique Users",),
    "visits": ("Visits",),
    "video_start": ("Video Start",),
    "video_first_quartile": ("Video First Quartile",),
    "video_midpoint": ("Video Midpoint",),
    "video_third_quartile": ("Video Third Quartile",),
    "video_complete": ("Video Complete",),
    "video_progress_3s": ("Video Progress 3s",),
    "video_start_percent": ("% Video Start",),
    "video_first_quartile_percent": ("% Video First Quartile",),
    "video_midpoint_percent": ("% Video Midpoint",),
    "video_third_quartile_percent": ("% Video Third Quartile",),
    "video_complete_percent": ("% Video Complete",),
    "video_progress_3s_percent": ("% Video Progress 3s",),
    "video_etfm_cpv": ("Avg. CPV",),
    "video_etfm_cpcv": ("Avg. CPCV",),
    "bid_modifier": ("Bid Modifier",),
    "sspd_url": ("SSPD Link",),
    "campaign_type": ("Campaign Type",),
    "agency_tags": ("Agency Tags",),
    "account_tags": ("Account Tags",),
    "campaign_tags": ("Campaign Tags",),
    "ad_group_tags": ("Ad Group Tags",),
    "source_tags": ("Source Tags",),
    "mrc50_measurable": ("Measurable Impressions",),
    "mrc50_viewable": ("Viewable Impressions",),
    "mrc50_non_measurable": ("Not-Measurable Impressions", "Not-Measurable Impr."),
    "mrc50_non_viewable": ("Not-Viewable Impressions",),
    "mrc50_measurable_percent": ("% Measurable Impressions",),
    "mrc50_viewable_percent": ("% Viewable Impressions",),
    "mrc50_viewable_distribution": ("Impression Distribution (Viewable)",),
    "mrc50_non_measurable_distribution": ("Impression Distribution (Not-Measurable)",),
    "mrc50_non_viewable_distribution": ("Impression Distribution (Not-Viewable)",),
    "etfm_mrc50_vcpm": ("Avg. VCPM",),
    "mrc100_measurable": ("MRC100 Measurable Impressions",),
    "mrc100_viewable": ("MRC100 Viewable Impressions",),
    "mrc100_non_measurable": ("MRC100 Not-Measurable Impressions",),
    "mrc100_non_viewable": ("MRC100 Not-Viewable Impressions",),
    "mrc100_measurable_percent": ("% MRC100 Measurable Impressions",),
    "mrc100_viewable_percent": ("% MRC100 Viewable Impressions",),
    "mrc100_viewable_distribution": ("MRC100 Impression Distribution (Viewable)",),
    "mrc100_non_measurable_distribution": ("MRC100 Impression Distribution (Not-Measurable)",),
    "mrc100_non_viewable_distribution": ("MRC100 Impression Distribution (Not-Viewable)",),
    "etfm_mrc100_vcpm": ("Avg. MRC100 VCPM",),
    "vast4_measurable": ("VAST4 Measurable Impressions",),
    "vast4_viewable": ("VAST4 Viewable Impressions",),
    "vast4_non_measurable": ("VAST4 Non-Measurable",),
    "vast4_non_viewable": ("VAST4 Non-Viewable",),
    "vast4_measurable_percent": ("% VAST4 Measurable Impressions",),
    "vast4_viewable_percent": ("% VAST4 Viewable Impressions",),
    "vast4_viewable_distribution": ("VAST4 Impression Distribution (Viewable)",),
    "vast4_non_measurable_distribution": ("VAST4 Impression Distribution (Not-Measurable)",),
    "vast4_non_viewable_distribution": ("VAST4 Impression Distribution (Not-Viewable)",),
    "etfm_vast4_vcpm": ("Avg. VAST4 VCPM",),
}

#  - same name as source, figure out how to solve this
_FIELD_MAPPING_PUBLISHERS_OVERRIDES = {"domain_link": ("Link",)}

_COST_FIELDS = (
    "bid_cpc",
    "bid_cpm",
    "daily_budget",
    "data_cost",
    "b_data_cost",
    "e_data_cost",
    "b_media_cost",
    "e_media_cost",
    "e_media_cost_refund",
    "service_fee",
    "license_fee",
    "service_fee_refund",
    "license_fee_refund",
    "margin",
    "margin_refund",
    "media_cost",
    "media_cost_refund",
    "avg_etfm_cost_per_new_visitor",
    "avg_etfm_cost_per_minute",
    "avg_etfm_cost_per_non_bounced_visit",
    "avg_etfm_cost_per_pageview",
    "avg_etfm_cost_per_visit",
    "avg_etfm_cost_per_unique_user",
    "etfm_cost",
    "etfm_cost_refund",
    "etf_cost",
    "etf_cost_refund",
    "bt_cost",
    "et_cost",
    "et_cost_refund",
    "at_cost",
    "at_cost_refund",
    "yesterday_etfm_cost",
    "yesterday_at_cost",
    "etfm_cpc",
    "etfm_cpm",
    "video_etfm_cpv",
    "video_etfm_cpcv",
    "etfm_mrc50_vcpm",
    "etfm_mrc100_vcpm",
    "etfm_vast4_vcpm",
)

_DYNAMIC_COST_FIELDS_PREFIXES = ("avg_etfm_cost_per_", "etfm_roas")


class FieldsMeta(type):
    # support init of a class
    def __new__(cls, name, parents, dct):
        model_class = super(FieldsMeta, cls).__new__(cls, name, parents, dct)

        # Important: this initializes alias names from python attribute names
        # This is the main functionality of the model
        model_class.__init_class__()
        return model_class


class FieldNames(metaclass=FieldsMeta):
    @classmethod
    def __init_class__(cls):
        for k, v in _FIELD_MAPPING.items():
            setattr(cls, k, k)
        for k, v in _FIELD_MAPPING_PUBLISHERS_OVERRIDES.items():
            setattr(cls, k, k)


def custom_column_to_field_name_mapping(pixels=[], conversion_goals=[], show_publishers_fields=False):
    mappings = [_FIELD_MAPPING]
    if show_publishers_fields:
        mappings.append(_FIELD_MAPPING_PUBLISHERS_OVERRIDES)

    mapping = {}
    for m in mappings:
        for field_name, column_names in list(m.items()):
            for column_name in column_names:
                mapping[column_name] = field_name

    mapping.update(_get_pixel_field_names_mapping(pixels))
    mapping.update(_get_conversion_goals_field_names_mapping(conversion_goals))

    return mapping


def get_field_name(column_name, mapping=None, raise_exception=True):
    if mapping is None:
        mapping = DEFAULT_REVERSE_FIELD_MAPPING

    if column_name not in mapping and raise_exception:
        raise exceptions.FieldNameNotFound('No field matches column name "{}"'.format(column_name))
    return mapping.get(column_name, None)


def custom_field_to_column_name_mapping(pixels=[], conversion_goals=[], show_publishers_fields=False):
    mapping = custom_column_to_field_name_mapping(pixels, conversion_goals, show_publishers_fields)
    return {v: k for k, v in list(mapping.items())}


def get_column_name(field_name, mapping=None, raise_exception=True):
    if mapping is None:
        mapping = DEFAULT_FIELD_MAPPING

    if field_name not in mapping and raise_exception:
        raise exceptions.ColumnNameNotFound('No column matches field name "{}"'.format(field_name))
    return mapping.get(field_name, None)


def _get_pixel_field_names_mapping(pixels):
    click_conversion_windows = list(dash.constants.ConversionWindowsLegacy.get_choices())
    view_conversion_windows = list(dash.constants.ConversionWindows.get_choices())

    mapping = collections.OrderedDict()
    mapping.update(_generate_pixel_fields(pixels, click_conversion_windows, ["", " - Click attr."]))
    mapping.update(_generate_pixel_fields(pixels, view_conversion_windows, [" - View attr."], field_suffix="_view"))

    return mapping


def _generate_pixel_fields(pixels, conversion_windows, column_suffixes, field_suffix=None):
    mapping = collections.OrderedDict()
    for pixel in sorted(pixels, key=lambda x: x.name.lower()):
        prefix = pixel.get_prefix()

        for window, window_title in conversion_windows:
            field_name = "{}_{}".format(prefix, window) + (field_suffix or "")
            for column_suffix in column_suffixes:
                column_name = "{} {}".format(pixel.name, window_title) + column_suffix
                mapping[column_name] = field_name
                mapping.update(_get_conversion_rate_field_names_mapping(field_name, column_name))
                mapping.update(_get_cpa_field_names_mapping(field_name, column_name))
                mapping.update(_get_roas_field_names_mapping(field_name, column_name))

    return mapping


def _get_conversion_goals_field_names_mapping(conversion_goals):
    mapping = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        field_name = goal.get_view_key(conversion_goals)
        column_name = goal.name
        mapping[column_name] = field_name
        mapping.update(_get_conversion_rate_field_names_mapping(field_name, column_name))
        mapping.update(_get_cpa_field_names_mapping(field_name, column_name))

    return mapping


def _get_conversion_rate_field_names_mapping(field_name, column_name):
    return {"Conversion rate ({})".format(column_name): "conversion_rate_per_{}".format(field_name)}


def _get_cpa_field_names_mapping(field_name, column_name):
    return {"CPA ({})".format(column_name): "avg_etfm_cost_per_{}".format(field_name)}


def _get_roas_field_names_mapping(field_name, column_name):
    return {"ROAS ({})".format(column_name): "etfm_roas_{}".format(field_name)}


def get_conversion_goals_column_names_mapping(conversion_goals):
    mapping = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        field_name = goal.get_view_key(conversion_goals)
        column_name = goal.name
        mapping[field_name] = column_name
    return mapping


def add_date_to_name(name):
    local_date = dates_helper.local_today()
    return "{} ({})".format(name, local_date.strftime("%Y-%m-%d"))


def is_cost_column(column_name, field_name_mapping):
    field_name = get_field_name(column_name, field_name_mapping, raise_exception=False)
    if not field_name:
        return False
    return field_name in _COST_FIELDS or field_name.startswith(_DYNAMIC_COST_FIELDS_PREFIXES)


DEFAULT_FIELD_MAPPING = custom_field_to_column_name_mapping()
DEFAULT_REVERSE_FIELD_MAPPING = custom_column_to_field_name_mapping()
