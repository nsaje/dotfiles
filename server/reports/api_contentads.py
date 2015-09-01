import collections
import logging

from utils import exc

import dash.models
import reports.models

from django.db import connections, transaction
from reports import models
from reports import aggregate_fields
from reports import api_helpers

logger = logging.getLogger(__name__)


def query(start_date, end_date, breakdown=None, **constraints):
    constraints = _preprocess_constraints(constraints)

    stats = models.ContentAdStats.objects.filter(
        date__gte=start_date, date__lte=end_date, **constraints)

    if breakdown:
        breakdown = _preprocess_breakdown(breakdown)
        stats = stats.values(*breakdown).annotate(**aggregate_fields.AGGREGATE_FIELDS)
        return [_transform_row(s) for s in stats]

    stats = stats.aggregate(**aggregate_fields.AGGREGATE_FIELDS)

    return _transform_row(stats)


def _sumdiv(expr, divisor, name):
    return "CASE WHEN SUM({divis}) <> 0 THEN SUM(CAST({expr} AS FLOAT)) / SUM({divis}) ELSE NULL END as {name}".format(
        expr=expr,
        divis=divisor,
        name=name
    )


# TODO: queries will reside here for now
# they will work pretty much the same as current queries to database
def query_redshift(start_date, end_date, breakdown=None):

    proper_breakdown = None
    if breakdown:
        proper_breakdown = []
        for col in breakdown:
            if col == 'date':
                proper_breakdown.append('datetime')
            elif col == 'content_ad':
                proper_breakdown.append('content_ad_id')
            elif col == 'source':
                proper_breakdown.append('source_id')
            elif col == 'campaign':
                proper_breakdown.append('campaign_id')
            elif col == 'account':
                proper_breakdown.append('account_id')
            elif col == 'ad_group':
                proper_breakdown.append('adgroup_id')
            else:
                proper_breakdown.append(col)


    aggregate_columns = ','.join(proper_breakdown or [])
    if aggregate_columns != '':
        aggregate_columns = ",{ex}".format(ex=aggregate_columns)
    if aggregate_columns != '':
        group_by_clause = 'GROUP BY content_ad_id {cols}'.format(cols=aggregate_columns)
    else:
        group_by_clause = ''

    postclick_columns = ','.join([
        "SUM(visits) AS visits_sum",
        "SUM(new_visits) AS new_visits_sum",
        "SUM(pageviews) AS pageviews_sum",
        _sumdiv('new_visits', 'visits', 'percent_new_users'),
        _sumdiv('bounced_visits', 'visits', 'bounce_rate'),
        _sumdiv('pageviews', 'visits', 'pv_per_visit'),
        _sumdiv('total_time_on_site', 'visits', 'avg_tos')
    ])
    if postclick_columns != '':
        postclick_columns = ',{ex}'.format(ex=postclick_columns)

    query = "SELECT content_ad_id {postclick_cols} FROM contentadstats WHERE \
        datetime >= '{date_from}' AND datetime <= '{date_to}' \
        {group_clause}".format(
            postclick_cols=postclick_columns,
            date_from=start_date,
            date_to=end_date,
            group_clause=group_by_clause
        )

    db = connections['redshift']
    if not db:
        raise Exception('Redshift DB not configured')
    cursor = db.cursor()
    cursor.execute(query)

    return cursor.fetchall()


def _preprocess_breakdown(breakdown):
    if not breakdown or len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    breakdown_field_translate = {
        'ad_group': 'content_ad__ad_group'
    }

    breakdown = [] if breakdown is None else breakdown[:]

    fields = [breakdown_field_translate.get(field, field) for field in breakdown]

    return fields


def _preprocess_constraints(constraints):
    constraint_field_translate = {
        'ad_group': 'content_ad__ad_group',
        'campaign': 'content_ad__ad_group__campaign'
    }

    result = {}
    for k, v in constraints.iteritems():
        k = constraint_field_translate.get(k, k)

        if isinstance(v, collections.Sequence):
            result['{0}__in'.format(k)] = v
        else:
            result[k] = v

    return result


def _transform_row(row):
    result = {}
    for name, val in row.items():
        if name == 'content_ad__ad_group':
            name = 'ad_group'
        else:
            val = aggregate_fields.transform_val(name, val)
            name = aggregate_fields.transform_name(name)

        result[name] = val

    return result
