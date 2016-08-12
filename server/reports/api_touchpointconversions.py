import copy
from multiprocessing.pool import ThreadPool
from functools import partial

from reports import db_raw_helpers
from reports import redshift
from reports import rs_helpers

import dash.constants


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
        dict(sql='publisher',     app="publisher",  out=rs_helpers.unchanged),
    ]

    _CONVERSION_FIELDS = [
        dict(sql='conversion_count', app='conversion_count', out=rs_helpers.unchanged, calc=rs_helpers.count_ranked('conversion_id_ranked', 1)),
    ]

    _OTHER_FIELDS = [
        dict(sql='conversion_lag',       app='conversion_lag',       out=rs_helpers.unchanged),
        dict(sql='conversion_id_ranked', app='conversion_id_ranked', out=rs_helpers.unchanged, calc=rs_helpers.ranked('conversion_id',
                                                                                                                      '-touchpoint_timestamp')),
    ]

    FIELDS = _BREAKDOWN_FIELDS + _CONVERSION_FIELDS + _OTHER_FIELDS
    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _CONVERSION_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _BREAKDOWN_FIELDS)

RSTouchpointConversions = RSTouchpointConversionsModel()


def query(start_date, end_date, order=[], breakdown=[], pixels=[], constraints={}, constraints_list=[]):

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

    batches = _create_pixel_batches(pixels)
    pool = ThreadPool(processes=4)
    map_results = pool.map(
        partial(_async_query, breakdown, order, constraints, constraints_list),
        batches,
    )

    results = []
    for partial_results in map_results:
        results.extend(partial_results)
    return results


def _async_query(breakdown, order, constraints, constraints_list, batch):
    window, pixels = batch
    cursor = redshift.get_cursor(read_only=True)
    batch_results = _query(cursor, pixels, window, constraints, constraints_list, breakdown, order)
    cursor.close()
    return batch_results


def _query(cursor, pixels, window, constraints, constraints_list, breakdown, order):
    constraints_list = copy.copy(constraints_list)
    # create a base object, then OR onto it
    rsq = redshift.RSQ(account=pixels[0].account_id, slug=pixels[0].slug, conversion_lag__lte=window)
    for pixel in pixels[1:]:
        rsq |= redshift.RSQ(account=pixel.account_id, slug=pixel.slug, conversion_lag__lte=window)
    constraints_list.append(rsq)

    subquery = {
        'constraints_list': constraints_list,
        'returned_fields': ['*', 'conversion_id_ranked'],
    }

    results = RSTouchpointConversions.execute_select_query(
        cursor,
        RSTouchpointConversions.DEFAULT_RETURNED_FIELDS_APP,
        breakdown_fields=breakdown + ['slug', 'account'],
        order_fields=order,
        offset=None,
        limit=None,
        constraints=constraints,
        subquery=subquery,
        constraints_list=constraints_list,
    )

    _insert_conversion_window(results, window)

    return results


def _create_pixel_batches(pixels):
    return {
        window: list(pixels) for window in dash.constants.ConversionWindows.get_all()
    }.items()


def _insert_conversion_window(result, window):
    for row in result:
        row['conversion_window'] = window
