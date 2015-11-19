import logging
import copy
from reports import redshift

from reports.rs_helpers import from_micro_cpm, to_percent, sum_div, sum_agr

logger = logging.getLogger(__name__)


class RSPublishersModel(redshift.RSModel):
    TABLE_NAME = 'joint_publishers_1'

    # fields that are always returned (app-based naming)
    DEFAULT_RETURNED_FIELDS_APP = ["clicks", "impressions", "cost", "ctr", "cpc"]
    # fields that are allowed for breakdowns (app-based naming)
    ALLOWED_BREAKDOWN_FIELDS_APP = set(['exchange', 'domain', 'date', ])

    # 	SQL NAME                   APP NAME           OUTPUT TRANSFORM                    AGGREGATE                              ORDER BY function
    FIELDS = [
        dict(sql='clicks_sum',      app='clicks',      out=lambda v: v,                    calc=sum_agr('clicks')),
        dict(sql='impressions_sum', app='impressions', out=lambda v: v,                    calc=sum_agr('impressions'),          order="SUM(impressions) = 0, impressions_sum {direction}"),
        dict(sql='domain',          app='domain',      out=lambda v: v),
        dict(sql='exchange',        app='exchange',    out=lambda v: v),
        dict(sql='date',            app='date',        out=lambda v: v),
        dict(sql='cost_micro_sum',  app='cost',        out=lambda v: from_micro_cpm(v),    calc=sum_agr('cost_micro'),            order="SUM(cost_micro) = 0, cost_micro_sum {direction}"),
        dict(sql='cpc_micro',       app='cpc',         out=lambda v: from_micro_cpm(v),    calc=sum_div("cost_micro", "clicks"),  order="SUM(clicks) = 0, sum(cost_micro) IS NULL, cpc_micro {direction}"),  # makes sure nulls are last
        dict(sql='ctr',             app='ctr',         out=lambda v: to_percent(v),        calc=sum_div("clicks", "impressions"), order="sum(impressions) IS NULL, ctr {direction}"),
        dict(sql='adgroup_id',      app='ad_group',    out=lambda v: v),
    ]


class RSOutbrainPublishersModel(RSPublishersModel):
    TABLE_NAME = 'ob_publishers_1'

    FIELDS = copy.copy(RSPublishersModel.FIELDS) + [
        # The following are only available for Outbrain tables
        dict(sql='ob_section_id',   app='ob_section_id',   out=lambda v: v),
        dict(sql='name',            app='name',            out=lambda v: v),
    ]


rs_pub = RSPublishersModel()
rs_ob_pub = RSOutbrainPublishersModel()


def query(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}, constraints_list=[]):
    constraints = copy.copy(constraints)
    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date
    cursor = redshift.get_cursor()
    results = rs_pub.execute_select_query(
        cursor,
        rs_pub.DEFAULT_RETURNED_FIELDS_APP,
        breakdown_fields,
        order_fields,
        offset,
        limit,
        constraints,
        constraints_list=constraints_list
    )

    cursor.close()
    if breakdown_fields:
        return results
    else:
        return results[0]


def query_active_publishers(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}, blacklist=[]):
    constraints_list = []
    if blacklist:
        # create a base object, then OR onto it
        rsq = ~redshift.RSQ(
            domain=blacklist[0]['domain'],
            exchange=blacklist[0]['exchange'],
            ad_group=blacklist[0]['adgroup_id']
        )
        for blacklist_entry in blacklist[1:]:
            rsq &= ~redshift.RSQ(
                domain=blacklist_entry['domain'],
                exchange=blacklist_entry['exchange'],
                ad_group=blacklist_entry['adgroup_id']
            )
        constraints_list = [rsq]

    return query(start_date, end_date,
        breakdown_fields=breakdown_fields,
        order_fields=order_fields,
        offset=offset,
        limit=limit,
        constraints=constraints,
        constraints_list=constraints_list
    )


def query_blacklisted_publishers(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}, blacklist=[]):
    constraints_list = []
    if blacklist:
        # create a base object, then OR onto it
        rsq = _map_blacklist_to_rs_queryset(blacklist[0])
        for blacklist_entry in blacklist[1:]:
            rsq |= _map_blacklist_to_rs_queryset(blacklist_entry)
        constraints_list = [rsq]
    else:
        if breakdown_fields:
            return []
        else:
            return {}

    return query(start_date, end_date,
        breakdown_fields=breakdown_fields,
        order_fields=order_fields,
        offset=offset,
        limit=limit,
        constraints=constraints,
        constraints_list=constraints_list
    )


def _map_blacklist_to_rs_queryset(blacklist):
    if blacklist.get('adgroup_id') is not None:
        return redshift.RSQ(
            domain=blacklist['domain'],
            exchange=blacklist['exchange'],
            ad_group=blacklist['adgroup_id']
        )
    else:
        return redshift.RSQ(
            domain=blacklist['domain'],
            exchange=blacklist['exchange'],
        )


def query_publisher_list(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}):
    constraints = copy.copy(constraints)
    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date
    cursor = redshift.get_cursor()
    no_returned_fields = []
    results = rs_pub.execute_select_query(
        cursor,
        no_returned_fields,
        breakdown_fields,
        order_fields,
        offset,
        limit,
        constraints)

    cursor.close()
    return results


def ob_insert_adgroup_date(date, ad_group, exchange, datarowdicts, total_cost):
    # TODO: Execute this inside a transaction
    fields_sql = ['date', 'adgroup_id', 'exchange', 'domain', 'name', 'clicks', 'cost_micro', 'ob_section_id']
    row_tuples = []
    total_clicks = 0
    for row in datarowdicts:
        total_clicks += row['clicks']

    for row in datarowdicts:
        # strip http:
        url = row['url']
        if url.startswith("https://"):
            url = url[8:]
        if url.startswith("http://"):
            url = url[7:]
        url = url.strip("/")
        cost = 1.0 * row['clicks'] / total_clicks * total_cost
        newrow = (date, ad_group, exchange, url, row['name'], row['clicks'], cost * 1000000000, row['ob_section_id'])
        row_tuples.append(newrow)

    cursor = redshift.get_cursor()
    rs_ob_pub.execute_delete(cursor, {'date__eq': date, 'ad_group__eq': ad_group, 'exchange__eq': exchange})
    rs_ob_pub.execute_multi_insert_sql(cursor, fields_sql, row_tuples)
    cursor.close()
