import logging
import copy

from reports import redshift
from reports import models
import reports.rs_helpers as rsh

import dash.models

logger = logging.getLogger(__name__)


class RSContentAdStatsModel(redshift.RSModel):
    TABLE_NAME = 'contentadstats'

    # 	SQL NAME                   APP NAME           OUTPUT TRANSFORM      AGGREGATE
    _DIMENSIONS_FIELDS = [
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

    FIELDS = _DIMENSIONS_FIELDS + _TRAFFIC_FIELDS + _POSTCLICK_ENGAGEMENT_FIELDS + _POSTCLICK_ACQUISITION_FIELDS

    DEFAULT_RETURNED_FIELDS_APP = [f['app'] for f in _TRAFFIC_FIELDS + _POSTCLICK_ENGAGEMENT_FIELDS + _POSTCLICK_ACQUISITION_FIELDS]
    ALLOWED_BREAKDOWN_FIELDS_APP = set(f['app'] for f in _DIMENSIONS_FIELDS)

logger = logging.getLogger(__name__)


RSContentAdStats = RSContentAdStatsModel()


def query(start_date, end_date, breakdown=[], constraints={}):

    constraints = copy.copy(constraints)

    constraints['date__gte'] = start_date
    constraints['date__lte'] = end_date

    cursor = redshift.get_cursor()

    results = RSContentAdStats.execute_select_query(
        cursor,
        RSContentAdStats.DEFAULT_RETURNED_FIELDS_APP,
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


def has_complete_postclick_metrics_accounts(start_date, end_date, accounts, sources):
    return _has_complete_postclick_metrics(
        start_date,
        end_date,
        'account',
        accounts,
        sources,
    )


def has_complete_postclick_metrics_campaigns(start_date, end_date, campaigns, sources):
    return _has_complete_postclick_metrics(
        start_date,
        end_date,
        'campaign',
        campaigns,
        sources
    )


def has_complete_postclick_metrics_ad_groups(start_date, end_date, ad_groups, sources):

    return _has_complete_postclick_metrics(
        start_date,
        end_date,
        'ad_group',
        ad_groups,
        sources
    )


#  app_name: sql_name
POSTCLICK_METRICS_TABLE_MAPPING = {
    'duration': 'total_time_on_site'
}

HAS_POSTCLICK_METRICS_CONDITION = rsh.is_all_null([POSTCLICK_METRICS_TABLE_MAPPING.get(f, f) for f in models.POSTCLICK_METRICS])


class RSHasPostclickMetricsModel(RSContentAdStatsModel):

    FIELDS = copy.copy(RSContentAdStatsModel.FIELDS) + [
        dict(sql='has_postclick_metrics', app='has_postclick_metrics', out=rsh.unchanged,
             calc=HAS_POSTCLICK_METRICS_CONDITION),
    ]


RSHasPostclickMetrics = RSHasPostclickMetricsModel()


def _get_ad_group_ids_with_postclick_data(key, objects, exclude_archived=True):
    """
    Filters the objects that are passed in and returns ids
    of only those that have any postclick metric data.
    """

    constraints = {
        key: objects
    }

    if exclude_archived:
        ad_groups = dash.models.AdGroup.objects.all().exclude_archived()

        if key == 'ad_group':
            ad_groups = ad_groups.filter(pk__in=[adg.pk for adg in objects])

        constraints['ad_group'] = ad_groups

    having_constraints = [
        '({})=1'.format(HAS_POSTCLICK_METRICS_CONDITION)
    ]

    cursor = redshift.get_cursor()

    results = RSHasPostclickMetrics.execute_select_query(
        cursor,
        ['has_postclick_metrics'],
        ['ad_group'],
        order_fields=[],
        offset=None,
        limit=None,
        constraints=constraints,
        having_constraints=having_constraints
    )

    cursor.close()
    return [x['ad_group'] for x in results]


def _has_complete_postclick_metrics(start_date, end_date, key, objects, sources):
    """
    Returns True if passed-in objects have complete postclick data for the
    specfied date range. All objects that don't have this data at all are ignored.
    """

    ad_group_ids = _get_ad_group_ids_with_postclick_data(key, objects)
    if len(ad_group_ids) == 0:
        return True

    constraints = {
        'date__gte': start_date,
        'date__lte': end_date,
        'ad_group': ad_group_ids,
        'source': sources
    }

    cursor = redshift.get_cursor()

    results = RSHasPostclickMetrics.execute_select_query(
        cursor,
        ['ad_group', 'date', 'has_postclick_metrics'],
        ['ad_group', 'date'],
        order_fields=[],
        offset=None,
        limit=None,
        constraints=constraints
    )

    cursor.close()
    return all(x['has_postclick_metrics'] for x in results)
