import copy

# remove colums without permissions


def extract_stats_constraints(constraints):
    """
    Remove any constraints that are not part of the stats query.
    """
    constraints = copy.copy(constraints)

    del constraints['show_archived']

    return constraints