import copy
import datetime
import logging

import collections

from django.db.models import QuerySet, Model

from utils import sort_helper
from utils import exc

import dash.models
from dash.constants import PublisherBlacklistFilter

from stats import constants

logger = logging.getLogger(__name__)

CONTENT_ADS_FIELDS = [
    'url', 'title', 'display_url', 'brand_name', 'description', 'call_to_action', 'label', 'batch_name', 'batch_id',
    'upload_time', 'image_hash', 'image_urls', 'redirector_url', 'status_per_source'
]

SOURCE_FIELDS = [
    'min_bid_cpc', 'max_bid_cpc', 'daily_budget', 'maintenance', 'cpc', 'bid_cpc', 'current_bid_cpc',
    'current_daily_budget', 'supply_dash_url', 'supply_dash_disabled_message', 'editable_fields',
    'status_setting', 'id', 'notifications',
]

PUBLISHER_FIELDS = [
    'source_name', 'exchange', 'domain', 'external_id', 'domain_link', 'can_blacklist_publisher', 'blacklisted', 'blacklisted_level',
    'blacklisted_level_description'
]

OTHER_DASH_FIELDS = [
    'default_account_manager', 'default_sales_representative', 'campaign_manager', 'account_type', 'agency',
    'archived', 'maintenance', 'status_per_source'
]


Goals = collections.namedtuple('Goals', 'campaign_goals, conversion_goals, campaign_goal_values, pixels, primary_goals')


def get_goals(constraints):
    campaign = constraints.get('campaign')
    account = constraints.get('account')

    campaign_goals, conversion_goals, campaign_goal_values, pixels = [], [], [], []
    primary_goals = []

    if campaign:
        conversion_goals = campaign.conversiongoal_set.all().select_related('pixel')
        campaign_goals = campaign.campaigngoal_set.all().order_by('-primary', 'created_dt').select_related(
            'conversion_goal', 'conversion_goal__pixel')
        primary_goals = [campaign_goals.first()]
        campaign_goal_values = dash.campaign_goals.get_campaign_goal_values(campaign)

    elif 'allowed_campaigns' in constraints and 'account' in constraints:
        # only take for campaigns when constraints for 1 account, otherwise its too much
        allowed_campaigns = constraints['allowed_campaigns']
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign__in=allowed_campaigns)\
                                                             .select_related('pixel')

        campaign_goals = dash.models.CampaignGoal.objects.filter(campaign__in=allowed_campaigns)\
                                                         .order_by('-primary', 'created_dt')\
                                                         .select_related('conversion_goal', 'conversion_goal__pixel')

        primary_goals_by_campaign = {}
        for cg in campaign_goals:
            if cg.campaign_id not in primary_goals_by_campaign:
                primary_goals_by_campaign[cg.campaign_id] = cg
        primary_goals = primary_goals_by_campaign.values()

        for campaign in allowed_campaigns:
            campaign_goal_values.extend(dash.campaign_goals.get_campaign_goal_values(campaign))

    if account:
        pixels = account.conversionpixel_set.filter(archived=False)

    return Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, primary_goals)


def extract_stats_constraints(constraints, breakdown):
    """
    Copy constraints and remove all that are not part of the stats query.

    # NOTE: try to keep constraints in order - eg. account_id always sorted the same way
    so that we get the same collection when the same parameters are use. This way we don't
    miss cache when we request the same data but order of parameters differs.
    """

    new_constraints = {
        'date__gte': constraints['date__gte'],
        'date__lte': constraints['date__lte'],
        'source_id': list(constraints['filtered_sources'].values_list('pk', flat=True).order_by('pk')),
        'account_id': (constraints['account'].id if 'account' in constraints else
                       list(constraints['allowed_accounts'].values_list('pk', flat=True).order_by('pk'))),
    }

    if 'ad_group' in constraints:
        new_constraints['ad_group_id'] = constraints['ad_group'].id
    elif 'ad_group_id' in breakdown:
        new_constraints['ad_group_id'] = list(
            constraints['allowed_ad_groups'].values_list('pk', flat=True).order_by('pk'))

    if 'campaign' in constraints:
        new_constraints['campaign_id'] = constraints['campaign'].id
    elif 'campaign_id' in breakdown:
        new_constraints['campaign_id'] = list(
            constraints['allowed_campaigns'].values_list('pk', flat=True).order_by('pk'))

    if 'account' in constraints:
        new_constraints['account_id'] = constraints['account'].id

    if 'content_ad_id' in breakdown:
        new_constraints['content_ad_id'] = list(
            constraints['allowed_content_ads'].values_list('pk', flat=True).order_by('pk'))

    if 'publisher_id' in breakdown and constraints['publisher_blacklist_filter'] in \
       (PublisherBlacklistFilter.SHOW_ACTIVE, PublisherBlacklistFilter.SHOW_BLACKLISTED):
        publisher_constraints = [create_publisher_id(x.name, x.source_id) for x in constraints['publisher_blacklist']]

        if constraints['publisher_blacklist_filter'] == PublisherBlacklistFilter.SHOW_ACTIVE:
            new_constraints['publisher_id__neq'] = publisher_constraints
        elif constraints['publisher_blacklist_filter'] == PublisherBlacklistFilter.SHOW_BLACKLISTED:
            new_constraints['publisher_id'] = publisher_constraints

    return new_constraints


def decode_parents(breakdown, parents):
    """
    Returns a list of parsed breakdown_ids or None.
    """

    if not parents:
        return None

    return [decode_breakdown_id(breakdown, breakdown_id_str) for breakdown_id_str in parents]


def decode_breakdown_id(breakdown, breakdown_id_str):
    """
    Creates a dict with constraints from a breakdown id.

    Example:
    breakdown = [account, campaign, dma, day]
    breakdown_id_str = '1-2-500'

    Returns: {account_id: 1, campaign_id: 2, dma: '500'}
    """

    d = {}
    ids = breakdown_id_str.split(u"||")
    for i, dimension in enumerate(breakdown[:len(ids)]):
        str_id = ids[i]
        if str_id == '-None-':
            str_id = None
        elif dimension in constants.IntegerDimensions:
            str_id = int(str_id)

        d[dimension] = str_id

    return d


def encode_breakdown_id(breakdown, row):
    """
    Creates a breakdown id - string of consecutive ids separated by delimiter.

    Example:
    breakdown = [account, campaign, dma, day]
    row = {account_id: 1, campaign_id: 2, dma: '500', clicks: 123, ...}

    Returns: '1-2-500'
    """

    values = []
    for dim in breakdown:
        value = row[dim]

        if value is None:
            value = '-None-'

        values.append(unicode(value))

    return u"||".join(values)


def get_breakdown_id(row, breakdown):
    # returns a dict where breakdown dimensions are keys and values are dimension values
    d = {}
    for dim in breakdown:
        d[dim] = row[dim]
    return d


def check_constraints_are_supported(constraints):
    """
    Checks whether constraints include only known keys of known types.
    This way we check for programming mistakes.
    """

    query_set_keys = ['filtered_sources', 'filtered_agencies', 'allowed_accounts',
                      'allowed_campaigns', 'allowed_ad_groups', 'allowed_content_ads', 'publisher_blacklist']

    if 'filtered_sources' not in constraints:
        raise exc.UnknownFieldBreakdownError("Missing filtered sources")

    for key in query_set_keys:
        if key in constraints and not isinstance(constraints[key], QuerySet):
            raise exc.UnknownFieldBreakdownError("Value of '{}' should be a queryset".format(key))

    if 'account' not in constraints and 'allowed_accounts' not in constraints:
        raise exc.UnknownFieldBreakdownError("Constraints should include either 'account' or 'allowed_accounts")

    model_keys = ['account', 'campaign', 'ad_group']
    for key in model_keys:
        if key in constraints and not isinstance(constraints[key], Model):
            raise exc.UnknownFieldBreakdownError("Value of '{}' should be a django Model".format(key))

    other_keys = ['show_archived', 'filtered_account_types', 'date__gte', 'date__lte', 'publisher_blacklist_filter']
    unknown_keys = set(constraints.keys()) - set(query_set_keys) - set(model_keys) - set(other_keys)

    if unknown_keys:
        raise exc.UnknownFieldBreakdownError("Unknown fields in constraints {}".format(unknown_keys))


def get_supported_order(order, target_dimension):
    """
    This is hack that converts order field to something we already know
    how to sort. Order conversion in this function should be eventually supported.

    FIXME: Remove this hack
    """

    prefix, order_field = sort_helper.dissect_order(order)

    if order_field == 'cost':
        # cost is not supported anymore, this case needs to be handled in case this sort was cached in browser
        return prefix + 'media_cost'

    UNSUPPORTED_FIELDS = [
        "pacing", "allocated_budgets", "spend_projection",
        "license_fee_projection",
    ]

    if order_field in UNSUPPORTED_FIELDS:
        return prefix + "clicks"

    if target_dimension == 'publisher_id' and order_field in ('state', 'status'):
        return prefix + "clicks"

    if target_dimension == 'publisher_id' and order_field == 'exchange':
        return prefix + "source_id"

    return order


def extract_order_field(order, target_dimension, primary_goals=None):
    """
    Returns the order field that should be used to get visually pleasing results. Time is always
    shown ordered by time, so we don't get mixed dates etc.
    """

    # all time dimensions and age, age_gender, device_type are always sorted the same way
    if target_dimension in constants.TimeDimension._ALL or target_dimension in ('age', 'age_gender', 'device_type'):
        return 'name'

    prefix, order_field = sort_helper.dissect_order(order)

    if order_field == 'state':
        order_field = 'status'

    if target_dimension != 'content_ad_id' and order_field in CONTENT_ADS_FIELDS:
        order_field = 'name'

    if target_dimension != 'source_id' and order_field in SOURCE_FIELDS:
        order_field = 'clicks'

    if order_field == 'performance':
        if primary_goals:
            order_field = 'performance_' + primary_goals[0].get_view_key()
        else:
            order_field = 'clicks'

    return prefix + order_field


def extract_rs_order_field(order, target_dimension):
    """
    Converts order field to field name that is understood by redshiftapi.
    """

    prefix, order_field = sort_helper.dissect_order(order)

    if target_dimension in constants.TimeDimension._ALL or target_dimension in ('age', 'age_gender', 'device_type'):
        return prefix + target_dimension

    if target_dimension == 'publisher_id' and order_field == 'name':
        order_field = 'publisher'

    # all delivery dimensions are sorted by targeted dimension ids
    if target_dimension in constants.DeliveryDimension._ALL:
        if order_field == 'name':
            order_field = target_dimension
        elif order_field in ('state', 'status', 'archived'):
            # delivery does not have status/archived etc,
            # so mimick with clicks - more clicks, more active :)
            order_field = 'clicks'

    return prefix + order_field


def should_query_dashapi_first(order, target_dimension):

    if target_dimension == 'publisher_id':
        return False

    _, order_field = sort_helper.dissect_order(order)

    if order_field == 'name' and target_dimension in constants.StructureDimension._ALL:
        return True

    if order_field == 'status' and target_dimension in constants.StructureDimension._ALL:
        return True

    if order_field in CONTENT_ADS_FIELDS and target_dimension == 'content_ad_id':
        return True

    if order_field in SOURCE_FIELDS and target_dimension == 'source_id':
        return True

    if order_field in CONTENT_ADS_FIELDS and target_dimension == 'content_ad_id':
        return True

    if order_field in OTHER_DASH_FIELDS:
        return True

    return False


def should_query_dashapi(target_dimension):
    return target_dimension in constants.StructureDimension._ALL


def merge_rows(breakdown, dash_rows, stats_rows):
    group_a = sort_helper.group_rows_by_breakdown_key(breakdown, dash_rows)
    group_b = sort_helper.group_rows_by_breakdown_key(breakdown, stats_rows)

    rows = []
    for key, group_rows in group_a.iteritems():
        row_a = group_rows[0]
        row_b = group_b.pop(key, None)
        if row_b:
            row_a = merge_row(row_a, row_b[0])
        rows.append(row_a)

    if group_b:
        logger.warning("Got stats for unknown objects")

    return rows


def merge_row(row_a, row_b):
    row = {}
    row.update(row_a)
    row.update(row_b)
    return row


def create_publisher_id(domain, source_id):
    return u'__'.join((domain, unicode(source_id or '')))


def dissect_publisher_id(publisher):
    domain, source_id = publisher.rsplit(u'__', 1)
    return domain, int(source_id) if source_id else None


def log_user_query_request(user, breakdown, constraints, order, offset, limit):
    logger.info('Stats query request: user_id {}, breakdown {}, order {}, offset {}, limit {}, date range {}/{}, age {}, account_id {}, campaign_id {}, ad_group_id {}'.format(
        user.id,
        '__'.join(breakdown),
        order,
        offset,
        limit,
        constraints['date__gte'].isoformat(),
        constraints['date__lte'].isoformat(),
        (datetime.date.today() - constraints['date__gte']).days,
        constraints['account'].id if 'account' in constraints else 'NULL',
        constraints['campaign'].id if 'campaign' in constraints else 'NULL',
        constraints['ad_group'].id if 'ad_group' in constraints else 'NULL',
    ))
