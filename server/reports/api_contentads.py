import logging

from reports import aggregate_fields
from reports import api_helpers
from reports import redshift
from reports import exc


CONTENTADSTATS_FIELD_MAPPING = {
    'date': 'date',
    'duration': 'total_time_on_site',
    'content_ad': 'content_ad_id',
    'source': 'source_id',
    'campaign': 'campaign_id',
    'account': 'account_id',
    'ad_group': 'adgroup_id'
}
CONTENTADSTATS_FIELD_REVERSE_MAPPING = {v: k for k, v in CONTENTADSTATS_FIELD_MAPPING.iteritems()}


logger = logging.getLogger(__name__)


def query(start_date, end_date, breakdown=None, **constraints):

    if breakdown and len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    results = redshift.query_contentadstats(
        start_date,
        end_date,
        aggregate_fields.ALL_AGGREGATE_FIELDS,
        CONTENTADSTATS_FIELD_MAPPING,
        breakdown,
        **constraints)

    if breakdown:
        return [_transform_row(row) for row in results]

    return _transform_row(results)


def _transform_row(row):
    result = {}
    for name, val in row.items():
        name = CONTENTADSTATS_FIELD_REVERSE_MAPPING.get(name, name)

        val = aggregate_fields.transform_val(name, val)
        name = aggregate_fields.transform_name(name)

        result[name] = val

    return result
