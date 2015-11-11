import copy

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
    ]

    _CONVERSION_FIELDS = [
        dict(sql='conversion_id', app='conversion_count', out=rs_helpers.unchanged, calc=rs_helpers.count_distinct_agr('conversion_id')),
        dict(sql='touchpoint_id', app='touchpoint_count', out=rs_helpers.unchanged, calc=rs_helpers.count_agr('touchpoint_id'))
    ]

    _OTHER_FIELDS = [
        dict(sql='conversion_lag', app='conversion_lag', out=rs_helpers.unchanged)
    ]

    FIELDS = _BREAKDOWN_FIELDS + _CONVERSION_FIELDS + _OTHER_FIELDS
    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _CONVERSION_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _BREAKDOWN_FIELDS)

RSTouchpointConversions = RSTouchpointConversionsModel()


def query(start_date, end_date, order=[], breakdown=[], conversion_goals=[], constraints={}):

    breakdown = copy.copy(breakdown)
    conversion_goals = copy.copy(conversion_goals)
    order = copy.copy(order)
    conversion_goals = copy.copy(conversion_goals)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date

    constraints = db_raw_helpers.extract_obj_ids(constraints)

    constraints_list = []
    if conversion_goals:
        # create a base object, then OR onto it
        rsq = redshift.RSQ(account=conversion_goals[0].pixel.account_id, slug=conversion_goals[0].pixel.slug,
                           conversion_lag__lte=conversion_goals[0].conversion_window)
        for conversion_goal in conversion_goals[1:]:
            rsq |= redshift.RSQ(account=conversion_goal.pixel.account_id, slug=conversion_goal.pixel.slug,
                                conversion_lag__lte=conversion_goal.conversion_window)
        constraints_list = [rsq]

    cursor = redshift.get_cursor()

    results = RSTouchpointConversions.execute_select_query(
        cursor,
        RSTouchpointConversions.DEFAULT_RETURNED_FIELDS_APP,
        breakdown_fields=breakdown,
        order_fields=order,
        offset=None,
        limit=None,
        constraints=constraints,
        constraints_list=constraints_list
    )

    cursor.close()

    if breakdown:
        return results

    return results[0]
