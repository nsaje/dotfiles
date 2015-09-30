import json

from django.db.models import Sum, Max
from django.db import connection, transaction
from django.conf import settings

import reports.models
from reports.db_raw_helpers import dictfetchall
from reports import redshift

import dash.models


def _get_joined_stats_rows(date, ad_group_id, source_id):
    query = '''SELECT s.source_id as source_id1, p.source_id as source_id2,
                      s.content_ad_id as content_ad_id1, p.content_ad_id as content_ad_id2,
                      s.date as date1, p.date as date2, cost_cc, data_cost_cc, impressions, clicks,
                      visits, new_visits, bounced_visits, pageviews, total_time_on_site
            FROM reports_contentadstats s FULL OUTER JOIN reports_contentadpostclickstats p
            ON s.date = p.date AND s.content_ad_id = p.content_ad_id AND s.source_id = p.source_id
            WHERE (s.date = %(date)s OR p.date = %(date)s)
            AND (s.content_ad_id IN (
                SELECT id FROM dash_contentad WHERE ad_group_id = %(ad_group_id)s
            ) OR p.content_ad_id IN (
                SELECT id FROM dash_contentad WHERE ad_group_id = %(ad_group_id)s
            ))'''

    params = {'date': date.isoformat(), 'ad_group_id': ad_group_id}

    if source_id:
        query = query + ' AND (s.source_id = %(source_id)s OR p.source_id = %(source_id)s)'
        params['source_id'] = source_id

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = dictfetchall(cursor)

    return map(_normalize_join_cols, rows)


def _normalize_join_cols(row):
    """When doing outer join in Django, columns with same names
    in both tables can get overriden if one of them is null.
    As a workaround, we select both of them by giving them different names
    and then choose the right one."""

    cols = ['date', 'content_ad_id', 'source_id']

    for col in cols:
        row[col] = row[col + '1'] or row[col + '2']
        del row[col + '1']
        del row[col + '2']

    return row


def _dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def _get_goals_dict(date, ad_group_id, source_id):
    goals = reports.models.ContentAdGoalConversionStats.objects.filter(
        date=date,
        content_ad__ad_group_id=ad_group_id,
    )

    if source_id:
        goals = goals.filter(source_id=source_id)

    goals_dict = {}
    for goal in goals:
        if (goal.content_ad_id, goal.source_id) not in goals_dict:
            goals_dict[(goal.content_ad_id, goal.source_id)] = []

        goals_dict[(goal.content_ad_id, goal.source_id)].append(goal)

    return goals_dict


def _add_goals(row, goals_dict):
    content_ad_id = row['content_ad_id']
    source_id = row['source_id']

    goals = goals_dict.get((content_ad_id, source_id), [])

    row['conversions'] = _get_goals_json(goals)

    return row


def _add_ids(row, ad_group):
    row['adgroup_id'] = ad_group.id
    row['campaign_id'] = ad_group.campaign_id
    row['account_id'] = ad_group.campaign.account_id

    return row


def _get_goals_json(goals):
    result = {}
    for goal in goals:
        key = '{}__{}'.format(goal.goal_type, goal.goal_name)
        result[key] = goal.conversions

    return json.dumps(result)


# @transaction.atomic(using=settings.STATS_DB_NAME)
def refresh_contentadstats(date, ad_group, source=None):
    source_id = source.id if source is not None else None

    # join data
    rows = _get_joined_stats_rows(date, ad_group.id, source_id)
    goals_dict = _get_goals_dict(date, ad_group.id, source_id)

    rows = [_add_goals(row, goals_dict) for row in rows]
    rows = [_add_ids(row, ad_group) for row in rows]

    # redshift.delete_contentadstats(date, ad_group.id, source_id)
    # redshift.insert_contentadstats(rows)


def refresh_adgroup_stats(**constraints):
    # make sure we only filter by the allowed dimensions
    assert len(set(constraints.keys()) - {'datetime', 'ad_group', 'source'}) == 0

    rows = reports.models.ArticleStats.objects.filter(**constraints).values(
        'datetime', 'ad_group', 'source'
    ).annotate(
        impressions=Sum('impressions'),
        clicks=Sum('clicks'),
        cost_cc=Sum('cost_cc'),
        data_cost_cc=Sum('data_cost_cc'),
        visits=Sum('visits'),
        new_visits=Sum('new_visits'),
        bounced_visits=Sum('bounced_visits'),
        pageviews=Sum('pageviews'),
        duration=Sum('duration'),
        has_traffic_metrics=Max('has_traffic_metrics'),
        has_postclick_metrics=Max('has_postclick_metrics'),
        has_conversion_metrics=Max('has_conversion_metrics'),
    )

    ad_group_lookup = {}
    source_lookup = {}
    with transaction.atomic():
        reports.models.AdGroupStats.objects.filter(**constraints).delete()

        for row in rows:
            ad_group_id = row['ad_group']
            if ad_group_id not in ad_group_lookup:
                ad_group_lookup[ad_group_id] = dash.models.AdGroup.objects.get(pk=ad_group_id)

            source_id = row['source']
            if source_id not in source_lookup:
                source_lookup[source_id] = dash.models.Source.objects.get(pk=source_id)

            row['ad_group'] = ad_group_lookup[ad_group_id]
            row['source'] = source_lookup[source_id]

            reports.models.AdGroupStats.objects.create(**row)


def refresh_adgroup_conversion_stats(**constraints):
    # make sure we only filter by the allowed dimensions
    assert len(set(constraints.keys()) - {'datetime', 'ad_group', 'source', 'goal_name'}) == 0

    rs = reports.models.GoalConversionStats.objects.filter(**constraints).values(
        'datetime', 'ad_group', 'source', 'goal_name'
    ).annotate(
        conversions=Sum('conversions'),
        conversions_value_cc=Sum('conversions_value_cc')
    )
    ad_group_lookup = {}
    source_lookup = {}
    with transaction.atomic():
        for row in rs:
            if row['ad_group'] not in ad_group_lookup:
                ad_group_lookup[row['ad_group']] = \
                    dash.models.AdGroup.objects.get(pk=row['ad_group'])
            if row['source'] not in source_lookup:
                source_lookup[row['source']] = \
                    dash.models.Source.objects.get(pk=row['source'])
            dimensions = {
                'datetime': row['datetime'],
                'ad_group': ad_group_lookup[row['ad_group']],
                'source': source_lookup[row['source']],
                'goal_name': row['goal_name']
            }
            row['ad_group'] = ad_group_lookup[row['ad_group']]
            row['source'] = source_lookup[row['source']]
            try:
                adgroup_conversion_stats = reports.models.AdGroupGoalConversionStats.objects.get(**dimensions)
                for metric, value in row.items():
                    if metric not in ('datetime', 'ad_group', 'source', 'goal_name'):
                        adgroup_conversion_stats.__setattr__(metric, value)
            except reports.models.AdGroupGoalConversionStats.DoesNotExist:
                adgroup_conversion_stats = reports.models.AdGroupGoalConversionStats(**row)

            adgroup_conversion_stats.save()
