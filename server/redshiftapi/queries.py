import backtosql
import datetime
import dateutil

from stats import constants


def prepare_lvl1_top_rows(default_context):
    sql = backtosql.generate_sql('breakdown_lvl1_top_rows.sql', defaultcontext)

    params = default_context['constraints'].get_params()

    # TODO this query requires breakdown_constraints to work correctly
    if default_context['breakdown_constraints']:
        params.extend(default_context['breakdown_constraints'].get_params())

    return sql, params


def prepare_lvl2_top_rows(default_context):
    sql = backtosql.generate_sql('breakdown_lvl2_top_rows.sql', default_context)

    params = default_context['constraints'].get_params()

    # TODO this query requires breakdown_constraints to work correctly
    if default_context['breakdown_constraints']:
        params.extend(default_context['breakdown_constraints'].get_params())

    return sql, params


def prepare_time_top_rows(model, time_dimension, default_context, constraints, offset, limit):

    _prepare_time_constraints(time_dimension, constraints, offset, limit)
    default_context['constraints'] = backtosql.Q(cls, **constraints)

    sql = backtosql.generate_sql('breakdown_simple_select.sql', default_context)

    params = default_context['constraints'].get_params()
    if default_context['breakdown_constraints']:
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
        end_date = start_date + datetime.timedelta(days=(limit - offset))

    if time_dimension == constants.TimeDimension.WEEK:
        start_date = start_date + datetime.timedelta(days=7 * offset)
        end_date = start_date + datetime.timedelta(days=7 * (limit - offset))

    if time_dimension == constants.TimeDimension.MONTH:
        start_date = start_date + dateutil.relativedelta.relativedelta(months=offset)
        end_date = start_date + dateutil.relativedelta.relativedelta(months=(limit - offset))

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date
