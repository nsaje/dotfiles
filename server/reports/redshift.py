import collections
from itertools import repeat

from django.conf import settings
from django.db import connections
from django.db.models import Sum
from django.db.models.query import QuerySet

from utils.statsd_helper import statsd_timer

from utils import db_aggregates

from reports import exc
from reports.db_raw_helpers import dictfetchall, get_obj_id, quote


@statsd_timer('reports.redshift', 'delete_contentadstats')
def delete_contentadstats(date, ad_group_id, source_id):
    cursor = _get_cursor()

    query = 'DELETE FROM contentadstats WHERE date = %s AND adgroup_id = %s'
    params = [date.isoformat(), ad_group_id]

    if source_id:
        query = query + ' AND source_id = %s'
        params.append(source_id)

    cursor.execute(query, params)
    cursor.close()


@statsd_timer('reports.redshift', 'delete_contentadstats')
def delete_touchpoint_conversions(date):
    cursor = _get_cursor()

    query = 'DELETE FROM touchpointconversions WHERE date = %s'
    params = [date.isoformat()]

    cursor.execute(query, params)
    cursor.close()


@statsd_timer('reports.redshift', 'insert_contentadstats')
def insert_contentadstats(rows):
    if not rows:
        return

    cursor = _get_cursor()

    cols = rows[0].keys()

    query = 'INSERT INTO contentadstats ({cols}) VALUES {rows}'.format(
        cols=','.join(cols),
        rows=','.join(_get_row_string(cursor, cols, row) for row in rows))

    cursor.execute(query, [])
    cursor.close()


@statsd_timer('reports.redshift', 'insert_touchpointconversions')
def insert_touchpoint_conversions(rows):
    if not rows:
        return

    cursor = _get_cursor()

    cols = rows[0].keys()

    query = 'INSERT INTO touchpointconversions ({cols}) VALUES {rows}'.format(
        cols=','.join(cols),
        rows=','.join(_get_row_string(cursor, cols, row) for row in rows))

    cursor.execute(query, [])
    cursor.close()


@statsd_timer('reports.redshift', 'sum_contentadstats')
def sum_contentadstats():
    query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    result = dictfetchall(cursor)

    cursor.close()
    return result[0]


@statsd_timer('reports.redshift', 'get_pixel_last_verified_dt')
def get_pixels_last_verified_dt(account_id=None):
    query = 'SELECT account_id, slug, max(conversion_timestamp) FROM touchpointconversions'
    params = []
    if account_id:
        query += ' WHERE account_id = %s'
        params.append(account_id)

    query += ' GROUP BY slug, account_id'

    cursor = _get_cursor()
    cursor.execute(query, params)

    result = cursor.fetchall()
    cursor.close()

    return {(row[0], row[1]): row[2] for row in result}


@statsd_timer('reports.redshift', 'vacuum_contentadstats')
def vacuum_contentadstats():
    query = 'VACUUM FULL contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    cursor.close()


def query_contentadstats(start_date, end_date, aggregates, field_mapping, breakdown=None, **constraints):

    constraints = _prepare_constraints(constraints, field_mapping)
    constraints.append('{} >= \'{}\''.format(quote('date'), start_date))
    constraints.append('{} <= \'{}\''.format(quote('date'), end_date))

    aggregates = _prepare_aggregates(aggregates, field_mapping)

    reverse_field_mapping = {v: k for k, v in field_mapping.iteritems()}

    if breakdown:
        breakdown = _prepare_breakdown(breakdown, field_mapping)
        statement = _create_select_query(
            'contentadstats',
            breakdown + aggregates,
            constraints,
            breakdown
        )

        results = _get_results(statement)
        return [_translate_row(row, reverse_field_mapping) for row in results]

    statement = _create_select_query(
        'contentadstats',
        aggregates,
        constraints
    )

    results = _get_results(statement)

    return _translate_row(results[0], reverse_field_mapping)


def query_publishers(start_date, end_date, aggregates, field_mapping, breakdown=None, **constraints):

    constraints = _prepare_constraints(constraints, field_mapping)
    constraints.append('{} >= \'{}\''.format(quote('date'), start_date))
    constraints.append('{} <= \'{}\''.format(quote('date'), end_date))

    aggregates = _prepare_aggregates(aggregates, field_mapping, hack=False)

    reverse_field_mapping = {v: k for k, v in field_mapping.iteritems()}

    if breakdown:
        breakdown = _prepare_breakdown(breakdown, field_mapping)
        statement = _create_select_query(
            'b1_publishers_1',
            breakdown + aggregates,
            constraints,
            breakdown
        )

        results = _get_results(statement)
        return [_translate_row(row, reverse_field_mapping) for row in results]

    statement = _create_select_query(
        'b1_publishers_1',
        aggregates,
        constraints
    )

    results = _get_results(statement)

    return _translate_row(results[0], reverse_field_mapping)


def _prepare_constraints(constraints, field_mapping):
    result = []

    def quote_if_str(val):
        if isinstance(val, str):
            return quote(val)
        return str(val)

    for k, v in constraints.iteritems():
        k = quote(field_mapping.get(k, k))

        if isinstance(v, collections.Sequence) or isinstance(v, QuerySet):
            if v:
                result.append('{} IN ({})'.format(k, ','.join([quote_if_str(get_obj_id(x)) for x in v])))
            else:
                result.append('FALSE')
        else:
            result.append('{}={}'.format(k, quote_if_str(get_obj_id(v))))

    return result


def _prepare_aggregates(aggregates, field_mapping, hack = True):
    processed_aggrs = []
    for key, aggr in aggregates.iteritems():
        field_name = aggr.input_field.name
        field_name = field_mapping.get(field_name, field_name)
        if isinstance(aggr, db_aggregates.SumDivision):
            divisor = aggr.extra['divisor']
            divisor = field_mapping.get(divisor, divisor)
            processed_aggrs.append(_sum_division_aggregate(field_name, divisor, key))
        elif isinstance(aggr, Sum):
            processed_aggrs.append(_sum_aggregate(field_name, key))
        else:
            raise exc.ReportsUnknownAggregator('Unknown aggregator')

    # HACK: should be added to aggregate_fields
    if hack:
        # SOMEONE PLEASE REMOVE THIS HACK
        processed_aggrs.append(_click_discrepancy_aggregate('clicks', 'visits', 'click_discrepancy'))

    return processed_aggrs


def _prepare_breakdown(breakdown, field_mapping):
    return [quote(field_mapping.get(field, field)) for field in breakdown]


def _translate_row(row, reverse_field_mapping):
    return {reverse_field_mapping.get(k, k): v for k, v in row.iteritems()}


def _create_select_query(table, fields, constraints, breakdown=None):
    group_by = ''
    if breakdown:
        group_by = 'GROUP BY {}'.format(','.join(breakdown))
    return 'SELECT {fields} FROM {table} WHERE {constraints} {group_by}'.format(
        fields=','.join(fields),
        table=table,
        constraints=' AND '.join(constraints),
        group_by=group_by
    )


def _click_discrepancy_aggregate(clicks_col, visits_col, stat_name):
    return ('CASE WHEN SUM({clicks}) = 0 THEN NULL WHEN SUM({visits}) = 0 THEN 1'
            ' WHEN SUM({clicks}) < SUM({visits}) THEN 0'
            ' ELSE (SUM(CAST({clicks} AS FLOAT)) - SUM({visits})) / SUM({clicks})'
            ' END as {stat_name}').format(
                clicks=quote(clicks_col),
                visits=quote(visits_col),
                stat_name=quote(stat_name))


def _sum_division_aggregate(expr, divisor, stat_name):
    return ('CASE WHEN SUM({divisor}) <> 0 THEN SUM(CAST({expr} AS FLOAT)) / SUM({divisor}) '
            'ELSE NULL END as {stat_name}').format(
                expr=quote(expr),
                divisor=quote(divisor),
                stat_name=quote(stat_name))


def _sum_aggregate(expr, stat_name):
    return 'SUM({}) AS {}'.format(quote(expr), quote(stat_name))


@statsd_timer('reports.redshift', 'vacuum_touchpoint_conversions')
def vacuum_touchpoint_conversions():
    query = 'VACUUM FULL touchpointconversions'

    cursor = _get_cursor()
    cursor.execute(query, [])

    cursor.close()


def _get_cursor():
    return connections[settings.STATS_DB_NAME].cursor()


def _get_results(statement):
    cursor = _get_cursor()
    print "XXXX", statement
    cursor.execute(statement, [])

    results = dictfetchall(cursor)

    cursor.close()
    return results


def _get_row_string(cursor, cols, row):
    template_string = '(' + ','.join(repeat('%s', len(cols))) + ')'
    return cursor.mogrify(template_string, [row[col] for col in cols])
