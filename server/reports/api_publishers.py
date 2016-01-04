import logging
import copy
from reports import redshift

from reports.rs_helpers import from_micro_cpm, from_nano, to_percent, sum_div, sum_agr, unchanged

logger = logging.getLogger(__name__)

FORMULA_BILLING_COST = '({} + {} + {})'.format(
    sum_agr('effective_cost_nano'),
    sum_agr('effective_data_cost_nano'),
    sum_agr('license_fee_nano'),
)
FORMULA_TOTAL_COST = '({}*1000 + {}*1000 + {})'.format(
    sum_agr('cost_micro'),
    sum_agr('data_cost_micro'),
    sum_agr('license_fee_nano'),
)

class RSPublishersModel(redshift.RSModel):
    TABLE_NAME = 'joint_publishers_1_3'

    # fields that are always returned (app-based naming)
    DEFAULT_RETURNED_FIELDS_APP = [
        "clicks", "impressions", "cost", "data_cost", "media_cost", "ctr", "cpc",
        "e_media_cost", "e_data_cost", "total_cost", "billing_cost", "license_fee",
    ]
    # fields that are allowed for breakdowns (app-based naming)
    ALLOWED_BREAKDOWN_FIELDS_APP = set(['exchange', 'domain', 'date', ])

    # 	SQL NAME                           APP NAME            OUTPUT TRANSFORM        AGGREGATE                                  ORDER BY function
    FIELDS = [
        dict(sql='clicks_sum',             app='clicks',       out=unchanged,          calc=sum_agr('clicks')),
        dict(sql='impressions_sum',        app='impressions',  out=unchanged,          calc=sum_agr('impressions'),               order="SUM(impressions) = 0, impressions_sum {direction}"),
        dict(sql='domain',                 app='domain',       out=unchanged),
        dict(sql='exchange',               app='exchange',     out=unchanged),
        dict(sql='date',                   app='date',         out=unchanged),
        dict(sql='cost_micro_sum',         app='cost',         out=from_micro_cpm,     calc=sum_agr('cost_micro'),                order="SUM(cost_micro) = 0, cost_micro_sum {direction}"),
        dict(sql='media_cost_micro_sum',   app='media_cost',   out=from_micro_cpm,     calc=sum_agr('cost_micro'),                order="SUM(cost_micro) = 0, cost_micro_sum {direction}"),
        dict(sql='data_cost_micro_sum',    app='data_cost',    out=from_micro_cpm,     calc=sum_agr('data_cost_micro'),           order="SUM(data_cost_micro) = 0, data_cost_micro_sum {direction}"),
        dict(sql='cpc_micro',              app='cpc',          out=from_micro_cpm,     calc=sum_div("cost_micro", "clicks"),      order="SUM(clicks) = 0, sum(cost_micro) IS NULL, cpc_micro {direction}"),  # makes sure nulls are last
        dict(sql='ctr',                    app='ctr',          out=to_percent,         calc=sum_div("clicks", "impressions"),     order="SUM(impressions) IS NULL, ctr {direction}"),
        dict(sql='adgroup_id',             app='ad_group',     out=unchanged),
        dict(sql='license_fee_nano_sum',   app='license_fee',  out=from_nano,          calc=sum_agr('license_fee_nano'),          order="license_fee_nano_sum = 0, license_fee_nano_sum {direction}"),
        dict(sql='e_media_cost_nano_sum',  app='e_media_cost', out=from_nano,          calc=sum_agr('effective_cost_nano'),       order="effective_cost_nano_sum = 0, cost_micro_sum {direction}"),
        dict(sql='e_data_cost_nano_sum',   app='e_data_cost',  out=from_nano,          calc=sum_agr('effective_data_cost_nano'),  order="data_cost_micro_sum = 0, data_cost_micro_sum {direction}"),
        dict(sql='billing_cost_nano_sum',  app='billing_cost', out=from_nano,          calc=FORMULA_BILLING_COST,                 order="billing_cost_nano_sum = 0, billing_cost_nano_sum {direction}"),
        dict(sql='total_cost_nano_sum',    app='total_cost',   out=from_nano,          calc=FORMULA_TOTAL_COST,                   order="total_cost_micro_sum = 0, total_cost_micro_sum {direction}"),
    ]


class RSOutbrainPublishersModel(RSPublishersModel):
    TABLE_NAME = 'ob_publishers_2'

    FIELDS = copy.copy(RSPublishersModel.FIELDS) + [
        # The following are only available for Outbrain tables
        dict(sql='ob_id',   app='ob_id',   out=lambda v: v),
        dict(sql='name',    app='name',            out=lambda v: v),
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
        rsq = ~_map_blacklist_to_rs_queryset(blacklist[0])
        for blacklist_entry in blacklist[1:]:
            rsq &= ~_map_blacklist_to_rs_queryset(blacklist_entry)
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
    fields_sql = ['date', 'adgroup_id', 'exchange', 'domain', 'name', 'clicks', 'cost_micro', 'ob_id']
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
        newrow = (date, ad_group, exchange, url, row['name'], row['clicks'], cost * 1000000000, row['ob_id'])
        row_tuples.append(newrow)

    cursor = redshift.get_cursor()
    rs_ob_pub.execute_delete(cursor, {'date__eq': date, 'ad_group__eq': ad_group, 'exchange__eq': exchange})
    rs_ob_pub.execute_multi_insert_sql(cursor, fields_sql, row_tuples)
    cursor.close()
