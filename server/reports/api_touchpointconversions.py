import logging
import datetime

from reports import redshift
from reports import rs_helpers


class RSTouchpointConversionsModel(redshift.RSModel):
    TABLE_NAME = 'touchpointconversions'

    _BREAKDOWN_FIELDS = [
        dict(sql='date',          app='date',       out=rs_helpers.unchanged),
        dict(sql='account_id',    app='account',    out=rs_helpers.unchanged),
        dict(sql='campaign_id',   app='campaign',   out=rs_helpers.unchanged),
        dict(sql='ad_group_id',   app='ad_group',   out=rs_helpers.unchanged),
        dict(sql='content_ad_id', app='content_ad', out=rs_helpers.unchanged),
        dict(sql='source_id',     app='source',     out=rs_helpers.unchanged),
        dict(sql='slug',          app='slug',       out=rs_helpers.unchanged),
    ]

    _OTHER_FIELDS = [
        dict(sql='conversion_id', app='conversion_count', out=rs_helpers.unchanged, calc=rs_helpers.count_distinct_agr('conversion_id')),
        dict(sql='touchpoint_id', app='touchpoint_count', out=rs_helpers.unchanged, calc=rs_helpers.count_agr('touchpoint_id'))
    ]

    FIELDS = _BREAKDOWN_FIELDS + _OTHER_FIELDS
    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _OTHER_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _BREAKDOWN_FIELDS)

RSTouchpointConversions = RSTouchpointConversionsModel()


def query(start_date, end_date, breakdown=None, constraints=None):
    if not breakdown:
        breakdown = []

    if not constraints:
        constraints = []

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date

    cursor = redshift.get_cursor()

    results = RSTouchpointConversions.execute_select_query(
        cursor,
        RSTouchpointConversions.DEFAULT_RETURNED_FIELDS_APP,
        breakdown_fields=breakdown,
        order_fields=[],
        offset=None,
        limit=None,
        constraints=constraints
    )

    cursor.close()

    if breakdown:
        return results

    return results[0]
