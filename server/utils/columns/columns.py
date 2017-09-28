import collections
import dash.constants
from utils import dates_helper
import exceptions


_FIELD_MAPPING = {
    'date': ('Date',),

    'day': ('Day',),
    'week': ('Week',),
    'month': ('Month',),

    'agency': ('Agency',),
    'agency_id': ('Agency Id', 'Agency ID'),
    'account_id': ('Account Id', 'Account ID'),
    'account': ('Account',),
    'campaign_id': ('Campaign Id', 'Campaign ID'),
    'campaign': ('Campaign',),
    'ad_group_id': ('Ad Group Id', 'Ad Group ID'),
    'ad_group': ('Ad Group',),

    'content_ad_id': ('Content Ad Id', 'Content Ad ID'),
    'content_ad': ('Content Ad',),
    'batch_name': ('Batch Name',),
    'brand_name': ('Brand Name',),
    'call_to_action': ('Call to action',),
    'description': ('Description',),
    'display_url': ('Display URL',),
    'image_urls': ('Thumbnail',),
    'image_hash': ('Image Hash',),
    'tracker_urls': ('Impression trackers',),
    'image_url': ('Image URL',),
    'label': ('Label',),
    'upload_time': ('Uploaded',),
    'url': ('URL',),

    'publisher_id': ('Publisher Id',),
    'publisher': ('Publisher',),
    'external_id': ('External Id',),
    'blacklisted_level': ('Blacklisted Level',),

    'source': ('Media Source',),
    'source_id': ('Media Source Id', 'Media Source ID', 'Source ID'),
    'source_slug': ('Media Source Slug', 'Source Slug'),
    'bid_cpc': ('Bid CPC',),
    'daily_budget': ('Daily Spend Cap',),
    'supply_dash_url': ('Link',),

    'status': ('Status',),
    'account_status': ('Account Status',),
    'campaign_status': ('Campaign Status',),
    'ad_group_status': ('Ad Group Status',),
    'content_ad_status': ('Content Ad Status',),
    'source_status': ('Media Source Status',),
    'publisher_status': ('Publisher Status',),

    'campaign_manager': ('Campaign Manager',),
    'account_type': ('Account Type',),
    'default_sales_representative': ('Sales Representative',),
    'default_cs_representative': ('CS Representative',),
    'default_account_manager': ('Account Manager',),
    'salesforce_url': ('SalesForce Link',),

    'age': ('Age',),
    'gender': ('Gender',),
    'age_gender': ('Age and Gender',),
    'country': ('Country',),
    'state': ('State',),
    'dma': ('DMA',),
    'device_type': ('Device',),
    'placement_type': ('Placement Type',),
    'video_playback_method': ('Video Playback Method',),

    'agency_cost': ('Total Spend + Margin',),
    'avg_cost_for_new_visitor': ('Avg. Cost for New Visitor',),
    'avg_cost_per_minute': ('Avg. Cost per Minute',),
    'avg_cost_per_non_bounced_visit': ('Avg. Cost per Non-Bounced Visit',),
    'avg_cost_per_pageview': ('Avg. Cost per Pageview',),
    'avg_cost_per_visit': ('Avg. Cost per Visit',),
    'avg_tos': ('Time on Site',),
    'billing_cost': ('Total Spend',),
    'bounce_rate': ('Bounce Rate',),
    'bounced_visits': ('Bounced Visits',),
    'click_discrepancy': ('Click Discrepancy',),
    'clicks': ('Clicks',),
    'cpc': ('Avg. CPC',),
    'cpm': ('Avg. CPM',),
    'ctr': ('CTR',),
    'data_cost': ('Actual Data Cost',),
    'e_data_cost': ('Data Cost',),
    'e_media_cost': ('Media Spend',),
    'e_yesterday_cost': ('Yesterday Spend',),
    'impressions': ('Impressions',),
    'license_fee': ('License Fee',),
    'margin': ('Margin',),
    'media_cost': ('Actual Media Spend',),
    'new_users': ('New Users',),
    'non_bounced_visits': ('Non-Bounced Visits',),
    'pageviews': ('Pageviews',),
    'percent_new_users': ('% New Users',),
    'pv_per_visit': ('Pageviews per Visit',),
    'returning_users': ('Returning Users',),
    'total_seconds': ('Total Seconds',),
    'unique_users': ('Unique Users',),
    'visits': ('Visits',),
    'yesterday_cost': ('Actual Yesterday Spend',),

    'pacing': ('Pacing',),
    'allocated_budgets': ('Media budgets',),
    'spend_projection': ('Spend Projection',),
    'license_fee_projection': ('License Fee Projection',),
    'flat_fee': ('Recognized Flat Fee',),
    'total_fee': ('Total Fee',),
    'total_fee_projection': ('Total Fee Projection',),

    'video_start': ('Video Start',),
    'video_first_quartile': ('Video First Quartile',),
    'video_midpoint': ('Video Midpoint',),
    'video_third_quartile': ('Video Third Quartile',),
    'video_complete': ('Video Complete',),
    'video_progress_3s': ('Video Progress 3s',),
    'video_cpv': ('Avg. CPV',),
    'video_cpcv': ('Avg. CPCV',),
}

_FIELD_MAPPING_BCMV2_OVERRIDES = {
    'avg_etfm_cost_for_new_visitor': ('Avg. Cost for New Visitor',),
    'avg_etfm_cost_per_minute': ('Avg. Cost per Minute',),
    'avg_etfm_cost_per_non_bounced_visit': ('Avg. Cost per Non-Bounced Visit',),
    'avg_etfm_cost_per_pageview': ('Avg. Cost per Pageview',),
    'avg_etfm_cost_per_visit': ('Avg. Cost per Visit',),
    'avg_et_cost_for_new_visitor': ('Avg. Platform Cost for New Visitor',),
    'avg_et_cost_per_minute': ('Avg. Platform Cost per Minute',),
    'avg_et_cost_per_non_bounced_visit': ('Avg. Platform Cost per Non-Bounced Visit',),
    'avg_et_cost_per_pageview': ('Avg. Platform Cost per Pageview',),
    'avg_et_cost_per_visit': ('Avg. Platform Cost per Visit',),

    'etfm_cost': ('Total Spend',),
    'etf_cost': ('Agency Spend',),
    'et_cost': ('Platform Spend',),
    'at_cost': ('Actual Platform Spend',),

    'yesterday_etfm_cost': ('Yesterday Spend',),
    'yesterday_et_cost': ('Yesterday Platform Spend',),
    'yesterday_at_cost': ('Actual Yesterday Spend',),

    'etfm_cpc': ('Avg. CPC',),
    'et_cpc': ('Avg. Platform CPC',),

    'etfm_cpm': ('Avg. CPM',),
    'et_cpm': ('Avg. Platform CPM',),

    'video_etfm_cpv': ('Avg. CPV',),
    'video_et_cpv': ('Avg. Platform CPV',),

    'video_etfm_cpcv': ('Avg. CPCV',),
    'video_et_cpcv': ('Avg. Platform CPCV',),
}

#  - same name as source, figure out how to solve this
_FIELD_MAPPING_PUBLISHERS_OVERRIDES = {
    'domain_link': ('Link',),
}


class FieldsMeta(type):
    # support init of a class
    def __new__(cls, name, parents, dct):
        model_class = super(FieldsMeta, cls).__new__(cls, name, parents, dct)

        # Important: this initializes alias names from python attribute names
        # This is the main functionality of the model
        model_class.__init_class__()
        return model_class


class FieldNames:
    __metaclass__ = FieldsMeta

    @classmethod
    def __init_class__(cls):
        for k, v in _FIELD_MAPPING.iteritems():
            setattr(cls, k, k)
        for k, v in _FIELD_MAPPING_BCMV2_OVERRIDES.iteritems():
            setattr(cls, k, k)
        for k, v in _FIELD_MAPPING_PUBLISHERS_OVERRIDES.iteritems():
            setattr(cls, k, k)


def custom_column_to_field_name_mapping(pixels=[], conversion_goals=[], show_publishers_fields=False, uses_bcm_v2=False):
    mappings = [_FIELD_MAPPING]
    if uses_bcm_v2:
        mappings.append(_FIELD_MAPPING_BCMV2_OVERRIDES)
    if show_publishers_fields:
        mappings.append(_FIELD_MAPPING_PUBLISHERS_OVERRIDES)

    mapping = {}
    for m in mappings:
        for field_name, column_names in m.items():
            for column_name in column_names:
                mapping[column_name] = field_name

    mapping.update(_get_pixel_field_names_mapping(pixels, uses_bcm_v2))
    mapping.update(_get_conversion_goals_field_names_mapping(conversion_goals, uses_bcm_v2))

    return mapping


def get_field_name(column_name, mapping=None, raise_exception=True):
    if mapping is None:
        mapping = DEFAULT_REVERSE_FIELD_MAPPING

    if column_name not in mapping and raise_exception:
        raise exceptions.FieldNameNotFound('No field matches column name "{}"'.format(column_name))
    return mapping.get(column_name, None)


def custom_field_to_column_name_mapping(pixels=[], conversion_goals=[], show_publishers_fields=False, uses_bcm_v2=False):
    mapping = custom_column_to_field_name_mapping(pixels, conversion_goals, show_publishers_fields, uses_bcm_v2)
    return {v: k for k, v in mapping.items()}


def get_column_name(field_name, mapping=None, raise_exception=True):
    if mapping is None:
        mapping = DEFAULT_FIELD_MAPPING

    if field_name not in mapping and raise_exception:
        raise exceptions.ColumnNameNotFound('No column matches field name "{}"'.format(field_name))
    return mapping.get(field_name, None)


def _get_pixel_field_names_mapping(pixels, uses_bcm_v2):
    mapping = collections.OrderedDict()
    for pixel in sorted(pixels, key=lambda x: x.name.lower()):
        prefix = pixel.get_prefix()

        for window, window_title in dash.constants.ConversionWindows.get_choices():
            field_name = '{}_{}'.format(prefix, window)
            column_name = u'{} {}'.format(pixel.name, window_title)
            mapping[column_name] = field_name
            mapping.update(_get_cpa_field_names_mapping(field_name, column_name, uses_bcm_v2))
            mapping.update(_get_roas_field_names_mapping(field_name, column_name, uses_bcm_v2))

    return mapping


def _get_conversion_goals_field_names_mapping(conversion_goals, uses_bcm_v2):
    mapping = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        field_name = goal.get_view_key(conversion_goals)
        column_name = goal.name
        mapping[column_name] = field_name
        mapping.update(_get_cpa_field_names_mapping(field_name, column_name, uses_bcm_v2))

    return mapping


def _get_cpa_field_names_mapping(field_name, column_name, uses_bcm_v2):
    if uses_bcm_v2:
        return {
            u'CPA ({})'.format(column_name): 'avg_etfm_cost_per_{}'.format(field_name),
            u'Platform CPA ({})'.format(column_name): 'avg_et_cost_per_{}'.format(field_name),
        }

    return {
        u'CPA ({})'.format(column_name): 'avg_cost_per_{}'.format(field_name)
    }


def _get_roas_field_names_mapping(field_name, column_name, uses_bcm_v2):
    if uses_bcm_v2:
        return {
            u'ROAS ({})'.format(column_name): 'roas_etfm_{}'.format(field_name),
            u'Platform ROAS ({})'.format(column_name): 'roas_et_{}'.format(field_name),
        }
    return {
        u'ROAS ({})'.format(column_name): 'roas_{}'.format(field_name),
    }


def get_conversion_goals_column_names_mapping(conversion_goals):
    mapping = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        field_name = goal.get_view_key(conversion_goals)
        column_name = goal.name
        mapping[field_name] = column_name
    return mapping


def add_date_to_name(name):
    local_date = dates_helper.local_today()
    return u'{} ({})'.format(name, local_date.strftime('%Y-%m-%d'))


DEFAULT_FIELD_MAPPING = custom_field_to_column_name_mapping()
DEFAULT_REVERSE_FIELD_MAPPING = custom_column_to_field_name_mapping()
