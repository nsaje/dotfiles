import json
import logging

from django.db.models import Sum, Max
from django.db import connection, transaction
from django.conf import settings

import reports.models
from reports.db_raw_helpers import dictfetchall
from reports import redshift
from utils.statsd_helper import statsd_incr
from utils import sqs_helper

import dash.models

logger = logging.getLogger(__name__)


def _get_joined_stats_rows(date, campaign_id):
    query_1 = '''SELECT castats.source_id, castats.content_ad_id, castats.date, castats.cost_cc,
                        castats.data_cost_cc, castats.impressions, castats.clicks,
                        ag.id AS adgroup_id
                 FROM   reports_contentadstats AS castats
                        INNER JOIN dash_contentad AS ca ON ca.id = castats.content_ad_id
                        INNER JOIN dash_adgroup AS ag ON ca.ad_group_id = ag.id
                 WHERE  date = %(date)s AND ag.campaign_id = %(campaign_id)s'''

    query_2 = '''SELECT capstats.source_id, capstats.content_ad_id, capstats.date, capstats.visits,
                        capstats.new_visits, capstats.bounced_visits, capstats.pageviews,
                        capstats.total_time_on_site, ag.id AS adgroup_id
                 FROM   reports_contentadpostclickstats AS capstats
                        INNER JOIN dash_contentad AS ca ON ca.id = capstats.content_ad_id
                        INNER JOIN dash_adgroup AS ag ON ca.ad_group_id = ag.id
                 WHERE  date = %(date)s AND ag.campaign_id = %(campaign_id)s'''

    params = {'date': date.isoformat(), 'campaign_id': campaign_id}

    with connection.cursor() as cursor:
        cursor.execute(query_1, params)
        rows_1 = dictfetchall(cursor)
        cursor.execute(query_2, params)
        rows_2 = dictfetchall(cursor)

    rows_dict = {}

    keys = {'source_id', 'content_ad_id', 'date', 'cost_cc', 'data_cost_cc', 'impressions', 'clicks', 'visits',
            'new_visits', 'bounced_visits', 'pageviews', 'total_time_on_site', 'adgroup_id'}

    for r1 in rows_1:
        key = (r1['content_ad_id'], r1['source_id'])
        rows_dict[key] = {k: r1.get(k) for k in keys}

    for r2 in rows_2:
        key = (r2['content_ad_id'], r2['source_id'])
        if key in rows_dict:
            rows_dict[key].update({k: r2.get(k) for k in keys if r2.get(k) is not None})
        else:
            rows_dict[key] = {k: r2.get(k) for k in keys}

    return rows_dict.values()


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


def _get_goals_dict(date, campaign_id):
    goals = reports.models.ContentAdGoalConversionStats.objects.filter(
        date=date,
        content_ad__ad_group__campaign_id=campaign_id,
    )

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


def _add_ids(row, campaign):
    row['campaign_id'] = campaign.id
    row['account_id'] = campaign.account_id

    return row


def _get_goals_json(goals):
    result = {}
    for goal in goals:
        key = '{}__{}'.format(goal.goal_type, goal.goal_name)
        result[key] = goal.conversions

    return json.dumps(result)


def notify_campaign_data_change(date, campaign_id):
    sqs_helper.write_message_json(
        settings.CAMPAIGN_CHANGE_QUEUE,
        {'date': date, 'campaign_id': campaign_id}
    )


def refresh_changed_campaigns_data():
    messages = sqs_helper.get_all_messages_json(settings.CAMPAIGN_CHANGE_QUEUE)
    to_refresh = set((el['date'], el['campaign_id']) for el in messages)
    for date, campaign_id in to_refresh:
        ad_groups = dash.models.AdGroup.objects.filter(campaign_id=campaign_id).exclude_archived()
        for ad_group in ad_groups:
            refresh_contentadstats(date, ad_group)


@transaction.atomic(using=settings.STATS_DB_NAME)
def refresh_contentadstats(date, campaign):
    # join data
    rows = _get_joined_stats_rows(date, campaign.id)
    goals_dict = _get_goals_dict(date, campaign.id)

    rows = [_add_goals(row, goals_dict) for row in rows]
    rows = [_add_ids(row, campaign) for row in rows]

    redshift.delete_contentadstats(date, campaign.id)
    redshift.insert_contentadstats(rows)

    redshift.delete_contentadstats_diff(date, campaign.id)
    refresh_contentadstats_diff(date, campaign)


def refresh_contentadstats_diff(date, campaign):
    logger.info('refresh_contentadstats_diff: Refreshing adgroup and contentad stats in Redshift')
    adgroup_stats_batch = reports.models.AdGroupStats.objects.filter(
        datetime__contains=date,
        ad_group__campaign_id=campaign.id
    )

    diff_rows = []
    for adgroup_stats in adgroup_stats_batch:
        # also remove and recalculate difference between adgroup stats and
        # contentadstats - this will be needed until we deprecated adgroupstats
        contentadstats_aggregate = reports.models.ContentAdStats.objects.filter(
            content_ad__ad_group=adgroup_stats.ad_group,
            source=adgroup_stats.source,
            date=adgroup_stats.datetime.date()
        ).aggregate(
            impressions_sum=Sum('impressions'),
            clicks_sum=Sum('clicks'),
            cost_cc_sum=Sum('cost_cc'),
            data_cost_cc_sum=Sum('data_cost_cc'),
        )

        contentad_postclickstats_aggregate = reports.models.ContentAdPostclickStats.objects.filter(
            content_ad__ad_group=adgroup_stats.ad_group,
            source=adgroup_stats.source,
            date=adgroup_stats.datetime.date()
        ).aggregate(
            visits_sum=Sum('visits'),
            new_visits_sum=Sum('new_visits'),
            bounced_visits_sum=Sum('bounced_visits'),
            pageviews_sum=Sum('pageviews'),
            total_time_on_site_sum=Sum('total_time_on_site')
        )

        row = {
            'date': adgroup_stats.datetime.date().isoformat(),
            'content_ad_id': redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID,
            'adgroup_id': adgroup_stats.ad_group.id,
            'source_id': adgroup_stats.source.id,
            'campaign_id': adgroup_stats.ad_group.campaign.id,
            'account_id': adgroup_stats.ad_group.campaign.account.id,

            'impressions': (adgroup_stats.impressions or 0) - (contentadstats_aggregate['impressions_sum'] or 0),
            'clicks': (adgroup_stats.clicks or 0) - (contentadstats_aggregate['clicks_sum'] or 0),
            'cost_cc': (adgroup_stats.cost_cc or 0) - (contentadstats_aggregate['cost_cc_sum'] or 0),
            'data_cost_cc': (adgroup_stats.data_cost_cc or 0) - (contentadstats_aggregate['data_cost_cc_sum'] or 0),

            'visits': (adgroup_stats.visits or 0) - (contentad_postclickstats_aggregate['visits_sum'] or 0),
            'new_visits': (adgroup_stats.new_visits or 0) - (contentad_postclickstats_aggregate['new_visits_sum'] or 0),
            'bounced_visits': (adgroup_stats.bounced_visits or 0) - (contentad_postclickstats_aggregate['bounced_visits_sum'] or 0),
            'pageviews': (adgroup_stats.pageviews or 0) - (contentad_postclickstats_aggregate['pageviews_sum'] or 0),
            'total_time_on_site': (adgroup_stats.duration or 0) - (contentad_postclickstats_aggregate['total_time_on_site_sum'] or 0),

            'conversions': '{}'
        }

        metric_keys = ('impressions', 'clicks', 'cost_cc', 'data_cost_cc',
                       'visits', 'new_visits', 'bounced_visits', 'pageviews', 'total_time_on_site')

        if all(row[key] == 0 for key in metric_keys):
            continue

        for key in metric_keys:
            if row[key] > 0:
                statsd_incr('reports.refresh.contentadstats_diff_{}'.format(row[key]), row[key])

        diff_rows.append(row)

    if diff_rows != []:
        redshift.insert_contentadstats(diff_rows)
        logger.info('refresh_contentadstats_diff: Inserted {count} diff rows into redshift'.format(count=len(diff_rows)))


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

