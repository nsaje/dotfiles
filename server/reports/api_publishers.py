import logging
import copy
from reports import redshift
from reports import exc

from reports.rs_helpers import from_micro_cpm, to_percent, sum_div

logger = logging.getLogger(__name__)

class RSPublishersModel(redshift.RSModel):
    TABLE_NAME = 'b1_publishers_1'
    
    # fields that are always returned (app-based naming)
    DEFAULT_RETURNED_FIELDS_APP = ["clicks", "impressions", "cost", "ctr", "cpc"]
    # fields that are allowed for breakdowns (app-based naming)
    ALLOWED_BREAKDOWN_FIELDS_APP = set(['exchange', 'domain', 'date', ])

    #	       SQL NAME               APP NAME           OUTPUT TRANSFORM                    AGGREGATE                            ORDER BY function
    FIELDS = [dict(sql='clicks_sum',      app='clicks',      out=lambda v: v,                    calc='SUM("clicks")'),
              dict(sql='impressions_sum', app='impressions', out=lambda v: v,                    calc='SUM("impressions")'),    	
              dict(sql='domain',          app='domain',      out=lambda v: v),
              dict(sql='exchange',        app='exchange',    out=lambda v: v),
              dict(sql='date',            app='date',        out=lambda v: v),
              dict(sql='cost_micro_sum',  app='cost',        out=lambda v: from_micro_cpm(v),    calc='SUM("cost_micro")'),
              dict(sql='cpc_micro',       app='cpc',         out=lambda v: from_micro_cpm(v),    calc=sum_div("cost_micro", "clicks"), order="SUM(clicks)=0, cpc_micro"), # makes sure nulls are last
              dict(sql='ctr',             app='ctr',         out=lambda v: to_percent(v),        calc=sum_div("clicks", "impressions")),
              dict(sql='adgroup_id',      app='ad_group',    out=lambda v: v),
              dict(sql='exchange',        app='exchange',    out=lambda v: v),
              dict(sql='ob_section_id',   app='ob_section_id',out=lambda v: v),
              ]


rspub = RSPublishersModel()


def query(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}):
    # This API tries to completely isolate the rest of the app from Redshift-tied part, so namings are decoupled:
    # First map all query fields to their SQL representations first
    # Then run the query (without any knowledge about the outside world of the app)
    # Lastly map SQL fields back to application-used fields
        
    breakdown_fields = rspub.translate_breakdown_fields(breakdown_fields)    
    order_fields_tuples = rspub.translate_order_fields(order_fields)
    
    # map constraints fields
    constraints = copy.copy(constraints)
    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date
    constraints = rspub.translate_constraints(constraints)
    
    returned_fields = rspub.get_returned_fields() 

    # now get the query and parameters
    (statement, params) = redshift.get_query_general(
        rspub.TABLE_NAME,
        returned_fields,
        breakdown_fields,
        order_fields_tuples=order_fields_tuples,
        limit=limit,
        offset=offset,
        constraints=constraints)

    
    results = redshift.general_get_results(statement, params)
    results = rspub.map_results_to_app(results)

    if breakdown_fields:
        return results
    else:
        return results[0]




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
    
    redshift.delete_general('ob_publishers_1', {'date__eq': date, 'adgroup_id__eq': ad_group, 'exchange__eq': exchange})
    redshift.multi_insert_general('ob_publishers_1', sql_fields, row_tuples)
    
    





        