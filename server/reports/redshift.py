import itertools

from django.conf import settings
from django.db import connections

from utils.statsd_helper import statsd_timer

from reports import exc
from reports.db_raw_helpers import MyCursor, is_collection

JSON_KEY_DELIMITER = '--'

# historically we have migrated data to Redshift partially
# but there are differences and missing data for older
# postclick statistics - this id stores the difference generated
# with a script on fea_redshift_migration /
REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1


@statsd_timer('reports.redshift', 'delete_contentadstats')
def delete_contentadstats(date, ad_group_id, source_id):
    cursor = get_cursor()

    query = 'DELETE FROM contentadstats WHERE date = %s AND adgroup_id = %s AND id != %s'
    params = [date.isoformat(), ad_group_id, REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID]

    if source_id:
        query = query + ' AND source_id = %s'
        params.append(source_id)

    cursor.execute(query, params)
    cursor.close()


@statsd_timer('reports.redshift', 'delete_contentadstats')
def delete_touchpoint_conversions(date):
    cursor = get_cursor()

    query = 'DELETE FROM touchpointconversions WHERE date = %s'
    params = [date.isoformat()]

    cursor.execute(query, params)
    cursor.close()


@statsd_timer('reports.redshift', 'insert_contentadstats')
def insert_contentadstats(rows):
    if not rows:
        return

    cursor = get_cursor()

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

    cursor = get_cursor()

    cols = rows[0].keys()

    query = 'INSERT INTO touchpointconversions ({cols}) VALUES {rows}'.format(
        cols=','.join(cols),
        rows=','.join(_get_row_string(cursor, cols, row) for row in rows))

    cursor.execute(query, [])
    cursor.close()


@statsd_timer('reports.redshift', 'sum_contentadstats')
def sum_contentadstats():
    query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'

    cursor = get_cursor()
    cursor.execute(query, [])

    result = cursor.dictfetchall()

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

    cursor = get_cursor()
    cursor.execute(query, params)

    result = cursor.fetchall()
    cursor.close()

    return {(row[0], row[1]): row[2] for row in result}


@statsd_timer('reports.redshift', 'vacuum_contentadstats')
def vacuum_contentadstats():
    query = 'VACUUM FULL contentadstats'

    cursor = get_cursor()
    cursor.execute(query, [])
    cursor.close()


@statsd_timer('reports.redshift', 'vacuum_touchpoint_conversions')
def vacuum_touchpoint_conversions():
    query = 'VACUUM FULL touchpointconversions'

    cursor = get_cursor()
    cursor.execute(query, [])

    cursor.close()


def get_cursor():
    return MyCursor(connections[settings.STATS_DB_NAME].cursor())


def _get_row_string(cursor, cols, row):
    template_string = '(' + ','.join(itertools.repeat('%s', len(cols))) + ')'
    return cursor.mogrify(template_string, [row[col] for col in cols])


def grouper(n, iterable):
    """
    Iterate in chunks, python recepie
    """

    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def execute_multi_insert_sql(cursor, table, fields_sql, all_row_tuples, max_at_a_time=100):
    fields_str = "(" + ",".join(fields_sql) + ")"
    fields_placeholder = "(" + ",".join(["%s"] * len(fields_sql)) + ")"
    for row_tuples in grouper(max_at_a_time, all_row_tuples):
        statement = "INSERT INTO {table} {fields} VALUES {fields_strs}".\
                    format(table=table,
                           fields=fields_str,
                           fields_strs=",".join([fields_placeholder] * len(row_tuples)))

        row_tuples_flat = [item for sublist in row_tuples for item in sublist]
        cursor.execute(statement, row_tuples_flat)


class RSModel(object):
    FIELDS = []
    TABLE_NAME = "test_table"

    # fields that are always returned (app-based naming)
    DEFAULT_RETURNED_FIELDS_APP = []

    # fields that are allowed for breakdowns (app-based naming)
    ALLOWED_BREAKDOWN_FIELDS_APP = set()

    def __init__(self):
        # set-up lookup tables
        self.by_sql_mapping = {d['sql']: d for d in self.FIELDS}
        self.by_app_mapping = {d['app']: d for d in self.FIELDS}

        # by default all fields are allowed as constraints
        self.constraints_fields_app = set(self.by_app_mapping.keys())

    def _is_json_field(self, field_name):
        return JSON_KEY_DELIMITER in field_name

    def _extract_field_part(self, field_name):
        return field_name.split(JSON_KEY_DELIMITER, 1)[0]

    def _extract_json_key(self, field_name):
        return field_name.split(JSON_KEY_DELIMITER, 1)[1]

    def _replace_json_key(self, field_name, json_key, rep):
        return field_name.replace(JSON_KEY_DELIMITER + json_key, '__{}'.format(rep))

    def _append_json_key(self, field_name, json_key):
        return field_name + JSON_KEY_DELIMITER + json_key

    def translate_app_fields(self, field_names):
        sql_names = []
        for field_name in field_names:
            field_part = field_name
            if self._is_json_field(field_name):
                # for json fields the key part needs to be ignored in order to get the correct matching sql field
                field_part = self._extract_field_part(field_name)

            sql_name = self.by_app_mapping[field_part]['sql']
            if self._is_json_field(field_name):
                json_key = self._extract_json_key(field_name)
                sql_name = self._append_json_key(sql_name, json_key)

            sql_names.append(sql_name)
        return sql_names

    def expand_returned_sql_fields(self, field_names):

        # returns the expanded fields, params used in them and json field mapping
        fields = []
        params = []
        json_fields = []

        for field_name in field_names:
            field_part = field_name
            if self._is_json_field(field_name):
                field_part = self._extract_field_part(field_name)

            desc = self.by_sql_mapping[field_part]
            if self._is_json_field(field_name):
                # store the json field name in the mapping and replace it with the index to that mapping
                json_key = self._extract_json_key(field_name)
                field_name = self._replace_json_key(field_name, json_key, len(json_fields))
                json_fields.append(json_key)
                params.extend([json_key] * (desc['json_params']))

            if "calc" in desc:
                field_expanded = desc["calc"] + " AS \"" + field_name + "\""
            else:
                if self._is_json_field(field_name):
                    raise Exception('json field has to have calc defined')

                field_expanded = '"' + field_name + '"'

            fields.append(field_expanded)

        return fields, params, json_fields

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
                if is_collection(value):
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

    def _prepare_select_query(self, returned_fields, breakdown_fields, order_fields, offset, limit,
                              constraints, having_constraints):
        # Takes app-based fields and first checks & translates them and then creates a query
        # first translate constraints into tuples, then create a single constraints str
        (constraint_str, constraint_params) = self.constraints_to_str(constraints)
        breakdown_fields = self.translate_breakdown_fields(breakdown_fields)
        order_fields = self.translate_order_fields(order_fields)
        returned_fields, returned_params, json_fields = self.get_returned_fields(returned_fields)

        params = returned_params + constraint_params
        statement = self._form_select_query(
            self.TABLE_NAME,
            breakdown_fields + returned_fields,
            constraint_str,
            breakdown_fields=breakdown_fields,
            order_fields=order_fields,
            limit=limit,
            offset=offset,
            having_constraints=having_constraints
        )

        return (statement, params, json_fields)

    @staticmethod
    def _form_select_query(table, fields, constraint_str, breakdown_fields=None, order_fields=None, limit=None,
                           offset=None, having_constraints=None):
        cmd = 'SELECT {fields} FROM {table} WHERE {constraint_str}'.format(
            fields=','.join(fields),
            table=table,
            constraint_str=constraint_str,
        )

        if breakdown_fields:
            cmd += ' GROUP BY {}'.format(','.join(breakdown_fields))

        if having_constraints:
            cmd += ' HAVING {}'.format(' AND '.join(having_constraints))

        if order_fields:
            cmd += " ORDER BY " + ",".join(order_fields) + " "

        if limit:
            cmd += " LIMIT " + str(limit)
        if offset:
            cmd += " OFFSET " + str(offset)
        return cmd

    def map_results_to_app(self, rows, json_fields):
        # this passthrough makes testing much easier as we keep the original mock
        if len(rows) == 0:
            return rows
        return [self.map_result_to_app(row, json_fields) for row in rows]

    def map_result_to_app(self, row, json_fields):
        result = {}
        for field_name, val in row.items():
            field_part = field_name
            if self._is_json_field(field_name):
                field_part = self._extract_field_part(field_name)

            field_desc = self.by_sql_mapping[field_part]
            newname = field_desc['app']
            if self._is_json_field(field_name):
                # get the matching json field back from the mapping by index that is in the sql column name
                json_key = self._extract_json_key(field_name)
                newname = self._append_json_key(newname, json_fields[int(json_key)])

            output_function = field_desc['out']
            newval = output_function(val)
            result[newname] = newval

        return result

    # Execute functions actually execute the queries
    # Each one needs cursor passed into it
    # Default cursor can be obtained by get_cursor()

    def execute_select_query(self, cursor, returned_fields, breakdown_fields, order_fields, offset, limit, constraints,
                             having_constraints=None):

        (statement, params, json_fields) = self._prepare_select_query(
            returned_fields,
            breakdown_fields,
            order_fields,
            offset,
            limit,
            constraints,
            having_constraints)

        cursor.execute(statement, params)
        results = cursor.dictfetchall()
        results = self.map_results_to_app(results, json_fields)
        return results

    def execute_multi_insert_sql(self, cursor, fields_sql, all_row_tuples, max_at_a_time=100):
        # This function specifically takes sql-named fields
        execute_multi_insert_sql(cursor, self.TABLE_NAME, fields_sql, all_row_tuples, max_at_a_time)

    def execute_delete(self, cursor, constraints=None):
        if not constraints:
            raise exc.ReportsQueryError("Delete query without specifying constraints")
        (constraint_str, constraint_params) = self.constraints_to_str(constraints)

        statement = 'DELETE FROM "{table}" WHERE {constraint_str}'.format(table=self.TABLE_NAME,
                                                                          constraint_str=constraint_str)
        cursor.execute(statement, constraint_params)
