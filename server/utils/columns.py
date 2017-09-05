import collections
import copy
import dash.constants
from utils import dates_helper


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

_PUBLISHERS_FIELD_MAPPING = {
    'domain_link': ('Link',),
}

_FIELD_MAPPING_REVERSE = {name: field for field, names in _FIELD_MAPPING.iteritems() for name in names}
_PUBLISHERS_FIELD_MAPPING_REVERSE = {name: field for field, names in _PUBLISHERS_FIELD_MAPPING.iteritems() for name in names}


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

    @classmethod
    def from_column_name(cls, name, raise_exception=True):
        match = _FIELD_MAPPING_REVERSE.get(name, None)
        if match:
            return match
        else:
            if raise_exception:
                raise Exception('No field key matches name "{}"'.format(name))
            return None


class ColumnNames:
    __metaclass__ = FieldsMeta

    @classmethod
    def __init_class__(cls):
        for k, v in _FIELD_MAPPING.iteritems():
            setattr(cls, k, v[0])


def get_field_names_mapping(pixels=[], conversion_goals=[], show_publishers_fields=False):
    columns = copy.copy(_FIELD_MAPPING_REVERSE)
    columns.update(get_pixel_field_names_mapping(pixels))
    columns.update(get_conversion_goals_field_names_mapping(conversion_goals))
    if show_publishers_fields:
        columns.update(_PUBLISHERS_FIELD_MAPPING_REVERSE)
    return columns


def get_pixel_field_names_mapping(pixels):
    field_names = collections.OrderedDict()
    for pixel in sorted(pixels, key=lambda x: x.name.lower()):
        prefix = pixel.get_prefix()

        for window, window_title in dash.constants.ConversionWindows.get_choices():
            field_name = '{}_{}'.format(prefix, window)
            column_name = u'{} {}'.format(pixel.name, window_title)
            field_names[column_name] = field_name

            cpa_field_name, cpa_column_name = _get_cpa_column(field_name, column_name)
            field_names[cpa_column_name] = cpa_field_name

            roas_field_name, roas_column_name = _get_roas_column(field_name, column_name)
            field_names[roas_column_name] = roas_field_name
    return field_names


def get_conversion_goals_field_names_mapping(conversion_goals):
    field_names = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        field_name = goal.get_view_key(conversion_goals)
        column_name = goal.name
        field_names[column_name] = field_name

        cpa_field_name, cpa_column_name = _get_cpa_column(field_name, column_name)
        field_names[cpa_column_name] = cpa_field_name
    return field_names


def _get_cpa_column(field_name, column_name):
    field_name = 'avg_cost_per_{}'.format(field_name)
    column_name = u'CPA ({})'.format(column_name)
    return field_name, column_name


def _get_roas_column(field_name, column_name):
    field_name = 'roas_{}'.format(field_name)
    column_name = u'ROAS ({})'.format(column_name)
    return field_name, column_name


def get_conversion_goals_column_names_mapping(conversion_goals):
    columns = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        field_name = goal.get_view_key(conversion_goals)
        column_name = goal.name
        columns[field_name] = column_name
    return columns


def add_date_to_name(name):
    local_date = dates_helper.local_today()
    return u'{} ({})'.format(name, local_date.strftime('%Y-%m-%d'))
