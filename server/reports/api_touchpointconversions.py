import copy
import collections

from reports import db_raw_helpers
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
        dict(sql='publisher',     app="publisher",  out=rs_helpers.unchanged),
    ]

    _CONVERSION_FIELDS = [
        dict(sql='conversion_count', app='conversion_count', out=rs_helpers.unchanged, calc=rs_helpers.count_ranked('conversion_id_ranked', 1)),
        dict(sql='touchpoint_count', app='touchpoint_count', out=rs_helpers.unchanged, calc=rs_helpers.count_agr('touchpoint_id')),
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


def query(start_date, end_date, order=[], breakdown=[], conversion_goals=[], constraints={}, constraints_list=[]):

    breakdown = copy.copy(breakdown)
    conversion_goals = copy.copy(conversion_goals)
    order = copy.copy(order)
    constraints = copy.copy(constraints)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date

    constraints = db_raw_helpers.extract_obj_ids(constraints)

    cursor = redshift.get_cursor()

    if conversion_goals:
        results = []
        for conversion_goals_batch in _split_conversion_goals_by_window(conversion_goals):
            batch_results = _query(cursor, conversion_goals_batch, constraints, constraints_list, breakdown, order)
            results.extend(batch_results)
        cursor.close()
    else:
        results = _query(cursor, conversion_goals, constraints, constraints_list, breakdown, order)
        cursor.close()

    return results


def _query(cursor, conversion_goals, constraints, constraints_list, breakdown, order):
    constraints_list = copy.copy(constraints_list)
    if conversion_goals:
        # create a base object, then OR onto it
        rsq = redshift.RSQ(account=conversion_goals[0].pixel.account_id, slug=conversion_goals[0].pixel.slug,
                           conversion_lag__lte=conversion_goals[0].conversion_window)
        for conversion_goal in conversion_goals[1:]:
            rsq |= redshift.RSQ(account=conversion_goal.pixel.account_id, slug=conversion_goal.pixel.slug,
                                conversion_lag__lte=conversion_goal.conversion_window)
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

    _insert_conversion_window(results, conversion_goals)

    return results


def _split_conversion_goals_by_window(conversion_goals):
    # split conversions goals into batches
    # new batches are created when goals with same pixels are used
    # and use different window length

    goals_by_pixels = collections.defaultdict(list)
    nr_batches = 1  # the number of batches is the max nr of different conversion goals with the same pixels
    for cg in conversion_goals:
        k = (cg.pixel.slug, cg.pixel.account_id)
        goals_by_pixels[k].append(cg)
        if len(goals_by_pixels[k]) > nr_batches:
            nr_batches = len(goals_by_pixels[k])

    # join batches by goals list indices
    conversion_goals_batches = collections.defaultdict(list)
    for i in xrange(nr_batches):
        gs = []
        for px, goals in goals_by_pixels.items():
            if len(goals) >= i + 1:
                gs.append(goals[i])

        conversion_goals_batches[i].extend(gs)

    return conversion_goals_batches.values()


def _insert_conversion_window(result, conversion_goals):
    conversion_goals_by_slug = {(cg.pixel.slug, cg.pixel.account_id): cg for cg in
                                conversion_goals if cg.pixel}
    for row in result:
        cg = conversion_goals_by_slug.get((row['slug'], row['account'],))
        row['conversion_window'] = cg.conversion_window if cg else None
