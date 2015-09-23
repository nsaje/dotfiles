import logging
import copy

from reports import redshift
import reports.rs_helpers as rsh

logger = logging.getLogger(__name__)


class RSContentAdStatsModel(redshift.RSModel):
    TABLE_NAME = 'contentadstats'

    # 	SQL NAME                   APP NAME           OUTPUT TRANSFORM                    AGGREGATE                              ORDER BY function
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
    ALLOWED_BREAKDOWN_FIELDS_APP = set(['content_ad', 'ad_group', 'date', 'source', 'account', 'campaign'])

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
