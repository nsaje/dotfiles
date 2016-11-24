import collections
import copy
import dash.constants


class FieldsMeta(type):
    # support init of a class
    def __new__(cls, name, parents, dct):
        model_class = super(FieldsMeta, cls).__new__(cls, name, parents, dct)

        # Important: this initializes alias names from python attribute names
        # This is the main functionality of the model
        model_class.__init_class__()
        return model_class


class Names:
    __metaclass__ = FieldsMeta

    __FIELDS_KEY_NAME_DICT__ = None

    @classmethod
    def __init_class__(cls):
        cls.__FIELDS_KEY_NAME_DICT__ = {}
        for k, v in ((k, v) for k, v in cls.__dict__.iteritems() if not k.startswith('_') and isinstance(v, basestring)):
            cls.__FIELDS_KEY_NAME_DICT__[k] = v

    date = 'Date'

    day = 'Day'
    week = 'Week'
    month = 'Month'

    ad_group_id = 'Ad Group Id'
    ad_group = 'Ad Group'

    content_ad_id = 'Content Ad Id'
    content_ad = 'Content Ad'
    batch_name = 'Batch Name'
    brand_name = 'Brand Name'
    call_to_action = 'Call to action'
    description = 'Description'
    display_url = 'Display URL'
    image_urls = 'Thumbnail'
    label = 'Label'
    upload_time = 'Uploaded'
    url = 'URL'

    publisher_id = 'Publisher Id'
    publisher = 'Publisher'
    external_id = 'External Id'
    domain_link = 'Link'
    blacklisted_level = 'Blacklisted Level'

    source = 'Media Source'
    source_id = 'Media Source Id'
    bid_cpc = 'Bid CPC'
    daily_budget = 'Daily Spend Cap'
    supply_dash_url = 'Link'

    status = 'Status'

    agency_total = 'Total Spend + Margin'
    avg_cost_for_new_visitor = 'Avg. Cost for New Visitor'
    avg_cost_per_minute = 'Avg. Cost per Minute'
    avg_cost_per_non_bounced_visit = 'Avg. Cost per Non-Bounced Visit'
    avg_cost_per_pageview = 'Avg. Cost per Pageview'
    avg_cost_per_visit = 'Avg. Cost per Visit'
    avg_tos = 'Time on Site'
    billing_cost = 'Total Spend'
    bounce_rate = 'Bounce Rate'
    bounced_visits = 'Bounced Visits'
    click_discrepancy = 'Click Discrepancy'
    clicks = 'Clicks'
    cpc = 'Avg. CPC'
    cpm = 'Avg. CPM'
    ctr = 'CTR'
    data_cost = 'Actual Data Cost'
    e_data_cost = 'Data Cost'
    e_media_cost = 'Media Spend'
    e_yesterday_cost = 'Yesterday Spend'
    impressions = 'Impressions'
    license_fee = 'License Fee'
    margin = 'Margin'
    media_cost = 'Actual Media Spend'
    new_users = 'New Users'
    non_bounced_visits = 'Non-Bounced Visits'
    pageviews = 'Pageviews'
    percent_new_users = '% New Users'
    pv_per_visit = 'Pageviews per Visit'
    returning_users = 'Returning Users'
    total_seconds = 'Total Seconds'
    unique_users = 'Unique Users'
    visits = 'Visits'
    yesterday_cost = 'Actual Yesterday Spend'

    @classmethod
    def get_keys(cls, names):
        fields = []
        for name in names:
            match = [k for k, v in cls.__FIELDS_KEY_NAME_DICT__.iteritems() if v == name]
            if len(match) == 1:
                fields.append(match[0])
            elif len(match) > 1:
                raise Exception('Multiple field keys {} match name "{}"'.format(match, name))
            else:
                raise Exception('No field key matches name "{}"'.format(name))
        return fields


def get_column_names_mapping(pixels=[], conversion_goals=[]):
    columns = copy.copy(Names.__FIELDS_KEY_NAME_DICT__)
    columns.update(get_pixel_column_names_mapping(pixels))
    columns.update(get_conversion_goals_column_names_mapping(conversion_goals))
    return columns


def get_pixel_column_names_mapping(pixels):
    columns = collections.OrderedDict()
    for pixel in sorted(pixels, key=lambda x: x.name.lower()):
        prefix = pixel.get_prefix()

        for window, window_title in dash.constants.ConversionWindows.get_choices():
            key = '{}_{}'.format(prefix, window)
            name = '{} {}'.format(pixel.name, window_title)
            columns[key] = name

            key = 'avg_cost_per_{}'.format(key)
            name = 'CPA ({})'.format(name)
            columns[key] = name
    return columns


def get_conversion_goals_column_names_mapping(conversion_goals):
    columns = collections.OrderedDict()
    for goal in (x for x in conversion_goals if x.type != dash.constants.ConversionGoalType.PIXEL):
        key = goal.get_view_key(conversion_goals)
        name = goal.name
        columns[key] = name
    return columns
