
import backtosql
import datetime
from dateutil import rrule, relativedelta
from dash import breakdown_helpers


def prepare_lvl1_top_rows(model, breakdown, constraints, breakdown_constraints,
                          order, page, page_size):

    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, page, page_size)

    sql = backtosql.generate_sql('breakdown_lvl1_top_rows.sql', context)

    params = context['constraints'].get_params()

    return sql, params


def prepare_lvl2_top_rows(model, breakdown, constraints, breakdown_constraints,
                          order, page, page_size):
    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, page, page_size)

    sql = backtosql.generate_sql('breakdown_lvl2_top_rows.sql', context)

    # this is template specific - based on what comes first
    params = context['constraints'].get_params()
    params.extend(context['breakdown_constraints'].get_params())

    return sql, params


def prepare_time_top_rows(model, time_dimension, breakdown, constraints, breakdown_constraints,
                          order, page, page_size):

    _prepare_time_constraints(time_dimension, constraints, page, page_size)
    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, page, page_size)

    sql = backtosql.generate_sql('breakdown_simple_select.sql', context)

    params = context['constraints'].get_params()
    if context['breakdown_constraints']:
        params.extend(context['breakdown_constraints'].get_params())

    print 'CONTEXT', context

    return sql, params


def _get_default_context(model, breakdown, constraints, breakdown_constraints,
                         order, page, page_size):
    """
    Returns the template context that is used by most of templates
    """

    constraints = backtosql.Q(model, **constraints)
    breakdown_constraints = _prepare_breakdown_constraints(breakdown_constraints)

    context = {
        'view': model.get_best_view(breakdown),
        'breakdown': model.get_breakdown(breakdown),
        'constraints': constraints,
        'breakdown_constraints': breakdown_constraints,
        'aggregates': model.get_aggregates(),
        'order': model.select_order(order),
        'offset': (page - 1) * page_size,
        'limit': page * page_size,
    }

    return context


def _prepare_breakdown_constraints(breakdown_constraints):
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

def _prepare_time_constraints(time_dimension, constraints, page, page_size):

    # TODO there is no limit on max date span here, just another page
    start_date = constraints['date__gte']

    start_idx = (page - 1) * page_size
    if time_dimension == breakdown_helpers.TimeDimension.WEEK:
        start_date = start_date + datetime.timedelta(days=7*start_idx)
        end_date = start_date + datetime.timedelta(days=7*page_size)
    elif time_dimension == breakdown_helpers.TimeDimension.MONTH:
        start_date = start_date + relativedelta.relativedelta(months=+start_idx)
        end_date = start_date + relativedelta.relativedelta(months=page_size)
    else:
        start_date = start_date + datetime.timedelta(days=start_idx)
        end_date = start_date + datetime.timedelta(days=page_size)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = min(end_date, constraints['date__lte'])