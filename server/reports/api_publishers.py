import logging

from reports import aggregate_fields
from reports import api_helpers
from reports import redshift
from reports import exc


PUBLISHERS_FIELD_MAPPING = {
    'domain': 'domain',
    'exchange': 'exchange',
    'date': 'date',
    'ad_group': 'adgroup_id',
    'cost': 'cost_cc_sum',
        
}

PUBLISHERS_FIELD_REVERSE_MAPPING = {v: k for k, v in PUBLISHERS_FIELD_MAPPING.iteritems()}


logger = logging.getLogger(__name__)


def query(start_date, end_date, breakdown=None, order_fields_unmapped=None, order_direction=None, offset=None, limit=None, constraints_dict={}):

    if breakdown and len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    results = redshift.query_publishers(
        start_date,
        end_date,
        aggregate_fields.PUBLISHERS_AGGREGATE_FIELDS,
        PUBLISHERS_FIELD_MAPPING,
        breakdown,
        order_fields_unmapped = order_fields_unmapped,
        order_direction = order_direction,
        limit = limit,
        offset = offset,
        constraints_dict = constraints_dict)

    if breakdown:
        return [_transform_row(row) for row in results]

    return _transform_row(results)


def _transform_row(row):
    result = {}
    for name, val in row.items():
        name = PUBLISHERS_FIELD_REVERSE_MAPPING.get(name, name)

        val = aggregate_fields.transform_val(name, val)
        name = aggregate_fields.transform_name(name)

        result[name] = val

    return result
