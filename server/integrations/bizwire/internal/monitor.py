import pytz
import datetime

import influx
import boto3

import backtosql
from integrations.bizwire import config
from integrations.bizwire.internal import helpers
import dash.models

from redshiftapi import db

from utils import dates_helper, email_helper


def monitoring_hourly_job():
    monitor_num_ingested_articles()
    monitor_yesterday_spend()
    monitor_duplicate_articles()
    monitor_remaining_budget()


def _get_s3_keys_for_date(s3, date):
    prefix = 'uploads/{}/{}/{}'.format(date.year, date.month, date.day)
    objects = s3.list_objects(Bucket='businesswire-articles', Prefix=prefix)

    keys = []
    while 'Contents' in objects and len(objects['Contents']) > 0:
        keys.extend(k['Key'] for k in objects['Contents'])
        objects = s3.list_objects(Bucket='businesswire-articles', Prefix=prefix, Marker=objects['Contents'][-1]['Key'])
    return keys


def monitor_num_ingested_articles():
    s3 = boto3.client('s3')

    today = dates_helper.utc_now().date()
    dates = [today - datetime.timedelta(days=x) for x in xrange(3)]

    s3_count = 0
    for date in dates:
        s3_count += len(_get_s3_keys_for_date(s3, date))

    db_count = dash.models.ContentAd.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        created_dt__gte=dates[-1],
        created_dt__lt=dates[0],
    ).count()

    influx.gauge('integrations.bizwire.article_count', s3_count, source='s3')
    influx.gauge('integrations.bizwire.article_count', db_count, source='db')


def monitor_remaining_budget():
    now = dates_helper.local_now()
    if now.hour != 0:
        return

    today = now.date()
    remaining_budget = 0
    for bli in dash.models.BudgetLineItem.objects.filter(
        campaign_id=config.AUTOMATION_CAMPAIGN,
    ).select_related('credit').filter_active(today):
        remaining_budget += bli.get_available_amount(today) * (1 - bli.credit.license_fee)

    if remaining_budget > 1000:
        return

    emails = ['luka.silovinac@zemanta.com']
    subject = 'Businesswire campaign is running out of budget'
    body = '''Hi,

Businesswire campaign is running out of budget. Configure any additional budgets: https://one.zemanta.com/campaigns/{}/budget'''.format(config.AUTOMATION_CAMPAIGN)  # noqa
    email_helper.send_notification_mail(emails, subject, body)


def monitor_yesterday_spend():
    pacific_tz = pytz.timezone('US/Pacific')
    pacific_today = helpers.get_pacific_now().date()
    pacific_midnight_today = pacific_tz.localize(
        datetime.datetime(pacific_today.year, pacific_today.month, pacific_today.day),
    )

    pacific_midnight_yesterday = pacific_midnight_today - datetime.timedelta(days=1)
    content_ad_ids = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
        created_dt__lte=pacific_midnight_today,
        created_dt__gte=pacific_midnight_yesterday,
    ).values_list('id', flat=True)

    actual_spend = db.execute_query(
        backtosql.generate_sql('bizwire_ads_stats_monitoring.sql', {
            'cost': backtosql.TemplateColumn(
                'part_sum_nano.sql',
                {'column_name': 'cost_nano'}
            ),
            'content_ad_ids': content_ad_ids,
        }),
        [],
        'bizwire_ads_stats_monitoring',
    )[0]

    expected_spend = len(content_ad_ids) * 4

    influx.gauge('integrations.bizwire.yesterday_spend', actual_spend, type='actual')
    influx.gauge('integrations.bizwire.yesterday_spend', expected_spend, type='expected')


def monitor_duplicate_articles():
    num_labels = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
    ).count()

    num_distinct = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
    ).distinct('label').count()

    influx.gauge('integrations.bizwire.labels', num_labels, type='all')
    influx.gauge('integrations.bizwire.labels', num_distinct, type='distinct')
