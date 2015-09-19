import logging

from django.db.models import Sum

from utils import db_aggregates
from reports import redshift
from reports import exc


logger = logging.getLogger(__name__)

def from_micro_cpm(num):
    if num is None:
        return None
    else:
        # we divide first by a million (since we use fixed point) and then by additional thousand (cpm)
        return num * 1.0 / 1000000000

def to_percent(num):
    if num is None:
        return None
    else:
        return num * 100

def _sum_div(expr, divisor):
    return ('CASE WHEN SUM("{divisor}") <> 0 THEN SUM(CAST("{expr}" AS FLOAT)) / SUM("{divisor}") '
            'ELSE NULL END').format(
                expr=expr,
                divisor=divisor,)

RETURNED_APP_FIELDS = ["clicks", "impressions", "cost", "ctr", "cpc"]

#	       SQL NAME               APP NAME           OUTPUT TRANSFORM                    AGGREGATE                            ORDER BY function
FIELDS = [dict(sql='clicks_sum',      app='clicks',      out=lambda v: v,                    calc='SUM("clicks")'),
          dict(sql='impressions_sum', app='impressions', out=lambda v: v,                    calc='SUM("impressions")'),    	
          dict(sql='domain',          app='domain',      out=lambda v: v),
          dict(sql='exchange',        app='exchange',    out=lambda v: v),
          dict(sql='date',            app='date',        out=lambda v: v),
          dict(sql='cost_micro_sum',  app='cost',        out=lambda v: from_micro_cpm(v),    calc='SUM("cost_micro")'),
          dict(sql='cpc_micro',       app='cpc',         out=lambda v: from_micro_cpm(v),    calc=_sum_div("cost_micro", "clicks"), order="SUM(clicks)=0, cpc_micro"), # makes sure nulls are last
          dict(sql='ctr',             app='ctr',         out=lambda v: to_percent(v),        calc=_sum_div("clicks", "impressions")),
          dict(sql='adgroup_id',      app='ad_group',    out=lambda v: v),
          dict(sql='exchange',        app='exchange',    out=lambda v: v),
          dict(sql='ob_section_id',   app='ob_section_id',out=lambda v: v),
          ]
BY_SQL_MAPPING = {d['sql']:d for d in FIELDS}
BY_APP_MAPPING = {d['app']:d for d in FIELDS}

CONSTRAINTS_FIELDS_APP_SET = set(BY_APP_MAPPING.keys())
BREAKDOWN_FIELDS_APP_SET = set(['exchange', 'domain', 'date', ])

def _translate_app_fields(field_names):
    return [BY_APP_MAPPING[field_name]['sql'] for field_name in field_names]
    

def _expand_sql_fields(field_names):
    fields = []
    for field_name in field_names:
        desc = BY_SQL_MAPPING[field_name]
        
        if "calc" in desc:
            field_expanded = desc["calc"] + " AS \"" + field_name +"\""
        else:
            field_expanded = '"' + field_name + '"'
        fields.append(field_expanded)
    return fields

def query(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}):
    # This API tries to completely isolate the rest of the app from Redshift-tied part, so namings are decoupled:
    # First map all query fields to their SQL representations first
    # Then run the query (without any knowledge about the outside world of the app)
    # Lastly map SQL fields back to application-used fields
    
    # map breakdown fields
    unknown_fields = set(breakdown_fields) - BREAKDOWN_FIELDS_APP_SET
    if unknown_fields:
        raise exc.ReportsQueryError('Invalid breakdowns: {}'.format(str(unknown_fields)))
    breakdown_fields = _translate_app_fields(breakdown_fields)
    # map order fields, we decode directions here too
    # we also support specifying order functions to be used instead of field name 
    # due to Redshift's inability to use aliased name inside expressions in ORDER BY
    order_fields_tuples = []
    for field in order_fields:
        direction = "ASC"
        if field.startswith("-"):
            direction = "DESC"
            field = field[1:]

        try: 	
            field_desc = BY_APP_MAPPING[field]
        except KeyError:
            raise exc.ReportsQueryError('Invalid field to order by: {}'.format(field))

        try:
            order_statement = field_desc['order']
        except KeyError:
            order_statement = field_desc['sql']
            
        order_fields_tuples.append((order_statement, direction))
    
    # map constraints fields
    unknown_fields = set(constraints.keys()) - CONSTRAINTS_FIELDS_APP_SET
    if unknown_fields:
        raise exc.ReportsQueryError("Unsupported field constraint fields: {}".format(str(unknown_fields)))
    constraints = {BY_APP_MAPPING[field_name]['sql']: v for field_name, v in constraints.iteritems()}

    returned_fields = _expand_sql_fields(_translate_app_fields(RETURNED_APP_FIELDS))

    # now execute the query
    results = redshift.query_general(
        'b1_publishers_1',
        start_date,
        end_date,
        returned_fields,
        breakdown_fields,
        order_fields_tuples=order_fields_tuples,
        limit=limit,
        offset=offset,
        constraints=constraints)


    # map back to app-specific fields
    if breakdown_fields:
        return [_map_rowdict_to_output(row) for row in results]

    return _map_rowdict_to_output(results[0])


def _map_rowdict_to_output(row):
    result = {}
    for field_name, val in row.items():
        field_desc = BY_SQL_MAPPING[field_name]
        newname = field_desc['app']
        output_function = field_desc['out']
        newval = output_function(val)
        result[newname] = newval

    return result


def ob_insert_adgroup_date(date, ad_group, exchange, datarowdicts):
    # start a transaction
    sql_fields = ['date', 'adgroup_id', 'exchange', 'domain', 'name', 'clicks', 'ob_section_id']
    row_tuples = []
    for row in datarowdicts:
        # strip http:
        url = row['url']
        if url.startswith("https://"):
            url = url[8:]
        if url.startswith("http://"):
            url = url[7:]
        newrow = (date, ad_group, exchange, url, row['name'], row['clicks'], row['ob_section_id'])
        row_tuples.append(newrow)
    
    redshift.delete_general('ob_publishers_1', {'date': date, 'adgroup_id': ad_group, 'exchange': exchange})
    redshift.multi_insert_general('ob_publishers_1', sql_fields, row_tuples)
    
    





        