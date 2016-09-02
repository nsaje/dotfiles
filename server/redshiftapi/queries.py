import backtosql
import datetime
import dateutil

from stats import constants
from utils import exc

from redshiftapi import models


def prepare_breakdown_query(model, breakdown, constraints, parents, order, offset, limit):
    target_dimension = constants.get_target_dimension(breakdown)
    default_context = model.get_default_context(breakdown, constraints, parents, order, offset, limit)

    if target_dimension in constants.TimeDimension._ALL:
        # should also cover the case for len(breakdown) == 4 because in that case time dimension should be the last one
        time_dimension = constants.get_time_dimension(breakdown)
        return prepare_breakdown_time_top_rows(model, time_dimension, default_context, constraints)

    if len(breakdown) == 0:
        # only totals
        return prepare_breakdown_top_rows(default_context)

    if len(breakdown) == 1:
        # base level
        return prepare_breakdown_top_rows(default_context)

    if 2 <= len(breakdown) <= 3:
        return prepare_breakdown_struct_delivery_top_rows(default_context)

    raise exc.InvalidBreakdownError("Selected breakdown is not supported {}".format(breakdown))


def prepare_augment_query(model, breakdown, constraints, parents):
    default_context = model.get_default_context(breakdown, constraints, parents)
    return prepare_breakdown_top_rows(default_context)


def prepare_query_structure_with_stats_query(model, breakdown, constraints):
    default_context = model.get_default_context(breakdown, constraints, None)
    sql = backtosql.generate_sql('breakdown_structure_with_stats.sql', default_context)
    params = default_context['constraints'].get_params()
    return sql, params


def prepare_breakdown_top_rows(default_context):
    """
    Prepares a SQL query for base level or totals.
    """

    if not default_context.get('breakdown') and default_context.get('order'):
        # remove order as it is not necessary when there is no breakdown
        default_context.pop('order')

    sql = backtosql.generate_sql('breakdown_top_rows.sql', default_context)

    params = default_context['constraints'].get_params()
    if default_context.get('parent_constraints'):
        params.extend(default_context['parent_constraints'].get_params())

    yesterday_params = []
    if 'yesterday_constraints' in default_context:
        yesterday_params = default_context['yesterday_constraints'].get_params()
        if default_context.get('parent_constraints'):
            yesterday_params.extend(default_context['parent_constraints'].get_params())

    conversion_params = []
    if default_context.get('conversions_aggregates'):
        conversion_params.extend(params)

    if default_context.get('touchpointconversions_aggregates'):
        conversion_params.extend(params)

    # conversion queries are ordered before the base query
    params = conversion_params + yesterday_params + params

    return sql, params


def prepare_breakdown_struct_delivery_top_rows(default_context):
    """
    Prepares a SQL query for a general 1st level breakdown.
    Breakdown array should be of lenght 2 - base and 1st level breakdown.
    """

    sql = backtosql.generate_sql('breakdown_struct_delivery_top_rows.sql', default_context)

    params = default_context['constraints'].get_params()
    if not default_context.get('parent_constraints'):
        raise exc.MissingBreakdownConstraintsError()

    params.extend(default_context['parent_constraints'].get_params())

    yesterday_params = []
    if 'yesterday_constraints' in default_context:
        yesterday_params = default_context['yesterday_constraints'].get_params()
        yesterday_params.extend(default_context['parent_constraints'].get_params())

    conversion_params = []
    if default_context.get('conversions_aggregates'):
        conversion_params.extend(params)

    if default_context.get('touchpointconversions_aggregates'):
        conversion_params.extend(params)

    # conversion queries are ordered before the base query
    params = conversion_params + yesterday_params + params

    return sql, params


def prepare_breakdown_time_top_rows(model, time_dimension, default_context, constraints):
    """
    Prepares a SQL query for a breakdown where targeted dimension is time.
    """

    offset = default_context['offset']
    limit = default_context['limit']

    _prepare_time_constraints(time_dimension, constraints, offset, limit)

    # prepare yesterday context for the modified constraints
    default_context.pop('yesterday_constraints', None)
    yesterday_context = models.get_default_yesterday_context(model, constraints, default_context['order'])
    default_context.update(yesterday_context)

    default_context['constraints'] = backtosql.Q(model, **constraints)

    # limit and offset are handeled via time constraints
    default_context['offset'] = None
    default_context['limit'] = None

    default_context['is_ordered_by_conversions'] = False
    default_context['is_ordered_by_touchpointconversions'] = False
    default_context['is_ordered_by_after_join_conversions_calculations'] = False
    default_context['is_ordered_by_yesterday_aggregates'] = False

    sql = backtosql.generate_sql('breakdown_top_rows.sql', default_context)

    params = default_context['constraints'].get_params()
    yesterday_params = []
    if 'yesterday_constraints' in default_context:
        yesterday_params = default_context['yesterday_constraints'].get_params()

    if default_context.get('parent_constraints'):
        params.extend(default_context['parent_constraints'].get_params())

        if 'yesterday_constraints' in default_context:
            yesterday_params.extend(default_context['parent_constraints'].get_params())

    conversion_params = []
    if default_context.get('conversions_aggregates'):
        conversion_params.extend(params)

    if default_context.get('touchpointconversions_aggregates'):
        conversion_params.extend(params)

    # conversion queries are ordered before the base query
    params = conversion_params + yesterday_params + params

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
        constraints['date__lte'] = end_date - datetime.timedelta(days=1)
