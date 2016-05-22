import copy

from stats import constants
from reports.db_raw_helpers import extract_obj_ids


def extract_stats_constraints(constraints):
    """
    Copy constraints and remove all that are not part of the stats query.
    """

    new_constraints = copy.copy(constraints)

    del new_constraints['show_archived']

    # replace 'account' with 'account_id' etc
    for k, v in constraints.items():
        if k in constants.SpecialDimensionIdentificators:
            new_constraints[constants.get_dimension_identifier(k)] = extract_obj_ids(v)
            del new_constraints[k]

    return new_constraints


def extract_stats_breakdown_constraints(breakdown, breakdown_page):
    """
    Returns a list of parsed breakdown_ids or None.
    """

    if not breakdown_page:
        return None

    return [extract_breakdown_id(breakdown, breakdown_id_str) for breakdown_id_str in breakdown_page]


def extract_stats_breakdown(breakdown):
    return [constants.get_dimension_identifier(dimension) for dimension in breakdown]


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
    ids = breakdown_id_str.split("-")
    for i, dimension in enumerate(breakdown[:len(ids)]):
        str_id = ids[i]
        str_id = int(str_id) if dimension in constants.IntegerDimensions else str_id

        d[constants.get_dimension_identifier(dimension)] = str_id

    return d


def create_breakdown_id(breakdown, row):
    """
    Creates a breakdown id - string of consecutive ids separated by delimiter.

    Example:
    breakdown = [account, campaign, dma, day]
    row = {account_id: 1, campaign_id: 2, dma: '500', clicks: 123, ...}

    Returns: '1-2-500'
    """
    return "-".join(str(row[constants.get_dimension_identifier(dimension)]) for dimension in breakdown)
