import collections
from itertools import repeat

from django.db.models.query import QuerySet

from reports.db_raw_helpers import dictfetchall, get_obj_id, _quote
from utils import db_aggregates
from django.db.models import Sum

from django.db import connections
from django.conf import settings

from utils.statsd_helper import statsd_timer


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


@statsd_timer('reports.redshift', 'sum_contentadstats')
def sum_contentadstats():
    query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    result = dictfetchall(cursor)

    cursor.close()
    return result[0]


@statsd_timer('reports.redshift', 'vacuum_contentadstats')
def vacuum_contentadstats():
    query = 'VACUUM FULL contentadstats'

    cursor = _get_cursor()
    cursor.execute(query, [])

    cursor.close()


def query_contentadstats(start_date, end_date, aggregates, field_mapping, breakdown=None, **constraints):

    print 'REDSHIFT'
    constraints = _prepare_constraints(constraints, field_mapping)
    constraints.append('{} >= \'{}\''.format(_quote('date'), start_date))
    constraints.append('{} <= \'{}\''.format(_quote('date'), end_date))

    aggregates = _prepare_aggregates(aggregates, field_mapping)

    # TODO: could this be precomputed
    reverse_field_mapping = {v: k for k, v in field_mapping.iteritems()}

    if breakdown:
        breakdown = _prepare_breakdown(breakdown, field_mapping)
        statement = _construct_select_statement(
            'contentadstats',
            breakdown + aggregates,
            constraints,
            breakdown
        )

        results = _get_results(statement)
        print 'breakdown', "\n", statement, "\n", results, "\n", [_translate_row(row, reverse_field_mapping) for row in results]
        return [_translate_row(row, reverse_field_mapping) for row in results]

    statement = _construct_select_statement(
        'contentadstats',
        aggregates,
        constraints
    )

    results = _get_results(statement)

    assert len(results) == 1
    print 'aggregate', "\n", statement, "\n", results, "\n", _translate_row(results[0], reverse_field_mapping)
    return _translate_row(results[0], reverse_field_mapping)


def _prepare_constraints(constraints, field_mapping):
    result = []
    for k, v in constraints.iteritems():
        k = _quote(field_mapping.get(k, k))

        if isinstance(v, collections.Sequence) or isinstance(v, QuerySet):
            if v:
                result.append('{} IN ({})'.format(k,
                                                  ','.join([str(get_obj_id(x)) for x in v])))
            else:
                result.append('FALSE')
        else:
            result.append('{}={}'.format(k, get_obj_id(v)))

    return result


def _prepare_aggregates(aggregates, field_mapping):
    processed_aggrs = []
    for key, aggr in aggregates.iteritems():
        field_name = aggr.input_field.name
        field_name = field_mapping.get(field_name, field_name)
        if isinstance(aggr, db_aggregates.SumDivision):
            divisor = aggr.input_field.name
            divisor = field_mapping.get(divisor, divisor)
            processed_aggrs.append(_sum_division_statement(field_name, divisor, key))
        elif isinstance(aggr, Sum):
            processed_aggrs.append(_sum_statement(field_name, key))
        else:
            # TODO: proper exception class
            raise Exception('Unknown aggregator')

    # HACK: should be added to aggregates
    processed_aggrs.append(_click_discrepancy_statement('clicks', 'visits', 'click_discrepancy'))

    return processed_aggrs


def _prepare_breakdown(breakdown, field_mapping):
    return [_quote(field_mapping.get(field, field)) for field in breakdown]


def _translate_row(row, reverse_field_mapping):
    return {reverse_field_mapping.get(k, k): v for k, v in row.iteritems()}


def _construct_select_statement(table, fields, constraints, breakdown=None):
    group_by = ''
    if breakdown:
        group_by = 'GROUP BY {}'.format(','.join(breakdown))
    return 'SELECT {fields} FROM {table} WHERE {constraints} {group_by}'.format(
        fields=','.join(fields),
        table=table,
        constraints=' AND '.join(constraints),
        group_by=group_by
    )


def _click_discrepancy_statement(clicks_col, visits_col, stat_name):
    return ('CASE WHEN SUM({clicks}) = 0 THEN NULL WHEN SUM({visits}) = 0 THEN 1'
            ' WHEN SUM({clicks}) < SUM({visits}) THEN 0'
            ' ELSE SUM(CAST({clicks} AS FLOAT)) - SUM({visits}) / SUM({clicks})'
            ' END as {stat_name}').format(
                clicks=_quote(clicks_col),
                visits=_quote(visits_col),
                stat_name=_quote(stat_name))


def _sum_division_statement(expr, divisor, stat_name):
    # TODO: needs a better name?
    return ('CASE WHEN SUM({divisor}) <> 0 THEN SUM(CAST({expr} AS FLOAT)) / SUM({divisor}) '
            'ELSE NULL END as {stat_name}').format(
                expr=_quote(expr),
                divisor=_quote(divisor),
                stat_name=_quote(stat_name))


def _sum_statement(expr, stat_name):
    # TODO: needs a better name?
    return 'SUM({}) AS {}'.format(_quote(expr), _quote(stat_name))


def _get_cursor():
    return connections[settings.STATS_DB_NAME].cursor()


def _get_results(statement):
    cursor = _get_cursor()
    cursor.execute(statement, [])

    results = dictfetchall(cursor)

    cursor.close()
    return results


def _get_row_string(cursor, cols, row):
    template_string = '(' + ','.join(repeat('%s', len(cols))) + ')'
    return cursor.mogrify(template_string, [row[col] for col in cols])
