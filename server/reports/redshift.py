import collections
import itertools

from django.conf import settings
from django.db import connections
from django.db.models import Sum
from django.db.models.query import QuerySet

from utils.statsd_helper import statsd_timer

from utils import db_aggregates

from reports import exc
from reports.db_raw_helpers import get_obj_id, quote, dictfetchall

from psycopg2.extensions import adapt as sqladapt


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
        rows=','.join(str(_get_row_string(cursor, cols, row)) for row in rows))

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


def query_contentadstats(start_date, end_date, aggregates, field_mapping, breakdown=None, constraints={}):

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


def _prepare_constraints(constraints, field_mapping):
    result = []

    def quote_if_str(val):
        if isinstance(val, str) or isinstance(val, unicode):
            return sqladapt(val).getquoted()
        else:
            # TODO, this is dangerous, we need to have an explicit list of types that are castable
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


def _prepare_aggregates(aggregates, field_mapping):
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
    processed_aggrs.append(_click_discrepancy_aggregate('clicks', 'visits', 'click_discrepancy'))

    return processed_aggrs


def _prepare_breakdown(breakdown, field_mapping):
    return [quote(field_mapping.get(field, field)) for field in breakdown]


def _translate_row(row, reverse_field_mapping):
    return {reverse_field_mapping.get(k, k): v for k, v in row.iteritems()}


def _create_select_query(table, fields, constraints, breakdown=None):
    cmd = 'SELECT {fields} FROM {table} WHERE {constraints}'.format(
        fields=','.join(fields),
        table=table,
        constraints=' AND '.join(constraints),
    )

    if breakdown:
        cmd += ' GROUP BY {}'.format(','.join(breakdown))

    return cmd


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


def _get_results(statement, args=None):
    cursor = _get_cursor()
    if args is None:
        args = []
    cursor.execute(statement, args)

    results = dictfetchall(cursor)
    cursor.close()
    return results


def _get_row_string(cursor, cols, row):
    template_string = '(' + ','.join(itertools.repeat('%s', len(cols))) + ')'
    return cursor.mogrify(template_string, [row[col] for col in cols])

# New style API


# iterate in chunks, python recepie
def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk

# In order to make testing easier, we abstract all the DB interactions
class MyCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, statement, params):
        self.cursor.execute(statement, params)

    def dictfetchall(self):
        desc = self.cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in self.cursor.fetchall()
        ]
        
    def close(self):
        self.cursor.close()


class RSModel(object):
    FIELDS = []
    TABLE_NAME = "test_table"

    def __init__(self):
        # set-up lookup tables
        self.by_sql_mapping = {d['sql']: d for d in self.FIELDS}
        self.by_app_mapping = {d['app']: d for d in self.FIELDS}

        # by default all fields are allowed as constraints
        self.constraints_fields_app = set(self.by_app_mapping.keys())

    def translate_app_fields(self, field_names):
        return [self.by_app_mapping[field_name]['sql'] for field_name in field_names]

    def expand_returned_sql_fields(self, field_names):
        fields = []
        for field_name in field_names:
            desc = self.by_sql_mapping[field_name]
            if "calc" in desc:
                field_expanded = desc["calc"] + " AS \"" + field_name + "\""
            else:
                field_expanded = '"' + field_name + '"'
            fields.append(field_expanded)
        return fields

    def translate_breakdown_fields(self, breakdown_fields):
        unknown_fields = set(breakdown_fields) - self.ALLOWED_BREAKDOWN_FIELDS_APP
        if unknown_fields:
            raise exc.ReportsQueryError('Invalid breakdowns: {}'.format(str(unknown_fields)))
        breakdown_fields = self.translate_app_fields(breakdown_fields)
        return breakdown_fields

    def translate_order_fields(self, order_fields):
        # Order fields have speciality -- a possiblity of - in front of them
        # map order fields, we decode directions here too
        # we also support specifying order functions to be used instead of field name
        # due to Redshift's inability to use aliased name inside expressions in ORDER BY
        order_fields_out = []
        for field in order_fields:
            direction = "ASC"
            if field.startswith("-"):
                direction = "DESC"
                field = field[1:]

            try:
                field_desc = self.by_app_mapping[field]
            except KeyError:
                raise exc.ReportsQueryError('Invalid field to order by: {}'.format(field))

            try:
                order_statement = field_desc['order'].format(direction=direction)
            except KeyError:
                order_statement = field_desc['sql'] + " " + direction

            order_fields_out.append(order_statement)

        return order_fields_out

    def translate_constraints(self, constraints):
        constraint_tuples = []
        for constraint_name, val in constraints.iteritems():
            parts = constraint_name.split("__")
            field_name_app = parts[0]
            if field_name_app not in self.constraints_fields_app:
                raise exc.ReportsQueryError("Unsupported field constraint fields: {}".format(field_name_app))
            field_name_sql = self.by_app_mapping[field_name_app]['sql']

            if len(parts) == 2:
                operator = parts[1]
            else:
                operator = "eq"

            constraint_tuples.append((field_name_sql, operator, val))
        return constraint_tuples

    def get_returned_fields(self, returned_fields):
        return self.expand_returned_sql_fields(self.translate_app_fields(returned_fields))

    def constraints_to_str(self, constraints):
        constraints_tuples = self.translate_constraints(constraints)

        # returns a string and list of params
        result = []
        params = []

        for field_name, operator, value in constraints_tuples:
            if operator == "lte":
                result.append('"{}" <= %s'.format(field_name))
                params.append(value)
            elif operator == "gte":
                result.append('"{}" >= %s'.format(field_name))
                params.append(value)
            elif operator == "eq":
                if (isinstance(value, collections.Sequence) or isinstance(value, QuerySet)) and type(value) not in (str, unicode):
                    if value:
                        result.append('{} IN ({})'.format(field_name, ','.join(["%s"] * len(value))))
                        params.extend(value)
                    else:
                        result.append('FALSE')
                else:
                    result.append('{}=%s'.format(field_name))
                    params.append(value)
            else:
                raise Exception("Unknown constraint type: {}".format(field_name))

        return " AND ".join(result), params

    def prepare_select_query(self, returned_fields, breakdown_fields, order_fields, offset, limit, constraints):
        # Takes app-based fields and first checks & translates them and then creates a query
        # first translate constraints into tuples, then create a single constraints str
        (constraint_str, constraint_params) = self.constraints_to_str(constraints)
        breakdown_fields = self.translate_breakdown_fields(breakdown_fields)
        order_fields = self.translate_order_fields(order_fields)
        returned_fields = self.get_returned_fields(returned_fields)

        statement = self.form_select_query(
            self.TABLE_NAME,
            breakdown_fields + returned_fields,
            constraint_str,
            breakdown_fields=breakdown_fields,
            order_fields=order_fields,
            limit=limit,
            offset=offset,
        )

        return (statement, constraint_params)

    @staticmethod
    def form_select_query(table, fields, constraint_str, breakdown_fields=None, order_fields=None, limit=None, offset=None):
        cmd = 'SELECT {fields} FROM {table} WHERE {constraint_str}'.format(
            fields=','.join(fields),
            table=table,
            constraint_str=constraint_str,
        )

        if breakdown_fields:
            cmd += ' GROUP BY {}'.format(','.join(breakdown_fields))

        if order_fields:
            cmd += " ORDER BY " + ",".join(order_fields) + " "

        if limit:
            cmd += " LIMIT " + str(limit)
        if offset:
            cmd += " OFFSET " + str(offset)
        return cmd

    def map_results_to_app(self, rows):
        # this passthrough makes testing much easier as we keep the original mock
        if len(rows) == 0:
            return rows
        return [self.map_result_to_app(row) for row in rows]

    def map_result_to_app(self, row):
        result = {}
        for field_name, val in row.items():
            field_desc = self.by_sql_mapping[field_name]
            newname = field_desc['app']
            output_function = field_desc['out']
            newval = output_function(val)
            result[newname] = newval

        return result

    # Execute functions actually execute the queries
    # Each one needs cursor passed into it
    # Default cursor can be obtained by get_cursor()

    def execute_select_query(self, cursor, returned_fields, breakdown_fields, order_fields, offset, limit, constraints):
        (statement, params) = self.prepare_select_query(returned_fields, breakdown_fields, order_fields, offset, limit, constraints)

        cursor.execute(statement, params)
        results = cursor.dictfetchall()
        results = self.map_results_to_app(results)
        return results

    MAX_AT_A_TIME = 100

    # This function specifically takes sql-named fields
    def execute_multi_insert_sql(self, cursor, fields_sql, all_row_tuples, max_at_a_time=None):
        if not max_at_a_time:
            max_at_a_time = self.MAX_AT_A_TIME
        fields_str = "(" + ",".join(fields_sql) + ")"
        fields_placeholder = "(" + ",".join(["%s"] * len(fields_sql)) + ")"
        for row_tuples in grouper(max_at_a_time, all_row_tuples):
            statement = "INSERT INTO {table} {fields} VALUES {fields_strs}".format(table=self.TABLE_NAME,
                                                                                   fields=fields_str,
                                                                                   fields_strs=",".join([fields_placeholder] * len(row_tuples))
                                                                                   )

            row_tuples_flat = [item for sublist in row_tuples for item in sublist]
            cursor.execute(statement, row_tuples_flat)

    def execute_delete(self, cursor, constraints=None):
        if not constraints:
            raise exc.ReportsQueryError("Delete query without specifying constraints")
        (constraint_str, constraint_params) = self.constraints_to_str(constraints)

        statement = 'DELETE FROM "{table}" WHERE {constraint_str}'.format(table=self.TABLE_NAME,
                                                                          constraint_str=constraint_str)
        cursor.execute(statement, constraint_params)

    def get_cursor(self):
        return MyCursor(connections[settings.STATS_DB_NAME].cursor())
