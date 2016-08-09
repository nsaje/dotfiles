import copy

from utils import sort_helper

from stats import constants
from reports.db_raw_helpers import extract_obj_ids


def extract_stats_constraints(constraints):
    """
    Copy constraints and remove all that are not part of the stats query.
    """

    new_constraints = copy.copy(constraints)

    filtered_sources = new_constraints.pop('filtered_sources', [])
    new_constraints['source_id'] = [x.pk for x in filtered_sources]

    for removed in ('show_archived', 'filtered_agencies', 'filtered_account_types'):
        new_constraints.pop(removed, None)

    return new_constraints


def extract_stats_breakdown_constraints(breakdown, breakdown_page):
    """
    Returns a list of parsed breakdown_ids or None.
    """

    if not breakdown_page:
        return None

    return [extract_breakdown_id(breakdown, breakdown_id_str) for breakdown_id_str in breakdown_page]


# TODO breakdown_id might need different delimiter
def extract_breakdown_id(breakdown, breakdown_id_str):
    """
    Creates a dict with constraints for a breakdown page.

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


def create_breakdown_id(breakdown, row):
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
