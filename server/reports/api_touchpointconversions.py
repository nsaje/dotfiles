import copy

from reports import db_raw_helpers
from reports import redshift
from reports import rs_helpers


class RSTouchpointConversionsModel(redshift.RSModel):
    TABLE_NAME = 'mv_touch_content_ad'

    _BREAKDOWN_FIELDS = [
        dict(sql='date',          app='date',       out=rs_helpers.unchanged),
        dict(sql='source_id',     app='source',     out=rs_helpers.unchanged),
        dict(sql='agency_id',     app='agency',     out=rs_helpers.unchanged),
        dict(sql='account_id',    app='account',    out=rs_helpers.unchanged),
        dict(sql='campaign_id',   app='campaign',   out=rs_helpers.unchanged),
        dict(sql='ad_group_id',   app='ad_group',   out=rs_helpers.unchanged),
        dict(sql='content_ad_id', app='content_ad', out=rs_helpers.unchanged),
        dict(sql='slug',          app='slug',       out=rs_helpers.unchanged),
    ]

    _CONVERSION_FIELDS = [
        dict(sql='conversion_count_24', app='conversion_count_24', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(24)),
        dict(sql='conversion_count_168', app='conversion_count_168', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(168)),
        dict(sql='conversion_count_720', app='conversion_count_720', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(720)),
        dict(sql='conversion_count_2160', app='conversion_count_2160', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(2160)),
    ]

    FIELDS = _BREAKDOWN_FIELDS + _CONVERSION_FIELDS
    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _CONVERSION_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _BREAKDOWN_FIELDS)


class RSTouchpointConversionsPublishersModel(redshift.RSModel):
    TABLE_NAME = 'mv_touchpointconversions'

    _BREAKDOWN_FIELDS = [
        dict(sql='date',          app='date',       out=rs_helpers.unchanged),
        dict(sql='source_id',     app='source',     out=rs_helpers.unchanged),
        dict(sql='agency_id',     app='agency',     out=rs_helpers.unchanged),
        dict(sql='account_id',    app='account',    out=rs_helpers.unchanged),
        dict(sql='campaign_id',   app='campaign',   out=rs_helpers.unchanged),
        dict(sql='ad_group_id',   app='ad_group',   out=rs_helpers.unchanged),
        dict(sql='content_ad_id', app='content_ad', out=rs_helpers.unchanged),
        dict(sql='publisher',     app='publisher',  out=rs_helpers.unchanged),
        dict(sql='slug',          app='slug',       out=rs_helpers.unchanged),
    ]

    _CONVERSION_FIELDS = [
        dict(sql='conversion_count_24', app='conversion_count_24', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(24)),
        dict(sql='conversion_count_168', app='conversion_count_168', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(168)),
        dict(sql='conversion_count_720', app='conversion_count_720', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(720)),
        dict(sql='conversion_count_2160', app='conversion_count_2160', out=rs_helpers.unchanged,
             calc=rs_helpers.sum_mv_touchpointconversions(2160)),
    ]

    FIELDS = _BREAKDOWN_FIELDS + _CONVERSION_FIELDS
    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _CONVERSION_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _BREAKDOWN_FIELDS)

RSTouchpointConversions = RSTouchpointConversionsModel()
RSTouchpointConversionsPublishers = RSTouchpointConversionsPublishersModel()


def query(*args, **kwargs):
    return _query(*args, **kwargs)


def query_publishers(*args, **kwargs):
    return _query(*args, model=RSTouchpointConversionsPublishers, **kwargs)


def _query(start_date, end_date, order=[], breakdown=[], pixels=[], constraints={}, constraints_list=[],
           model=RSTouchpointConversions):
    breakdown = copy.copy(breakdown)
    pixels = copy.copy(pixels)
    order = copy.copy(order)
    constraints = copy.copy(constraints)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date

    constraints = db_raw_helpers.extract_obj_ids(constraints)

    results = []
    if not pixels:
        return results

    cursor = redshift.get_cursor(read_only=True)
    constraints_list = copy.copy(constraints_list)

    # create a base object, then OR onto it
    rsq = redshift.RSQ(account=pixels[0].account_id, slug=pixels[0].slug)
    for pixel in pixels[1:]:
        rsq |= redshift.RSQ(account=pixel.account_id, slug=pixel.slug)
    constraints_list.append(rsq)

    results = model.execute_select_query(
        cursor,
        RSTouchpointConversions.DEFAULT_RETURNED_FIELDS_APP,
        breakdown_fields=breakdown + ['slug', 'account'],
        order_fields=order,
        offset=None,
        limit=None,
        constraints=constraints,
        constraints_list=constraints_list,
    )

    cursor.close()
    return results
