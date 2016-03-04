from collections import defaultdict
import unicodecsv as csv
import datetime
import dateutil.parser
import json
import logging
import re
import StringIO
import time

from django.db.models import Sum, Max
from django.db import connection, transaction
from django.conf import settings

import reports.api
import reports.models
from reports import exc
from reports.db_raw_helpers import dictfetchall
from reports import redshift
from reports import daily_statements
from utils import json_helper
from utils import s3helpers
from utils import statsd_helper
from utils import sqs_helper

import dash.models
import dash.constants

logger = logging.getLogger(__name__)

OB_RAW_PUB_DATA_S3_PREFIX = 'ob_publishers_raw/{year}/{month:02d}/{day:02d}/'
B1_RAW_PUB_DATA_S3_URI = 'b1_publishers_raw/{year}/{month:02d}/{day:02d}/part-00000'

LOAD_CONTENTADS_KEY_FMT = 'contentadstats_load/{year}/{month:02d}/{day:02d}/{campaign_id}/{ts}.json'
LOAD_B1_PUB_STATS_KEY_FMT = 'b1_publishers_load/{year}/{month:02d}/{day:02d}/{ts}.json'
LOAD_OB_PUB_STATS_KEY_FMT = 'ob_publishers_load/{year}/{month:02d}/{day:02d}/{ts}.json'
LOAD_PUB_STATS_KEY_FMT = 'publishers_load/{year}/{month:02d}/{day:02d}/{ts}.json'

CC_TO_NANO = 100000
DOLLAR_TO_NANO = 1000000000

MAX_DATES_TO_REFRESH = 200


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


def _add_effective_spend(date, campaign, rows):
    pct_actual_spend, pct_license_fee = daily_statements.get_effective_spend_pcts(date, campaign)
    for row in rows:
        row['effective_cost_nano'] = int(pct_actual_spend * (row['cost_cc'] or 0) * CC_TO_NANO)
        row['effective_data_cost_nano'] = int(pct_actual_spend * (row['data_cost_cc'] or 0) * CC_TO_NANO)
        row['license_fee_nano'] = int(pct_license_fee * (row['effective_cost_nano'] + row['effective_data_cost_nano']))


def notify_contentadstats_change(date, campaign_id):
    sqs_helper.write_message_json(
        settings.CAMPAIGN_CHANGE_QUEUE,
        {'date': date.isoformat(), 'campaign_id': campaign_id}
    )


def notify_daily_statements_change(date, campaign_id):
    sqs_helper.write_message_json(
        settings.DAILY_STATEMENTS_CHANGE_QUEUE,
        {'date': date.isoformat(), 'campaign_id': campaign_id}
    )


@statsd_helper.statsd_timer('reports.refresh', 'refresh_changed_contentadstats_timer')
def refresh_changed_contentadstats():
    messages = sqs_helper.get_all_messages(settings.CAMPAIGN_CHANGE_QUEUE)

    to_refresh = defaultdict(lambda: defaultdict(list))
    for message in messages:
        body = json.loads(message.get_body())
        key = body['campaign_id']
        to_refresh[key]['dates'].append(body['date'])
        to_refresh[key]['messages'].append(message)

    for key, val in to_refresh.iteritems():
        dates = [datetime.datetime.strptime(d, '%Y-%m-%d').date() for d in val['dates']]
        campaign = dash.models.Campaign.objects.get(id=key)

        logger.info('Refreshing changed content ad stats for campaign %s and %s date(s)', campaign.id, len(dates))
        changed_dates = daily_statements.reprocess_daily_statements(min(dates), campaign)

        for date in set(changed_dates).union(set(dates)):
            notify_daily_statements_change(date, campaign.id)

        sqs_helper.delete_messages(settings.CAMPAIGN_CHANGE_QUEUE, val['messages'])

    statsd_helper.statsd_gauge('reports.refresh.refresh_changed_contentadstats_num', len(to_refresh))


@statsd_helper.statsd_timer('reports.refresh', 'refresh_changed_daily_statements_timer')
def refresh_changed_daily_statements():
    messages = sqs_helper.get_all_messages(settings.DAILY_STATEMENTS_CHANGE_QUEUE)

    to_refresh = {}
    num_to_refresh = 0
    for message in messages:
        if num_to_refresh > MAX_DATES_TO_REFRESH:
            message.change_visibility(0)
            continue

        body = json.loads(message.get_body())
        key = (body['date'], body['campaign_id'])

        if key not in to_refresh:
            to_refresh[key] = []
            num_to_refresh += 1

        to_refresh[key].append(message)

    for key, val in to_refresh.iteritems():
        date = datetime.datetime.strptime(key[0], '%Y-%m-%d').date()
        campaign = dash.models.Campaign.objects.get(id=key[1])

        logger.info('Refreshing changed content ad stats for campaign %s and date %s', campaign.id, date)
        refresh_contentadstats(date, campaign)

        sqs_helper.delete_messages(settings.DAILY_STATEMENTS_CHANGE_QUEUE, val)

    statsd_helper.statsd_gauge('reports.refresh.refresh_changed_daily_statements_num', len(to_refresh))


def _get_s3_file_content_json(rows):
    # Redshift expects a whitespace separated list of top-level objects or arrays (each representing a row)
    # http://docs.aws.amazon.com/redshift/latest/dg/copy-parameters-data-format.html#copy-json-data-file
    return '\n'.join(json.dumps(row, cls=json_helper.DateJSONEncoder) for row in rows)


def put_contentadstats_to_s3(date, campaign, rows):
    rows_json = _get_s3_file_content_json(rows)
    s3_key = LOAD_CONTENTADS_KEY_FMT.format(
        year=date.year,
        month=date.month,
        day=date.day,
        campaign_id=campaign.id,
        ts=int(time.time()*1000)
    )
    s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS).put(s3_key, rows_json)
    return s3_key


def put_pub_stats_to_s3(date, rows, key_fmt):
    rows_json = _get_s3_file_content_json(rows)
    s3_key = key_fmt.format(
        year=date.year,
        month=date.month,
        day=date.day,
        ts=int(time.time()*1000)
    )
    s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS).put(s3_key, rows_json)
    return s3_key


def _get_b1_pub_data_s3_key(date):
    pub_data_url = B1_RAW_PUB_DATA_S3_URI.format(year=date.year, month=date.month, day=date.day)
    pub_data = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS).list(pub_data_url)
    if not pub_data:
        raise exc.S3FileNotFoundError()
    pub_data = next(iter(pub_data))
    return pub_data.name


def _extract_ob_raw_timestamp(s3_key):
    parts = s3_key.split('/')
    return int(re.sub(r'\.json$', '', parts[-1]))


def _get_latest_ob_pub_data_s3_keys(date):
    prefix_ob_pubs = OB_RAW_PUB_DATA_S3_PREFIX.format(year=date.year, month=date.month, day=date.day)

    by_ad_group = {}
    for key in s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS).list(prefix_ob_pubs):
        parts = key.name[len(prefix_ob_pubs):].split('/')
        ad_group_id = int(parts[0])
        by_ad_group.setdefault((date, ad_group_id), [])
        by_ad_group[(date, ad_group_id)].append(key.name)

    return {k: max(v, key=_extract_ob_raw_timestamp) for k, v in by_ad_group.iteritems()}


def _augment_pub_data_with_budgets(rows):
    pcts_lookup = {}
    for row in rows:
        campaign = dash.models.AdGroup.objects.select_related('campaign').get(id=row['adgroup_id']).campaign
        if (row['date'], campaign.id) not in pcts_lookup:
            pcts_lookup[(row['date'], campaign.id)] = daily_statements.get_effective_spend_pcts(row['date'], campaign)
        pct_actual_spend, pct_license_fee = pcts_lookup[(row['date'], campaign.id)]
        row['effective_cost_nano'] = int(pct_actual_spend * row['cost_nano'])
        if 'data_cost_nano' in row:
            row['effective_data_cost_nano'] = int(pct_actual_spend * row['data_cost_nano'])
        row['license_fee_nano'] = int(
            pct_license_fee * (row['effective_cost_nano'] + row.get('effective_data_cost_nano', 0)))


def _get_raw_b1_pub_data(s3_key):
    csv_data = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS).get(s3_key)
    r = csv.reader(StringIO.StringIO(csv_data))

    rows = []
    for row in r:
        rows.append({
            'date': dateutil.parser.parse(row[0]).date(),
            'adgroup_id': int(row[1]),
            'exchange': row[2],
            'domain': row[3],
            'external_id': '',
            'clicks': int(row[4]),
            'impressions': int(row[5]),
            'cost_nano': int(row[6]),
            'data_cost_nano': int(row[7]),
        })

    return rows


def _get_raw_ob_pub_data(s3_keys):
    bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

    rows = []
    for key, val in s3_keys.iteritems():
        date, ad_group_id = key
        json_data = json.loads(bucket.get(val))

        source = dash.models.Source.objects.get(source_type__type=dash.constants.SourceType.OUTBRAIN)
        ret = reports.api.get_day_cost(date, ad_group=ad_group_id, source=source)

        total_cost = 0
        if ret['cost'] is not None:
            total_cost = ret['cost']
        total_clicks = sum(row['clicks'] for row in json_data)

        for row in json_data:
            # impressions are missing because we only get clicks from outbrain
            new_row = {
                'adgroup_id': ad_group_id,
                'date': date,
                'domain': row['name'],
                'exchange': source.tracking_slug,  # code in publisher views assumes this
                'external_id': row['ob_id'],
                'clicks': row['clicks'],
                'cost_nano': 0
            }

            if total_clicks > 0:
                new_row['cost_nano'] = int(round((float(row['clicks']) / total_clicks) * total_cost * DOLLAR_TO_NANO))

            rows.append(new_row)

    return rows


def _get_latest_b1_pub_data(date):
    s3_key = _get_b1_pub_data_s3_key(date)
    return _get_raw_b1_pub_data(s3_key)


def _get_latest_ob_pub_data(date):
    s3_keys = _get_latest_ob_pub_data_s3_keys(date)
    return _get_raw_ob_pub_data(s3_keys)


def _get_latest_pub_data(date):
    ob_data = _get_latest_ob_pub_data(date)
    b1_data = _get_latest_b1_pub_data(date)
    return ob_data + b1_data


def process_publishers_stats(date):
    data = _get_latest_pub_data(date)
    _augment_pub_data_with_budgets(data)
    return put_pub_stats_to_s3(date, data, LOAD_PUB_STATS_KEY_FMT)


def refresh_publishers_data(date):
    s3_key = process_publishers_stats(date)
    with transaction.atomic(using=settings.STATS_DB_NAME):
        redshift.delete_publishers(date)
        redshift.load_publishers(s3_key)


def refresh_contentadstats(date, campaign):
    # join data
    rows = _get_joined_stats_rows(date, campaign.id)
    goals_dict = _get_goals_dict(date, campaign.id)

    _add_effective_spend(date, campaign, rows)
    rows = [_add_goals(row, goals_dict) for row in rows]
    rows = [_add_ids(row, campaign) for row in rows]
    s3_key = put_contentadstats_to_s3(date, campaign, rows)

    with transaction.atomic(using=settings.STATS_DB_NAME):
        redshift.delete_contentadstats(date, campaign.id)
        redshift.load_contentadstats(s3_key)

        redshift.delete_contentadstats_diff(date, campaign.id)
        refresh_contentadstats_diff(date, campaign)


def refresh_contentadstats_diff(date, campaign):
    adgroup_stats_batch = reports.models.AdGroupStats.objects.filter(
        datetime__contains=date,
        ad_group__campaign_id=campaign.id
    )

    diff_rows = []
    for ag_stats in adgroup_stats_batch:
        ca_stats_agg = reports.models.ContentAdStats.objects.filter(
            content_ad__ad_group=ag_stats.ad_group,
            source=ag_stats.source,
            date=ag_stats.datetime.date()
        ).aggregate(
            impressions_sum=Sum('impressions'),
            clicks_sum=Sum('clicks'),
            cost_cc_sum=Sum('cost_cc'),
            data_cost_cc_sum=Sum('data_cost_cc'),
        )

        ca_postclickstats_agg = reports.models.ContentAdPostclickStats.objects.filter(
            content_ad__ad_group=ag_stats.ad_group,
            source=ag_stats.source,
            date=ag_stats.datetime.date()
        ).aggregate(
            visits_sum=Sum('visits'),
            new_visits_sum=Sum('new_visits'),
            bounced_visits_sum=Sum('bounced_visits'),
            pageviews_sum=Sum('pageviews'),
            total_time_on_site_sum=Sum('total_time_on_site')
        )

        row = {
            'date': ag_stats.datetime.date().isoformat(),
            'content_ad_id': redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID,
            'adgroup_id': ag_stats.ad_group.id,
            'source_id': ag_stats.source.id,
            'campaign_id': ag_stats.ad_group.campaign.id,
            'account_id': ag_stats.ad_group.campaign.account.id,

            'impressions': (ag_stats.impressions or 0) - (ca_stats_agg['impressions_sum'] or 0),
            'clicks': (ag_stats.clicks or 0) - (ca_stats_agg['clicks_sum'] or 0),
            'cost_cc': (ag_stats.cost_cc or 0) - (ca_stats_agg['cost_cc_sum'] or 0),
            'data_cost_cc': (ag_stats.data_cost_cc or 0) - (ca_stats_agg['data_cost_cc_sum'] or 0),

            'visits': (ag_stats.visits or 0) - (ca_postclickstats_agg['visits_sum'] or 0),
            'new_visits': (ag_stats.new_visits or 0) - (ca_postclickstats_agg['new_visits_sum'] or 0),
            'bounced_visits': (ag_stats.bounced_visits or 0) - (ca_postclickstats_agg['bounced_visits_sum'] or 0),
            'pageviews': (ag_stats.pageviews or 0) - (ca_postclickstats_agg['pageviews_sum'] or 0),
            'total_time_on_site': (ag_stats.duration or 0) - (ca_postclickstats_agg['total_time_on_site_sum'] or 0),

            'conversions': '{}'
        }

        metric_keys = ('impressions', 'clicks', 'cost_cc', 'data_cost_cc',
                       'visits', 'new_visits', 'bounced_visits', 'pageviews', 'total_time_on_site')

        missing_keys = set(key for key in metric_keys if row[key] < 0)
        if missing_keys:
            logger.warning(
                'some ad group stats data missing. skipping those metrics in refreshing diffs. '
                'ad group id: %s source id: %s date: %s keys: %s',
                ag_stats.ad_group.id,
                ag_stats.source.id,
                date,
                missing_keys
            )

            for key in missing_keys:
                row[key] = 0

        if all(row[key] == 0 for key in metric_keys):
            continue

        for key in metric_keys:
            if row[key] > 0:
                statsd_helper.statsd_incr('reports.refresh.contentadstats_diff_{}'.format(key), row[key])

        diff_rows.append(row)

    _add_effective_spend(date, campaign, diff_rows)
    redshift.insert_contentadstats(diff_rows)


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
