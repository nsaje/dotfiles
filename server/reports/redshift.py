import itertools

from django.conf import settings
from django.db import connections

import influx

from utils.statsd_helper import statsd_timer

from reports import exc
from reports.db_raw_helpers import MyCursor, is_collection

JSON_KEY_DELIMITER = '--'
S3_FILE_URI = 's3://{bucket_name}/{key}'

# historically we have migrated data to Redshift partially
# but there are differences and missing data for older
# postclick statistics - this id stores the difference generated
# with a script on fea_redshift_migration /
REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1


def _get_aws_credentials_string(aws_access_key_id, aws_secret_access_key):
    return 'aws_access_key_id=%s;aws_secret_access_key=%s' % (aws_access_key_id, aws_secret_access_key)


@statsd_timer('reports.redshift', 'delete_contentadstats')
def delete_contentadstats(date, campaign_id):
    query = 'DELETE FROM contentadstats WHERE date = %s AND campaign_id = %s AND content_ad_id != %s'
    params = [date.isoformat(), campaign_id, REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID]
    _execute(query, params)


def _execute(query, params):
    with get_cursor() as cursor:
        cursor.execute(query, params)


def get_cursor(read_only=False):
    if not read_only:
        raise Exception("This cursor is deprecated and can only be used with read only.")
    return MyCursor(connections[settings.STATS_DB_NAME].cursor())


@statsd_timer('reports.redshift', 'delete_contentadstatsdiff')
def delete_contentadstats_diff(date, campaign_id):
    query = 'DELETE FROM contentadstats WHERE date = %s AND campaign_id = %s AND content_ad_id = %s'
    params = [date.isoformat(), campaign_id, REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID]
    _execute(query, params)


@statsd_timer('reports.redshift', 'delete_touchpointconversions')
def delete_touchpoint_conversions(date, account_id, slug):
    query = 'DELETE FROM touchpointconversions WHERE date = %s AND account_id = %s AND slug = %s'
    params = [date.isoformat(), account_id, slug]
    _execute(query, params)


@statsd_timer('reports.redshift', 'insert_contentadstats')
def insert_contentadstats(rows):
    if not rows:
        return

    cursor = get_cursor()

    cols = rows[0].keys()

    query = 'INSERT INTO contentadstats ({cols}) VALUES {rows}'.format(
            cols=','.join(cols),
            rows=_get_rows_string(cols, rows))

    cursor.execute(query, _get_rows_params(cols, rows))
    cursor.close()


@statsd_timer('reports.redshift', 'load_contentadstats')
def load_contentadstats(s3_key):
    query = "COPY contentadstats FROM %s CREDENTIALS %s FORMAT JSON 'auto' MAXERROR 0"

    credentials = _get_aws_credentials_string(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    params = [S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_key), credentials]

    _execute(query, params)


@statsd_timer('reports.redshift', 'insert_touchpointconversions')
def insert_touchpoint_conversions(rows):
    if not rows:
        return

    cursor = get_cursor()

    cols = rows[0].keys()

    query = 'INSERT INTO touchpointconversions ({cols}) VALUES {rows}'.format(
            cols=','.join(cols),
            rows=_get_rows_string(cols, rows))

    cursor.execute(query, _get_rows_params(cols, rows))
    cursor.close()


@statsd_timer('reports.redshift', 'sum_contentadstats')
def sum_contentadstats():
    query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats WHERE content_ad_id != %s'
    params = [REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID]

    cursor = get_cursor()
    cursor.execute(query, params)

    result = cursor.dictfetchall()

    cursor.close()
    return result[0]


@statsd_timer('reports.redshift', 'sum_of_stats')
def sum_of_stats(with_diffs=False):
    query = '''SELECT SUM(impressions) as impressions, SUM(visits) as visits,
    SUM(clicks) as clicks,
    SUM(cost_cc) as cost_cc,
    SUM(data_cost_cc) as data_cost_cc,
    SUM(new_visits) as new_visits,
    SUM(bounced_visits) as bounced_visits,
    SUM(pageviews) as pageviews,
    SUM(total_time_on_site) as total_time_on_site,
    SUM(effective_cost_nano) as effective_cost_nano,
    SUM(effective_data_cost_nano) as effective_data_cost_nano,
    SUM(license_fee_nano) as license_fee_nano
    FROM contentadstats'''

    params = []
    if not with_diffs:
        query += ' WHERE content_ad_id != %s AND account_id != 50'
        params.append(REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID)
    else:
        query += ' WHERE account_id != 50'

    cursor = get_cursor(read_only=True)
    cursor.execute(query, params)

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

    cursor = get_cursor(read_only=True)
    cursor.execute(query, params)

    result = cursor.fetchall()
    cursor.close()

    return {(row[0], row[1]): row[2] for row in result}


@statsd_timer('reports.redshift', 'vacuum_contentadstats')
@influx.timer('reports.redshift', operation='vacuum_contentadstats')
def vacuum_contentadstats():
    query = 'VACUUM FULL contentadstats'
    _execute(query, [])


@statsd_timer('reports.redshift', 'vacuum_touchpoint_conversions')
def vacuum_touchpoint_conversions():
    query = 'VACUUM FULL touchpointconversions'
    _execute(query, [])


@statsd_timer('reports.redshift', 'vacuum_publishers')
def vacuum_publishers():
    query = 'VACUUM FULL publishers_1'
    _execute(query, [])


@statsd_timer('reports.redshift', 'analyze_publishers')
def analyze_publishers():
    query = 'ANALYZE publishers_1'
    _execute(query, [])


@statsd_timer('reports.redshift', 'delete_publishers')
def delete_publishers(date):
    query = 'DELETE FROM publishers_1 WHERE date = %s'
    params = [date.isoformat()]
    _execute(query, params)


@statsd_timer('reports.redshift', 'load_publishers')
def load_publishers(s3_key):
    query = "COPY publishers_1 FROM %s CREDENTIALS %s FORMAT JSON 'auto' MAXERROR 0"

    credentials = _get_aws_credentials_string(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    params = [S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_key), credentials]
    _execute(query, params)


def _get_rows_string(cols, rows):
    template_string = '(' + ','.join(itertools.repeat('%s', len(cols))) + ')'
    return (template_string + ',') * (len(rows) - 1) + template_string


def _get_rows_params(cols, rows):
    params = []
    for row in rows:
        params.extend([row.get(k) for k in cols])
    return params


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
        statement = "INSERT INTO {table} {fields} VALUES {fields_strs}". \
            format(table=table,
                   fields=fields_str,
                   fields_strs=",".join([fields_placeholder] * len(row_tuples)))

        row_tuples_flat = [item for sublist in row_tuples for item in sublist]
        cursor.execute(statement, row_tuples_flat)


class RSQ(object):
    '''
    Used for constructing the WHERE filter of the query that supports AND, OR and NOT,
    similar to django Q (https://github.com/django/django/blob/master/django/db/models/query_utils.py)
    '''

    AND = ' AND '
    OR = ' OR '

    def __init__(self, *args, **kwargs):
        self.negate = False
        self.join_operator = self.AND
        self.children = list(args) + list(kwargs.iteritems())

    def _combine(self, other, join_operator):
        parent = type(self)(*[self, other])
        parent.join_operator = join_operator
        return parent

    def __and__(self, other):
        return self._combine(other, self.AND)

    def __or__(self, other):
        return self._combine(other, self.OR)

    def __invert__(self):
        self.negate = not self.negate
        return self

    def expand(self, rs_model):
        # BUG: This code will overflow the stack in case there are too many WHERE conditions
        parts = []
        params = []

        for child in self.children:
            if isinstance(child, type(self)):
                child_parts, child_params = child.expand(rs_model)
            else:
                child_parts, child_params = self._generate_sql(child, rs_model)

            parts.append(child_parts)
            params.extend(child_params)

        if not parts and not params:
            return '', []

        ret = '(' + self.join_operator.join(parts) + ')'
        if self.negate:
            ret = 'NOT ' + ret

        return ret, params

    def _prepare_constraint(self, constraint, rs_model):
        constraint_name, value = constraint

        parts = constraint_name.split("__")
        field_name_app = parts[0]
        if is_json_field(field_name_app):
            raise exc.ReportsQueryError("Json fields not supported in constraints: {}".format(field_name_app))
        if field_name_app not in rs_model.constraints_fields_app:
            raise exc.ReportsQueryError("Unsupported field constraint fields: {}".format(field_name_app))
        field_name_sql = rs_model.by_app_mapping[field_name_app]['sql']

        if len(parts) == 2:
            operator = parts[1]
        else:
            operator = "eq"

        return field_name_sql, operator, value

    def _generate_sql(self, constraint, rs_model):
        field_name, operator, value = self._prepare_constraint(constraint, rs_model)
        if operator == "lte":
            return '"{}"<=%s'.format(field_name), [value]
        elif operator == "lt":
            return '"{}"<%s'.format(field_name), [value]
        elif operator == "gte":
            return '"{}">=%s'.format(field_name), [value]
        elif operator == "gt":
            return '"{}">%s'.format(field_name), [value]
        elif operator == "eq":
            if is_collection(value):
                if value:
                    return '{} IN ({})'.format(field_name, ','.join(["%s"] * len(value))), value
                else:
                    return 'FALSE', []
            else:
                return '{}=%s'.format(field_name), [value]
        elif operator == "neq":
            if is_collection(value):
                if value:
                    return '{} NOT IN ({})'.format(field_name, ','.join(["%s"] * len(value))), value
                else:
                    return 'TRUE', []
            else:
                return '{}!=%s'.format(field_name), [value]
        else:
            raise Exception("Unknown constraint type: {}".format(operator))


def is_json_field(field_name):
    return JSON_KEY_DELIMITER in field_name


def extract_json_key_parts(field_name):
    return field_name.split(JSON_KEY_DELIMITER, 1)


def replace_json_key(field_name, json_key, rep):
    return field_name.replace(JSON_KEY_DELIMITER + json_key, JSON_KEY_DELIMITER + str(rep))


def append_json_key(field_name, json_key):
    return field_name + JSON_KEY_DELIMITER + json_key


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

    def _translate_app_field_to_sql(self, field_name):
        if field_name == '*':
            return '*'

        if not is_json_field(field_name):
            return self.by_app_mapping[field_name]['sql']

        # for json fields the key part needs to be ignored in order to get the correct matching sql field
        field_part, json_key = extract_json_key_parts(field_name)
        return append_json_key(self.by_app_mapping[field_part]['sql'], json_key)

    def translate_app_fields(self, field_names):
        return [self._translate_app_field_to_sql(field_name) for field_name in field_names]

    def _get_expanded_field_sql(self, field_name, desc):
        if "calc" in desc:
            return desc["calc"] + " AS \"" + field_name + "\""

        if is_json_field(field_name):
            raise exc.ReportsQueryError('json field has to have calc defined')

        return '"' + field_name + '"'

    def expand_returned_sql_fields(self, field_names):
        # returns the expanded fields, params used in them and json field mapping
        fields = []
        params = []
        json_fields = []

        for field_name in field_names:
            if field_name == '*':
                fields.append('*')
                continue

            if not is_json_field(field_name):
                desc = self.by_sql_mapping[field_name]
                fields.append(self._get_expanded_field_sql(field_name, desc))
                continue

            field_part, json_key = extract_json_key_parts(field_name)
            desc = self.by_sql_mapping[field_part]

            # store the json field name in the mapping and generate sql column name of format
            # {field_name}{JSON_KEY_DELIMITER}{index_to_mapping}
            field_name = replace_json_key(field_name, json_key, len(json_fields))
            json_fields.append(json_key)

            field_expanded = self._get_expanded_field_sql(field_name, desc)
            fields.append(field_expanded)
            params.extend([json_key] * (desc['num_json_params']))

        return fields, params, json_fields

    def translate_breakdown_fields(self, breakdown_fields):
        unknown_fields = set(breakdown_fields) - self.ALLOWED_BREAKDOWN_FIELDS_APP
        if any(is_json_field(field_name) for field_name in breakdown_fields):
            raise exc.ReportsQueryError('Json fields are not supported in breakdown: {}'.format(str(breakdown_fields)))
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

    def get_returned_fields(self, returned_fields):
        return self.expand_returned_sql_fields(self.translate_app_fields(returned_fields))

    def _prepare_select_query(self, returned_fields, breakdown_fields, order_fields, offset, limit,
                              constraints, constraints_list, having_constraints, subquery):
        # Takes app-based fields and first checks & translates them and then creates a query
        # first translate constraints into tuples, then create a single constraints str
        (constraint_str, constraint_params) = RSQ(*constraints_list, **constraints).expand(self)
        breakdown_fields = self.translate_breakdown_fields(breakdown_fields)
        order_fields = self.translate_order_fields(order_fields)
        returned_fields, returned_params, json_fields = self.get_returned_fields(returned_fields)

        from_table = self.TABLE_NAME
        from_params = []
        if subquery:
            from_table, from_params, from_json_fields = self._prepare_select_query(
                returned_fields=subquery['returned_fields'],
                breakdown_fields=subquery.get('breakdown_fields', []),
                order_fields=subquery.get('order_fields', []),
                offset=subquery.get('offset'),
                limit=subquery.get('limit'),
                constraints=subquery.get('constraints', {}),
                constraints_list=subquery.get('constraints_list', []),
                having_constraints=subquery.get('having_constraints'),
                subquery=subquery.get('subquery')
            )
            from_table = '(' + from_table + ')'
            json_fields.extend(from_json_fields)

        params = returned_params + from_params + constraint_params
        statement = self._form_select_query(
            from_table,
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
        cmd = 'SELECT {fields} FROM {table}'.format(
            fields=','.join(fields),
            table=table,
        )

        if constraint_str:
            cmd += ' WHERE {constraint_str}'.format(constraint_str=constraint_str)

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
            if not is_json_field(field_name):
                field_desc = self.by_sql_mapping[field_name]
                newname = field_desc['app']
                output_function = field_desc['out']
                newval = output_function(val)
                result[newname] = newval
                continue

            # get the matching json field back from the mapping by index that is in the sql column name
            field_part, json_key = extract_json_key_parts(field_name)
            field_desc = self.by_sql_mapping[field_part]

            newname = append_json_key(field_desc['app'], json_fields[int(json_key)])
            output_function = field_desc['out']
            newval = output_function(val)
            result[newname] = newval

        return result

    # Execute functions actually execute the queries
    # Each one needs cursor passed into it
    # Default cursor can be obtained by get_cursor()

    def execute_select_query(self, cursor, returned_fields, breakdown_fields, order_fields, offset, limit, constraints,
                             constraints_list=None, having_constraints=None, subquery=None):

        (statement, params, json_fields) = self._prepare_select_query(
            returned_fields=returned_fields,
            breakdown_fields=breakdown_fields,
            order_fields=order_fields,
            offset=offset,
            limit=limit,
            constraints=constraints,
            constraints_list=constraints_list if constraints_list else [],
            having_constraints=having_constraints,
            subquery=subquery)

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
        (constraint_str, constraint_params) = RSQ(**constraints).expand(self)

        statement = 'DELETE FROM "{table}" WHERE {constraint_str}'.format(table=self.TABLE_NAME,
                                                                          constraint_str=constraint_str)
        cursor.execute(statement, constraint_params)
