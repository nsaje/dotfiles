import copy
import json
import logging
import time

from django.conf import settings

from dash import conversions_helper
from dash.models import Source
from reports import redshift
from reports.rs_helpers import from_nano, to_percent, sum_div, sum_agr, unchanged, max_agr, click_discrepancy, \
    decimal_to_int_exact, sum_expr, extract_json_or_null, from_cc, subtractions, mul_expr

from utils import s3helpers

logger = logging.getLogger(__name__)

FORMULA_BILLING_COST = '({} + {} + {})'.format(
    sum_agr('effective_cost_nano'),
    sum_agr('effective_data_cost_nano'),
    sum_agr('license_fee_nano'),
)
FORMULA_TOTAL_COST = '({}*1000 + {}*1000 + {})'.format(
    sum_agr('cost_nano'),
    sum_agr('data_cost_nano'),
    sum_agr('license_fee_nano'),
)

# UNBOUNCED_VISITS_FORMULA = sum_div(subtractions(sum_agr('visits'), sum_agr('bounced_visits')), 100)
UNBOUNCED_VISITS_FORMULA = "(({} - {}) / {})".format(sum_agr('visits'), sum_agr('bounced_visits'), sum_agr('visits'))


OB_PUBLISHERS_KEY_FORMAT = 'ob_publishers_raw/{year}/{month:02d}/{day:02d}/{ad_group_id}/{ts}.json'


class RSPublishersModel(redshift.RSModel):
    TABLE_NAME = 'publishers_1'

    # fields that are always returned (app-based naming)
    DEFAULT_RETURNED_FIELDS_APP = [
        "clicks", "impressions", "cost", "data_cost", "media_cost", "ctr", "cpc",
        "e_media_cost", "e_data_cost", "total_cost", "billing_cost", "license_fee",
        "external_id", "visits", "click_discrepancy", "pageviews", "new_visits",
        "percent_new_users", "bounce_rate", "pv_per_visit", "avg_tos", "total_seconds",
        "avg_cost_per_second", "unbounced_visits" #;, "avg_cost_per_non_bounced_visitor",
        #"total_pageviews", "avg_cost_per_pageview"

    ]
    # fields that are allowed for breakdowns (app-based naming)
    ALLOWED_BREAKDOWN_FIELDS_APP = set(['exchange', 'domain', 'ad_group', 'date'])

    # 	SQL NAME                           APP NAME            OUTPUT TRANSFORM        AGGREGATE                                  ORDER BY function
    _FIELDS = [
        dict(sql='clicks_sum',             app='clicks',       out=unchanged,          calc=sum_agr('clicks')),
        dict(sql='impressions_sum',        app='impressions',  out=unchanged,          calc=sum_agr('impressions'),               order="SUM(impressions) = 0, impressions_sum {direction}"),
        dict(sql='domain',                 app='domain',       out=unchanged),
        dict(sql='exchange',               app='exchange',     out=unchanged),
        dict(sql='external_id',            app='external_id',  out=unchanged,          calc=max_agr('external_id')),
        dict(sql='date',                   app='date',         out=unchanged),
        dict(sql='cost_nano_sum',          app='cost',         out=from_nano,          calc=sum_agr('cost_nano'),                 order="SUM(cost_nano) = 0, cost_nano_sum {direction}"),
        dict(sql='media_cost_nano_sum',    app='media_cost',   out=from_nano,          calc=sum_agr('cost_nano'),                 order="SUM(cost_nano) = 0, cost_nano_sum {direction}"),
        dict(sql='data_cost_nano_sum',     app='data_cost',    out=from_nano,          calc=sum_agr('data_cost_nano'),            order="SUM(data_cost_nano) = 0, data_cost_nano_sum {direction}"),
        dict(sql='cpc_nano',               app='cpc',          out=from_nano,          calc=sum_div("cost_nano", "clicks"),       order="SUM(clicks) = 0, sum(cost_nano) IS NULL, cpc_nano {direction}"),  # makes sure nulls are last
        dict(sql='ctr',                    app='ctr',          out=to_percent,         calc=sum_div("clicks", "impressions"),     order="SUM(impressions) IS NULL, ctr {direction}"),
        dict(sql='adgroup_id',             app='ad_group',     out=unchanged),
        dict(sql='license_fee_nano_sum',   app='license_fee',  out=from_nano,          calc=sum_agr('license_fee_nano'),          order="license_fee_nano_sum = 0, license_fee_nano_sum {direction}"),
        dict(sql='e_media_cost_nano_sum',  app='e_media_cost', out=from_nano,          calc=sum_agr('effective_cost_nano'),       order="effective_cost_nano_sum = 0, cost_nano_sum {direction}"),
        dict(sql='e_data_cost_nano_sum',   app='e_data_cost',  out=from_nano,          calc=sum_agr('effective_data_cost_nano'),  order="data_cost_nano_sum = 0, data_cost_nano_sum {direction}"),
        dict(sql='billing_cost_nano_sum',  app='billing_cost', out=from_nano,          calc=FORMULA_BILLING_COST,                 order="billing_cost_nano_sum = 0, billing_cost_nano_sum {direction}"),
        dict(sql='total_cost_nano_sum',    app='total_cost',   out=from_nano,          calc=FORMULA_TOTAL_COST,                   order="total_cost_nano_sum = 0, total_cost_nano_sum {direction}"),
    ]

    _POSTCLICK_ACQUISITION_FIELDS = [
        dict(sql='visits_sum',              app='visits',               out=unchanged,          calc=sum_agr('visits')),
        dict(sql='click_discrepancy',       app='click_discrepancy',    out=to_percent,         calc=click_discrepancy('clicks', 'visits')),
        dict(sql='pageviews_sum',           app='pageviews',            out=unchanged,          calc=sum_agr('pageviews')),
    ]

    _POSTCLICK_ENGAGEMENT_FIELDS = [
        dict(sql='new_visits_sum',      app='new_visits',           out=unchanged,      calc=sum_agr('new_visits')),
        dict(sql='percent_new_users',   app='percent_new_users',    out=to_percent,     calc=sum_div('new_visits', 'visits')),
        dict(sql='bounce_rate',         app='bounce_rate',          out=to_percent,     calc=sum_div('bounced_visits', 'visits')),
        dict(sql='pv_per_visit',        app='pv_per_visit',         out=unchanged,      calc=sum_div('pageviews', 'visits')),
        dict(sql='avg_tos',             app='avg_tos',              out=unchanged,      calc=sum_div('total_time_on_site', 'visits')),
    ]

    _POSTCLICK_OPTIMIZATION_FIELDS = [
        dict(sql='total_seconds_sum',             app='total_seconds',                    out=unchanged,       calc=sum_agr('total_time_on_site')),
        dict(sql='total_seconds_avg_cost_sum',    app='avg_cost_per_second',              out=from_nano,       calc=sum_div('cost_nano', 'total_time_on_site')),
        dict(sql='unbounced_visits_diff',         app='unbounced_visits',                 out=to_percent,      calc=UNBOUNCED_VISITS_FORMULA),
        dict(sql='unbounced_visits_avg_cost_sum', app='avg_cost_per_non_bounced_visitor', out=from_nano,       calc=sum_div('cost_nano', UNBOUNCED_VISITS_FORMULA)),
        #dict(sql='total_pageviews_sum',           app='total_pageviews',                  out=to_percent,      calc=mul_expr('pv_per_visit', 'visits')),
        #dict(sql='avg_cost_per_pageview_sum',     app='avg_cost_per_pageview',            out=from_cc,         calc=sum_div('cost_cc', mul_expr('pv_per_visit', 'visits'))),
    ]

    _CONVERSION_GOAL_FIELDS = [
        dict(sql='conversions', app='conversions', out=decimal_to_int_exact,
             calc=sum_expr(extract_json_or_null('conversions')), num_json_params=2)
    ]

    FIELDS = _FIELDS +\
        _POSTCLICK_ACQUISITION_FIELDS +\
        _POSTCLICK_ENGAGEMENT_FIELDS +\
        _POSTCLICK_OPTIMIZATION_FIELDS +\
        _CONVERSION_GOAL_FIELDS


rs_pub = RSPublishersModel()


def query(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, conversion_goals=[], constraints={}, constraints_list=[]):
    conversion_goals = copy.copy(conversion_goals)

    constraints = copy.copy(constraints)
    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date
    cursor = redshift.get_cursor()

    returned_fields = rs_pub.DEFAULT_RETURNED_FIELDS_APP[:]
    for label in conversion_goals:
        returned_fields.append('conversions' + redshift.JSON_KEY_DELIMITER + label)

    results = rs_pub.execute_select_query(
        cursor,
        returned_fields,
        breakdown_fields,
        order_fields,
        offset,
        limit,
        constraints,
        constraints_list=constraints_list
    )

    cursor.close()

    results = conversions_helper.group_conversions(results)
    return results


def query_active_publishers(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}, constraints_list=[], conversion_goals=[]):
    return query(start_date, end_date,
        breakdown_fields=breakdown_fields,
        order_fields=order_fields,
        offset=offset,
        limit=limit,
        conversion_goals=conversion_goals,
        constraints=constraints,
        constraints_list=constraints_list
    )


def prepare_active_publishers_constraint_list(blacklist, use_touchpoint_fields):
    constraints_list = []
    if blacklist:
        aggregated_blacklist = _aggregate_domains(blacklist)

        if use_touchpoint_fields:
            _convert_exchange_to_source_id(aggregated_blacklist)

        # create a base object, then OR onto it
        rsq = ~_map_blacklist_to_rs_queryset(aggregated_blacklist[0], use_touchpoint_fields)
        for blacklist_entry in aggregated_blacklist[1:]:
            rsq &= ~_map_blacklist_to_rs_queryset(blacklist_entry, use_touchpoint_fields)
        constraints_list = [rsq]

    return constraints_list


def query_blacklisted_publishers(start_date, end_date, breakdown_fields=[], order_fields=[], offset=None, limit=None, constraints={}, constraints_list=[], conversion_goals=[]):
    return query(start_date, end_date,
        breakdown_fields=breakdown_fields,
        order_fields=order_fields,
        offset=offset,
        limit=limit,
        conversion_goals=conversion_goals,
        constraints=constraints,
        constraints_list=constraints_list
    )


def prepare_blacklisted_publishers_constraint_list(blacklist, breakdown_fields, use_touchpoint_fields):
    constraints_list = []
    if blacklist:
        aggregated_blacklist = _aggregate_domains(blacklist)

        if use_touchpoint_fields:
            _convert_exchange_to_source_id(aggregated_blacklist)

        # create a base object, then OR onto it
        rsq = _map_blacklist_to_rs_queryset(aggregated_blacklist[0], use_touchpoint_fields)
        for blacklist_entry in aggregated_blacklist[1:]:
            rsq |= _map_blacklist_to_rs_queryset(blacklist_entry, use_touchpoint_fields)
        constraints_list = [rsq]
    else:
        if breakdown_fields:
            return []
        else:
            return {}

    return constraints_list


def _convert_exchange_to_source_id(aggregated_blacklist):
    exchanges = set(filter(lambda x: x is not None, (agg.get('exchange') for agg in aggregated_blacklist)))

    sources = Source.objects.filter(bidder_slug__in=exchanges).values('id', 'bidder_slug')
    sources_by_exchange = {s['bidder_slug']: s['id'] for s in sources}

    for agg in aggregated_blacklist:
        if 'exchange' in agg:
            agg['source'] = sources_by_exchange[agg['exchange']]


def _aggregate_domains(blacklist):
    # creates a new blacklist that groups all domains that belong to same
    # adgroup_id and exchange into one list (thus reducing query size)

    aggregated_pubs = {}

    ret = []
    for blacklist_entry in blacklist:
        # treat global publishers separately
        if blacklist_entry.get('adgroup_id') is None:
            ret.append({
                'domain': blacklist_entry['domain'],
            })
            continue

        key = (blacklist_entry['adgroup_id'], blacklist_entry['exchange'])
        aggregated_pubs[key] = aggregated_pubs.get(key, []) + [blacklist_entry['domain']]
    for adgroup_id, exchange in aggregated_pubs:
        domain_list = aggregated_pubs[ (adgroup_id, exchange) ]
        if len(domain_list) == 1:
            domain_list = domain_list[0]

        ret.append({
            'domain': domain_list,
            'exchange': exchange,
            'adgroup_id': adgroup_id
        })
    return ret


def _map_blacklist_to_rs_queryset(blacklist, use_touchpoint_fields):
    if blacklist.get('adgroup_id') is not None:
        if use_touchpoint_fields:
            return redshift.RSQ(
                publisher=blacklist['domain'],
                source=blacklist['source'],
                ad_group=blacklist['adgroup_id'],
            )
        return redshift.RSQ(
            domain=blacklist['domain'],
            exchange=blacklist['exchange'],
            ad_group=blacklist['adgroup_id'],
        )
    else:
        if use_touchpoint_fields:
            return redshift.RSQ(
                publisher=blacklist['domain'],
            )
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


def put_ob_data_to_s3(date, ad_group, rows):
    key = OB_PUBLISHERS_KEY_FORMAT.format(
        year=date.year,
        month=date.month,
        day=date.day,
        ad_group_id=ad_group.id,
        ts=int(time.time()*1000)
    )
    s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS).put(key, json.dumps(rows))
