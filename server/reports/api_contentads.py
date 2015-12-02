import logging
import copy
import datetime
import pytz

from django.conf import settings

from reports import redshift
from reports import api
from reports.db_raw_helpers import extract_obj_ids
import reports.rs_helpers as rsh

import dash.models
import dash.constants

logger = logging.getLogger(__name__)


class RSContentAdStatsModel(redshift.RSModel):
    TABLE_NAME = 'contentadstats'

    # 	SQL NAME                   APP NAME           OUTPUT TRANSFORM      AGGREGATE
    _BREAKDOWN_FIELDS = [
        dict(sql='date',          app='date',        out=rsh.unchanged),
        dict(sql='content_ad_id', app='content_ad',  out=rsh.unchanged),
        dict(sql='source_id',     app='source',      out=rsh.unchanged),
        dict(sql='adgroup_id',    app='ad_group',    out=rsh.unchanged),
        dict(sql='campaign_id',   app='campaign',    out=rsh.unchanged),
        dict(sql='account_id',    app='account',     out=rsh.unchanged),
    ]

    _TRAFFIC_FIELDS = [
        dict(sql='clicks_sum',      app='clicks',      out=rsh.unchanged,   calc=rsh.sum_agr('clicks')),
        dict(sql='impressions_sum', app='impressions', out=rsh.unchanged,   calc=rsh.sum_agr('impressions')),
        dict(sql='cost_cc_sum',     app='cost',        out=rsh.from_cc,     calc=rsh.sum_agr('cost_cc')),
        dict(sql='data_cost_cc_sum',app='data_cost',   out=rsh.from_cc,     calc=rsh.sum_agr('data_cost_cc')),        
        dict(sql='ctr',             app='ctr',         out=rsh.to_percent,  calc=rsh.sum_div('clicks', 'impressions')),
        dict(sql='cpc_cc',          app='cpc',         out=rsh.from_cc,     calc=rsh.sum_div('cost_cc', 'clicks')),
    ]

    _POSTCLICK_ACQUISITION_FIELDS = [
        dict(sql='visits_sum',         app='visits',            out=rsh.unchanged,   calc=rsh.sum_agr('visits')),
        dict(sql='click_discrepancy',  app='click_discrepancy', out=rsh.to_percent,  calc=rsh.click_discrepancy('clicks', 'visits')),
        dict(sql='pageviews_sum',      app='pageviews',         out=rsh.unchanged,   calc=rsh.sum_agr('pageviews')),
    ]

    _POSTCLICK_ENGAGEMENT_FIELDS = [
        dict(sql='new_visits_sum',     app='new_visits',        out=rsh.unchanged,   calc=rsh.sum_agr('new_visits')),
        dict(sql='percent_new_users',  app='percent_new_users', out=rsh.to_percent,  calc=rsh.sum_div('new_visits', 'visits')),
        dict(sql='bounce_rate',        app='bounce_rate',       out=rsh.to_percent,  calc=rsh.sum_div('bounced_visits', 'visits')),
        dict(sql='pv_per_visit',       app='pv_per_visit',      out=rsh.unchanged,   calc=rsh.sum_div('pageviews', 'visits')),
        dict(sql='avg_tos',            app='avg_tos',           out=rsh.unchanged,   calc=rsh.sum_div('total_time_on_site', 'visits')),
    ]

    _CONVERSION_GOAL_FIELDS = [
        dict(sql='conversions', app='conversions', out=rsh.decimal_to_int_exact, calc=rsh.sum_expr(rsh.extract_json_or_null('conversions')), num_json_params=2)
    ]

    _OTHER_AGGREGATIONS = [
        dict(sql='total_time_on_site', app='duration', out=rsh.unchanged),
        dict(sql='has_postclick_metrics', app='has_postclick_metrics', out=rsh.unchanged,
             calc=rsh.is_all_null(['visits', 'pageviews', 'new_visits', 'bounced_visits', 'total_time_on_site']))
    ]

    FIELDS = _BREAKDOWN_FIELDS + _TRAFFIC_FIELDS + _POSTCLICK_ENGAGEMENT_FIELDS + _POSTCLICK_ACQUISITION_FIELDS + _CONVERSION_GOAL_FIELDS + _OTHER_AGGREGATIONS

    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _TRAFFIC_FIELDS + _POSTCLICK_ENGAGEMENT_FIELDS + _POSTCLICK_ACQUISITION_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _BREAKDOWN_FIELDS)


RSContentAdStats = RSContentAdStatsModel()


def query(start_date, end_date, breakdown=[], order=[], ignore_diff_rows=False, conversion_goals=[], **constraints):
    # TODO: it would be nicer if 'constraints' would be a dict, but we use kwargs to maintain
    # compatibility with reports.api
    breakdown = copy.copy(breakdown)
    conversion_goals = copy.copy(conversion_goals)
    order = copy.copy(order)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date

    if ignore_diff_rows:
        # In contentadstats table in redshift there are certain rows that have
        # a special content_ad_id - these contain difference between old stats
        # from ArticleStats table and new stats from ContentAdStats. These rows
        # must be ignored on Content Ads tab, since they cannot be distributed
        # between content ads correctly.
        constraints['content_ad__neq'] = redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID

    constraints = extract_obj_ids(constraints)

    cursor = redshift.get_cursor()

    returned_fields = RSContentAdStats.DEFAULT_RETURNED_FIELDS_APP[:]
    for label in conversion_goals:
        returned_fields.append('conversions' + redshift.JSON_KEY_DELIMITER + label)

    results = RSContentAdStats.execute_select_query(
        cursor,
        returned_fields,
        breakdown_fields=breakdown,
        order_fields=order,
        offset=None,
        limit=None,
        constraints=constraints
    )

    cursor.close()

    results = _transform_conversions(results)
    if breakdown:
        return results

    return results[0] if len(results) else {}


def _transform_conversions(rows):
    results = []
    for row in rows:
        new_row = {}
        for key, val in row.iteritems():
            if key.startswith('conversions'):
                _, json_key = redshift.extract_json_key_parts(key)
                new_row.setdefault('conversions', {})
                new_row['conversions'][json_key] = val
                continue
            new_row[key] = val
        results.append(new_row)
    return results


def has_complete_postclick_metrics_accounts(start_date, end_date, accounts, sources):
    # helper function for compatibility with reports.api
    return has_complete_postclick_metrics(
        start_date,
        end_date,
        level_constraints={'account': accounts},
        sources=sources,
    )


def has_complete_postclick_metrics_campaigns(start_date, end_date, campaigns, sources):
    # helper function for compatibility with reports.api
    return has_complete_postclick_metrics(
        start_date,
        end_date,
        level_constraints={'campaign': campaigns},
        sources=sources,
    )


def has_complete_postclick_metrics_ad_groups(start_date, end_date, ad_groups, sources):
    # helper function for compatibility with reports.api
    return has_complete_postclick_metrics(
        start_date,
        end_date,
        level_constraints={'ad_group': ad_groups},
        sources=sources,
    )


def _get_ad_group_ids_with_postclick_data(cursor, level_constraints_ids, exclude_archived=True):
    """
    Filters the objects that are passed in and returns ids
    of only those that have any postclick metric data.
    """

    constraints = level_constraints_ids

    if exclude_archived:
        ad_groups = dash.models.AdGroup.objects.all().exclude_archived()

        if 'ad_group' in constraints:
            ad_groups = ad_groups.filter(pk__in=constraints['ad_group'])

        # be sure to select only ids
        constraints['ad_group'] = ad_groups.values_list('pk', flat=True)

    has_postclick_metrics_sql = RSContentAdStats.by_app_mapping['has_postclick_metrics']['calc']
    having_constraints = [
        '({})=1'.format(has_postclick_metrics_sql)
    ]

    results = RSContentAdStats.execute_select_query(
        cursor,
        returned_fields=['has_postclick_metrics'],
        breakdown_fields=['ad_group'],
        order_fields=[],
        offset=None,
        limit=None,
        constraints=constraints,
        having_constraints=having_constraints
    )

    return [x['ad_group'] for x in results]


def has_complete_postclick_metrics(start_date, end_date, level_constraints, sources):
    """
    Returns True if passed-in objects have complete postclick data for the
    specified date range. All objects that don't have this data at all are ignored.
    """

    cursor = redshift.get_cursor()

    level_constraints_ids = extract_obj_ids(copy.copy(level_constraints))
    source_ids = extract_obj_ids(sources)

    ad_group_ids = _get_ad_group_ids_with_postclick_data(cursor, level_constraints_ids)
    if len(ad_group_ids) == 0:
        return True

    constraints = {
        'date__gte': start_date,
        'date__lte': end_date,
        'ad_group': ad_group_ids,
        'source': source_ids
    }

    results = RSContentAdStats.execute_select_query(
        cursor,
        returned_fields=['ad_group', 'date', 'has_postclick_metrics'],
        breakdown_fields=['ad_group', 'date'],
        order_fields=[],
        offset=None,
        limit=None,
        constraints=constraints
    )

    cursor.close()
    return all(x['has_postclick_metrics'] for x in results)


def row_has_traffic_data(row):
    # TODO: helper function for compatibility with reports.api
    return api.row_has_traffic_data(row)


def row_has_postclick_data(row):
    # TODO: helper function for compatibility with reports.api
    return api.row_has_postclick_data(row)


def get_yesterday_cost(**constraints):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today = datetime.datetime(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)

    rs = get_day_cost(yesterday, breakdown=['source'], **constraints)

    result = {row['source']: row['cost'] if row['cost'] else 0.0 for row in rs}
    return result


def get_day_cost(day, breakdown=None, **constraints):
    rs = query(
        start_date=day,
        end_date=day,
        breakdown=breakdown,
        **constraints
    )
    return rs


def remove_contentadstats(ad_group_id):
    """
    Completely removes stats for the selected ad group id
    """

    if not ad_group_id:
        return

    cursor = redshift.get_cursor()
    RSContentAdStats.execute_delete(cursor, {'ad_group': ad_group_id})
    cursor.close()
