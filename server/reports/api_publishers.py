import logging

from reports import aggregate_fields
from reports import api_helpers
from reports import redshift
from reports import exc


PUBLISHERS_FIELD_MAPPING = {
    'domain': 'domain',
    'exchange': 'exchange',
    'date': 'date',
    'ad_group': 'adgroup_id'
}
PUBLISHERS_FIELD_REVERSE_MAPPING = {v: k for k, v in PUBLISHERS_FIELD_MAPPING.iteritems()}


logger = logging.getLogger(__name__)


def query(start_date, end_date, breakdown=None, order=None, **constraints):

    if breakdown and len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    results = redshift.query_publishers(
        start_date,
        end_date,
        aggregate_fields.PUBLISHERS_AGGREGATE_FIELDS,
        PUBLISHERS_FIELD_MAPPING,
        breakdown,
        order,
        **constraints)

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
