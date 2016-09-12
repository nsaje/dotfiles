import copy
import collections

from django.db.models import QuerySet, Model

from utils import sort_helper
from utils import exc

import dash.models
from dash.constants import Level

from stats import constants
from reports.db_raw_helpers import extract_obj_ids

CONTENT_ADS_FIELDS = [
    'url', 'title', 'display_url', 'brand_name', 'description', 'call_to_action', 'label', 'batch_name', 'batch_id',
    'upload_time', 'image_hash', 'image_urls', 'redirector_url',
]

SOURCE_FIELDS = [
    'min_bid_cpc', 'max_bid_cpc', 'daily_budget'
]


Goals = collections.namedtuple('Goals', 'campaign_goals, conversion_goals, campaign_goal_values, pixels, primary_goal')


def prepare_constraints(level, user, breakdown, start_date, end_date, filtered_sources, show_archived=False,
                        filtered_agencies=None, filtered_account_types=None,
                        account=None, campaign=None, ad_group=None):
    """
    Sets constraints so that only objects for which user has proper permissions get queried.
    In case constraints are set to query objects that are not allowed an error gets raised.

    This function also sets parent objects.

    NOTE: we expect an abject for whom we demand a breakdown is already checked and allowed - eg. account, campaign,
    ad group.

    NOTE: show_archived filter is primarily applied here, we used it elsewhere only for minor adjustments.
    """

    constraints = {
        'date__gte': start_date,
        'date__lte': end_date,
        'show_archived': show_archived,
    }

    if filtered_agencies:
        constraints['filtered_agencies'] = filtered_agencies

    if filtered_account_types:
        constraints['filtered_account_types'] = filtered_account_types

    # only one can be set
    if len([x for x in (account, campaign, ad_group) if x is not None]) > 1:
        raise Exception("Only account, campaign, or ad_group can be set")

    allowed_campaigns = dash.models.Campaign.objects.all()\
                                                    .filter_by_user(user)\
                                                    .filter_by_sources(filtered_sources)\
                                                    .filter_by_agencies(filtered_agencies)\
                                                    .filter_by_account_types(filtered_account_types)\
                                                    .exclude_archived(show_archived)

    target_dimension = constants.get_target_dimension(breakdown)
    if account:
        constraints['account'] = account
        allowed_campaigns = allowed_campaigns.filter(account_id=account.id)
        constraints['allowed_campaigns'] = allowed_campaigns
        constraints['allowed_ad_groups'] = dash.models.AdGroup.objects.filter(campaign__in=allowed_campaigns)\
                                                                      .exclude_archived(show_archived)
        # add also inactive ad group sources as we need to query all. We remove them later
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__campaign__account_id=account.id)

    elif campaign:
        constraints['campaign'] = campaign
        constraints['account'] = campaign.account
        allowed_ad_groups = campaign.adgroup_set.all().exclude_archived(show_archived)
        constraints['allowed_ad_groups'] = allowed_ad_groups
        constraints['allowed_content_ads'] = dash.models.ContentAd.objects.filter(ad_group__in=allowed_ad_groups)\
                                                                          .exclude_archived(show_archived)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__campaign_id=campaign.id)

    elif ad_group:
        constraints['ad_group'] = ad_group
        constraints['campaign'] = ad_group.campaign
        constraints['account'] = ad_group.campaign.account
        constraints['allowed_content_ads'] = dash.models.ContentAd.objects.filter(ad_group=ad_group)\
                                                                          .exclude_archived(show_archived)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group_id=ad_group.id)

    # base safety
    if not constraints.get('account'):
        allowed_accounts = dash.models.Account.objects.all()\
                                                      .filter_by_user(user)\
                                                      .filter_by_sources(filtered_sources)\
                                                      .filter_by_agencies(filtered_agencies)\
                                                      .filter_by_account_types(filtered_account_types)\
                                                      .exclude_archived(show_archived)
        constraints['allowed_accounts'] = allowed_accounts
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__campaign__account__in=allowed_accounts)

    if not constraints.get('campaign'):
        if level != Level.ALL_ACCOUNTS or 'campaign_id' in breakdown:
            constraints['allowed_campaigns'] = allowed_campaigns

    constraints['filtered_sources'] = filtered_sources.filter(
        pk__in=ad_group_sources.distinct('source_id').values_list('source_id', flat=True))
    return constraints


def get_goals(constraints):
    campaign = constraints.get('campaign')
    account = constraints.get('account')

    campaign_goals, conversion_goals, campaign_goal_values, pixels = [], [], [], []
    primary_goal = None

    if campaign:
        conversion_goals = campaign.conversiongoal_set.all().select_related('pixel')
        campaign_goals = campaign.campaigngoal_set.all().order_by('-primary', 'created_dt').select_related(
            'conversion_goal', 'conversion_goal__pixel')
        primary_goal = campaign_goals.first()
        campaign_goal_values = dash.campaign_goals.get_campaign_goal_values(campaign)

    if account:
        pixels = account.conversionpixel_set.filter(archived=False)

    return Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, primary_goal)


def extract_stats_constraints(constraints, breakdown):
    """
    Copy constraints and remove all that are not part of the stats query.
    """

    new_constraints = {
        'date__gte': constraints['date__gte'],
        'date__lte': constraints['date__lte'],
        'source_id': list(constraints['filtered_sources'].values_list('pk', flat=True)),
        'account_id': (constraints['account'].id if 'account' in constraints else
                       list(constraints['allowed_accounts'].values_list('pk', flat=True))),
    }

    if 'ad_group' in constraints:
        new_constraints['ad_group_id'] = constraints['ad_group'].id
    elif 'ad_group_id' in breakdown:
        new_constraints['ad_group_id'] = list(constraints['allowed_ad_groups'].values_list('pk', flat=True))

    if 'campaign' in constraints:
        new_constraints['campaign_id'] = constraints['campaign'].id
    elif 'campaign_id' in breakdown:
        new_constraints['campaign_id'] = list(constraints['allowed_campaigns'].values_list('pk', flat=True))

    if 'account' in constraints:
        new_constraints['account_id'] = constraints['account'].id

    if 'content_ad_id' in breakdown:
        new_constraints['content_ad_id'] = list(constraints['allowed_content_ads'].values_list('pk', flat=True))

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


def get_breakdown_id_tuple(row, breakdown):
    d = []
    for dim in breakdown:
        d.append(row[dim])
    return tuple(d)


def get_breakdown_id(row, breakdown):
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
                      'allowed_campaigns', 'allowed_ad_groups', 'allowed_content_ads']

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

    other_keys = ['show_archived', 'filtered_account_types', 'date__gte', 'date__lte']
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

    if target_dimension == 'publisher' and order_field in ('state', 'status'):
        return prefix + "clicks"

    return order


def extract_order_field(order, target_dimension, primary_goal=None):
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
        if primary_goal:
            order_field = 'performance_' + primary_goal.get_view_key()
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

    if target_dimension == 'publisher' and order_field == 'name':
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


def group_rows_by_breakdown(breakdown, rows):
    groups = collections.defaultdict(list)

    for row in rows:
        groups[get_breakdown_id_tuple(row, breakdown)].append(row)

    return groups


def should_query_dashapi_first(order, target_dimension):
    _, order_field = sort_helper.dissect_order(order)

    if (order_field == 'name' and
       target_dimension in constants.StructureDimension._ALL and
       target_dimension != constants.StructureDimension.PUBLISHER):
        return True

    if order_field == 'status' and target_dimension in constants.StructureDimension._ALL:
        return True

    if order_field in SOURCE_FIELDS and target_dimension == 'source_id':
        return True

    return False


def should_augment_by_dash(target_dimension):
    return target_dimension in constants.StructureDimension._ALL
