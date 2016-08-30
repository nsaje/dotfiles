import copy

from django.db.models import QuerySet, Model

from utils import sort_helper
from utils import exc

from stats import constants
from reports.db_raw_helpers import extract_obj_ids


def extract_stats_constraints(constraints):
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

    if 'campaign' in constraints:
        new_constraints['campaign_id'] = constraints['campaign'].id
    elif 'allowed_campaigns' in constraints:
        new_constraints['campaign_id'] = list(constraints['allowed_campaigns'].values_list('pk', flat=True))

    if 'account' in constraints:
        new_constraints['account_id'] = constraints['account'].id

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


def extract_order_field(order, breakdown):
    target_dimension = constants.get_target_dimension(breakdown)
    if target_dimension in constants.TimeDimension._ALL or target_dimension in ('age', 'age_gender', 'device_type'):
        return target_dimension

    prefix, order_field = sort_helper.dissect_order(order)

    if order_field in constants.SpecialDimensionNameKeys:
        order = prefix + constants.get_dimension_name_key(order_field)

    return order


def check_constraints_are_supported(constraints):
    """
    Checks whether constraints include only known keys of known types.
    This way we check for programming mistakes.
    """

    query_set_keys = ['filtered_sources', 'filtered_agencies',
                      'allowed_accounts', 'allowed_campaigns']

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


# FIXME: Remove this hack
def get_supported_order(order):
    prefix, order_field = sort_helper.dissect_order(order)

    if order_field == 'cost':
        # cost is not supported anymore, this case needs to be handled in case this sort was cached in browser
        return prefix + 'media_cost'

    UNSUPPORTED_FIELDS = [
        "name", "state", "status", "performance",
        "min_bid_cpc", "max_bid_cpc", "daily_budget",
        "pacing", "allocated_budgets", "spend_projection",
        "license_fee_projection", "upload_time",
    ] + [v for _, v in constants.SpecialDimensionNameKeys.items()]

    if order_field in UNSUPPORTED_FIELDS:
        return "-clicks"

    return order
