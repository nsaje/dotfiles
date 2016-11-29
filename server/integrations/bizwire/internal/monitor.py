import logging
import pytz
import datetime
import re

import influx
import boto3

import backtosql
from integrations.bizwire import config
from integrations.bizwire.internal import helpers
import dash.models

from redshiftapi import db

from utils import dates_helper, email_helper

logger = logging.getLogger(__name__)


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

    now = dates_helper.utc_now()
    dates = [now.date() - datetime.timedelta(days=x) for x in xrange(3)]

    re_compiled = re.compile(r'.*{}/{}/{}/(\d+)(:|%3[aA]).*'.format(now.year, now.month, now.day))
    unique_ids = set()
    for date in dates:
        for key in _get_s3_keys_for_date(s3, date):
            m = re_compiled.match(key)
            hour = m.groups()[0]
            if hour == now.hour:
                continue

            article_id = m.groups()[1]  # take care of article revisions
            unique_ids.add(article_id)

    s3_count = len(unique_ids)
    db_count = dash.models.ContentAd.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        created_dt__gte=dates[-1],
        created_dt__lt=datetime.datetime(
            dates[0].year, dates[0].month, dates[0].day, now.hour),  # don't count articles from this hour
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

    emails = config.NOTIFICATION_EMAILS
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
        created_dt__lt=pacific_midnight_today,
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
    )[0]['cost']

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
