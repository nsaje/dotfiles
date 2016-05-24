import backtosql
import datetime
import dateutil

from stats import constants
from utils import exc


def prepare_lvl1_top_rows(default_context):
    """
    Prepares a SQL query for a general 1st level breakdown.
    Breakdown array should be of lenght 2 - base and 1st level breakdown.
    """

    sql = backtosql.generate_sql('breakdown_lvl1_top_rows.sql', default_context)

    params = default_context['constraints'].get_params()

    if not default_context.get('breakdown_constraints'):
        raise exc.MissingBreakdownConstraintsError()

    params.extend(default_context['breakdown_constraints'].get_params())

    return sql, params


def prepare_lvl2_top_rows(default_context):
    """
    Prepares a SQL query for a general 2st level breakdown.
    Breakdown array should be of lenght 3 - base, 1st level and 2nd level breakdown.
    """

    sql = backtosql.generate_sql('breakdown_lvl2_top_rows.sql', default_context)

    params = default_context['constraints'].get_params()

    if not default_context.get('breakdown_constraints'):
        raise exc.MissingBreakdownConstraintsError()

    params.extend(default_context['breakdown_constraints'].get_params())

    return sql, params


def prepare_time_top_rows(model, time_dimension, default_context, constraints, offset, limit):
    """
    Prepares a SQL query for a breakdown where targeted dimension is time.
    """

    _prepare_time_constraints(time_dimension, constraints, offset, limit)
    default_context['constraints'] = backtosql.Q(model, **constraints)

    # limit and offset are handeled via time constraints
    default_context['offset'] = None
    default_context['limit'] = None

    # when querying time dimension order is always time asc
    default_context['order'] = model.select_order([time_dimension])

    sql = backtosql.generate_sql('breakdown_simple_select.sql', default_context)

    params = default_context['constraints'].get_params()
    if default_context.get('breakdown_constraints'):
        params.extend(default_context['breakdown_constraints'].get_params())

    return sql, params


def _prepare_time_constraints(time_dimension, constraints, offset, limit):
    """
    Sets time constraints so that they fit offset and limit. Instead of
    using SQL offset and limit just adjust the date range so the scan space
    is smaller.
    """

    start_date = constraints['date__gte']

    if time_dimension == constants.TimeDimension.DAY:
        start_date = start_date + datetime.timedelta(days=offset)
        end_date = start_date + datetime.timedelta(days=limit)

    elif time_dimension == constants.TimeDimension.WEEK:
        start_date = start_date + datetime.timedelta(days=7 * offset)
        end_date = start_date + datetime.timedelta(days=7 * limit)

    else:
        start_date = start_date.replace(day=1)
        start_date = start_date + dateutil.relativedelta.relativedelta(months=offset)
        end_date = start_date + dateutil.relativedelta.relativedelta(months=limit)

    constraints['date__gte'] = max(start_date, constraints['date__gte'])
    if min(end_date, constraints['date__lte']) == constraints['date__lte']:
        # end of date range - fetch until the end
        constraints['date__lte'] = constraints['date__lte']
    else:
        # else later ranges are possible
        del constraints['date__lte']
        constraints['date__lt'] = end_date
