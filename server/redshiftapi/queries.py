import backtosql
import datetime
from dateutil import rrule, relativedelta

from stats import constants


def prepare_lvl1_top_rows(model, breakdown, constraints, breakdown_constraints,
                          order, offset, limit):

    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, offset, limit)

    sql = backtosql.generate_sql('breakdown_lvl1_top_rows.sql', context)

    params = context['constraints'].get_params()
    # TODO requires breakdown_constraints
    if context['breakdown_constraints']:
        params.extend(context['breakdown_constraints'].get_params())

    return sql, params


def prepare_lvl2_top_rows(model, breakdown, constraints, breakdown_constraints,
                          order, offset, limit):
    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, offset, limit)

    sql = backtosql.generate_sql('breakdown_lvl2_top_rows.sql', context)

    params = context['constraints'].get_params()
    # TODO requires breakdown_constraints
    if context['breakdown_constraints']:
        params.extend(context['breakdown_constraints'].get_params())

    return sql, params


def prepare_time_top_rows(model, time_dimension, breakdown, constraints, breakdown_constraints,
                          order, offset, limit):

    _prepare_time_constraints(time_dimension, constraints, offset, limit)
    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, offset, limit)

    sql = backtosql.generate_sql('breakdown_simple_select.sql', context)

    params = context['constraints'].get_params()
    if context['breakdown_constraints']:
        params.extend(context['breakdown_constraints'].get_params())

    return sql, params


def _get_default_context(model, breakdown, constraints, breakdown_constraints,
                         order, offset, limit):
    """
    Returns the template context that is used by most of templates
    """

    constraints = backtosql.Q(model, **constraints)
    breakdown_constraints = _prepare_breakdown_constraints(model, breakdown_constraints)

    context = {
        'view': model.get_best_view(breakdown),
        'breakdown': model.get_breakdown(breakdown),
        'constraints': constraints,
        'breakdown_constraints': breakdown_constraints,
        'aggregates': model.get_aggregates(),
        'order': model.select_order([order]),
        'offset': offset,
        'limit': limit,
    }

    return context


def _prepare_breakdown_constraints(model, breakdown_constraints):
    """
    Create OR separated AND statements based on breakdown_constraints.
    Eg.:

    (a AND b) OR (c AND d)
    """
    if not breakdown_constraints:
        return None

    bq = backtosql.Q(model, **breakdown_constraints[0])

    for branch in breakdown_constraints[1:]:
        bq |= backtosql.Q(model, **branch)

    return bq

def _prepare_time_constraints(time_dimension, constraints, offset, limit):
    # TODO there is no limit on max date span here, just another page
    # TODO this doesn';t work
    if True:
        return

    start_date = constraints['date__gte']

    start_idx = (page - 1) * limit
    if time_dimension == constants.TimeDimension.WEEK:
        start_date = start_date + datetime.timedelta(days=7*start_idx)
        end_date = start_date + datetime.timedelta(days=7*limit)
    elif time_dimension == constants.TimeDimension.MONTH:
        start_date = start_date + relativedelta.relativedelta(months=+start_idx)
        end_date = start_date + relativedelta.relativedelta(months=limit)
    else:
        start_date = start_date + datetime.timedelta(days=start_idx)
        end_date = start_date + datetime.timedelta(days=limit)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = min(end_date, constraints['date__lte'])