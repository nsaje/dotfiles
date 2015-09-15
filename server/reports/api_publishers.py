import logging

from django.db.models import Sum

from utils import db_aggregates
from reports import redshift
from reports import exc


logger = logging.getLogger(__name__)

def from_micro_cpm(num):
    if not num:	
        return None
    else:
        return num * 1.0 / 1000000000


PUBLISHERS_AGGREGATE_FIELDS = dict(
    clicks_sum=Sum('clicks'),
    impressions_sum=Sum('impressions'),
    cost_micro_sum=Sum('cost_micro'),
    ctr=db_aggregates.SumDivision('clicks', 'impressions'),
    cpc_micro=db_aggregates.SumDivision('cost_micro', 'clicks')
)

#			  SQL NAME           DICT NAME      OUTPUT TRANSFORM FUNCTION       
OUTPUT_FIELDS_MAPPING = {'clicks_sum':      ('clicks',      lambda v: v),
                         'impressions_sum': ('impressions', lambda v: v),
                         'domain':          ('domain',      lambda v: v),
                         'exchange':        ('exchange',    lambda v: v),
                         'date':            ('date',        lambda v: v),
                         'clicks_sum':      ('clicks',      lambda v: v),
                         'cost_micro_sum':  ('cost',        lambda v: from_micro_cpm(v)),
                         'cpc_micro':       ('cpc',         lambda v: from_micro_cpm(v)),
                         'ctr':             ('ctr',         lambda v: v * 100),
                         'ad_group_id':     ('adgroup_id',  lambda v: v),
                         'exchange':        ('exchange',    lambda v: v),
                        }
OUTPUT_FIELDS_REVERSE_MAPPING = {v[0]:k for k,v in OUTPUT_FIELDS_MAPPING.iteritems()}

CONSTRAINTS_FIELDS_UNMAPPED_SET = set(OUTPUT_FIELDS_REVERSE_MAPPING.keys())
BREAKDOWN_FIELDS_UNMAPPED_SET = set(['exchange', 'domain', 'date', ])

def query(start_date, end_date, breakdown_fields=[], order_fields=[], order_direction=None, offset=None, limit=None, constraints_dict={}):
    # map all query fields to their SQL representations first
    # then run query
    # then map SQL fields back to application fields
    
    # map breakdown fields
    unknown_fields = set(breakdown_fields) - BREAKDOWN_FIELDS_UNMAPPED_SET
    if len(unknown_fields) != 0:
        raise exc.ReportsQueryError('Invalid breakdowns: %s' % str(unknown_fields))
    breakdown_fields = [OUTPUT_FIELDS_REVERSE_MAPPING[field] for field in breakdown_fields]
    
    # map order fields
    unknown_fields = set(order_fields) - CONSTRAINTS_FIELDS_UNMAPPED_SET
    if len(unknown_fields) != 0:
        raise exc.ReportsQueryError('Invalid breakdowns: %s' % str(unknown_fields))
    order_fields = [OUTPUT_FIELDS_REVERSE_MAPPING[field] for field in order_fields]

    # map constraints fields	
    unknown_fields = set(constraints_dict.keys()) - CONSTRAINTS_FIELDS_UNMAPPED_SET
    if len(unknown_fields) > 0:
        raise exc.ReportsQueryError("Unsupported field constraint fields: %s" % str(unknown_fields))
    # TODO: map constrain fields too
        
    # now execute the query
    results = redshift.query_general(
        'b1_publishers_1',
        start_date,
        end_date,
        PUBLISHERS_AGGREGATE_FIELDS,
        breakdown_fields,
        order_fields = order_fields,
        order_direction = order_direction,
        limit = limit,
        offset = offset,
        constraints_dict = constraints_dict)



    if breakdown_fields:
        return [_map_rowdict_to_output(row) for row in results]
 
    return _map_rowdict_to_output(results[0])


def _map_rowdict_to_output(row):
    result = {}
    for name, val in row.items():
        (newname, mapfunc) = OUTPUT_FIELDS_MAPPING[name]
        newval = mapfunc(val)
        result[newname] = newval

    return result
