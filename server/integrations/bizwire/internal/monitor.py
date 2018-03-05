import logging
import pytz
import datetime

import influx
from dateutil import rrule

import backtosql
from integrations.bizwire import config
from integrations.bizwire.internal import helpers
import dash.models

from redshiftapi import db

from utils import dates_helper, email_helper

logger = logging.getLogger(__name__)

MISSING_CLICKS_THRESHOLD = 3


def run_hourly_job():
    monitor_num_ingested_articles()
    monitor_yesterday_spend()
    monitor_yesterday_clicks()
    monitor_duplicate_articles()
    monitor_remaining_budget()


def _get_unique_s3_labels(dates):
    now = dates_helper.utc_now()

    keys = helpers.get_s3_keys_for_dates(dates)
    unique_labels = set()
    for key in keys:
        key_dt = helpers.get_s3_key_dt(key)
        if (now - key_dt).total_seconds() < 5 * 60:
            # ignore articles less than five minutes old
            continue

        unique_labels.add(helpers.get_s3_key_label(key))
    return unique_labels


def monitor_num_ingested_articles():
    start_date = dates_helper.utc_today().replace(day=1)  # beginning of month
    dates = [dt.date() for dt in rrule.rrule(rrule.DAILY, dtstart=start_date, until=dates_helper.utc_today())]
    unique_labels = _get_unique_s3_labels(dates)
    content_ad_labels = set(
        dash.models.ContentAd.objects.filter(
            ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
            label__in=unique_labels,
        ).values_list('label', flat=True)
    )

    s3_count = len(unique_labels)
    db_count = len(content_ad_labels)
    diff_count = len(unique_labels - content_ad_labels)

    influx.gauge('integrations.bizwire.article_count', s3_count, source='s3')
    influx.gauge('integrations.bizwire.article_count', db_count, source='db')
    influx.gauge('integrations.bizwire.article_count', diff_count, source='diff')


def monitor_remaining_budget():
    now = dates_helper.local_now()
    if now.hour != 0:
        return

    tomorrow = now.date() + datetime.timedelta(days=1)
    remaining_budget = 0
    for bli in dash.models.BudgetLineItem.objects.filter(
        campaign_id=config.AUTOMATION_CAMPAIGN,
    ).select_related('credit').filter_active(tomorrow):
        remaining_budget += bli.get_available_amount(tomorrow) * (1 - bli.credit.license_fee)

    if remaining_budget > 4000:
        return

    emails = config.NOTIFICATION_EMAILS
    subject = '[BIZWIRE] Campaign is running out of budget'
    body = '''Hi,

Businesswire campaign is running out of budget. Configure any additional budgets: https://one.zemanta.com/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings'''.format(config.AUTOMATION_CAMPAIGN)  # noqa
    email_helper.send_internal_email(recipient_list=emails, subject=subject, body=body)


def _get_content_ad_ids_added_yesterday():
    pacific_tz = pytz.timezone('US/Pacific')
    pacific_today = helpers.get_pacific_now().date()
    pacific_midnight_today = pacific_tz.localize(
        datetime.datetime(pacific_today.year, pacific_today.month, pacific_today.day),
    )

    pacific_midnight_yesterday = pacific_midnight_today - datetime.timedelta(days=1)
    return dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
        created_dt__lt=pacific_midnight_today,
        created_dt__gte=pacific_midnight_yesterday,
    ).exclude_archived().values_list('id', flat=True)


def monitor_yesterday_clicks():
    content_ad_ids = _get_content_ad_ids_added_yesterday()
    result = db.execute_query(
        backtosql.generate_sql('bizwire_ads_clicks_monitoring.sql', {
            'content_ad_ids': content_ad_ids,
        }),
        [],
        'bizwire_ads_clicks_monitoring',
    )

    content_ads_by_clicks = {row['content_ad_id']: row['clicks'] for row in result}
    missing_clicks = 0

    for content_ad_id in content_ad_ids:
        if content_ad_id not in content_ads_by_clicks:
            missing_clicks += 15
            continue

        missing_clicks += max(15 - content_ads_by_clicks[content_ad_id], 0)

    influx.gauge('integrations.bizwire.yesterday_missing_clicks', missing_clicks)
    _send_missing_clicks_email_alert(missing_clicks)


def monitor_yesterday_spend():
    content_ad_ids = _get_content_ad_ids_added_yesterday()
    actual_spend = 0
    if content_ad_ids:
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
        )[0]['cost'] or 0

    expected_spend = len(content_ad_ids) * config.DAILY_BUDGET_PER_ARTICLE

    influx.gauge('integrations.bizwire.yesterday_spend', actual_spend, type='actual')
    influx.gauge('integrations.bizwire.yesterday_spend', expected_spend, type='expected')
    _send_unexpected_spend_email_alert(expected_spend, actual_spend)


def monitor_duplicate_articles():
    num_labels = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
    ).count()

    num_distinct = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
    ).distinct('label').count()

    num_duplicate = abs(num_labels - num_distinct)

    influx.gauge('integrations.bizwire.labels', num_labels, type='all')
    influx.gauge('integrations.bizwire.labels', num_distinct, type='distinct')
    influx.gauge('integrations.bizwire.labels', num_duplicate, type='duplicate')

    _monitor_duplicate_articles_30d()


def _monitor_duplicate_articles_30d():
    one_month_ago = dates_helper.local_today() - datetime.timedelta(days=30)
    num_labels = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
        created_dt__gte=one_month_ago,
    ).count()

    num_distinct = dash.models.ContentAd.objects.filter(
        ad_group__campaign=config.AUTOMATION_CAMPAIGN,
        created_dt__gte=one_month_ago,
    ).distinct('label').count()

    num_duplicate = abs(num_labels - num_distinct)
    influx.gauge('integrations.bizwire.labels', num_duplicate, type='duplicate_30d')


def _send_unexpected_spend_email_alert(expected_spend, actual_spend):
    if dates_helper.utc_now().hour != 14:
        return

    if actual_spend < expected_spend:
        return

    emails = config.NOTIFICATION_EMAILS
    subject = '[BIZWIRE] Campaign unexpected yesterday spend'
    body = '''Hi,

Yesterday's expected spend was {} and actual spend was {}.'''.format(expected_spend, actual_spend)
    email_helper.send_internal_email(recipient_list=emails, subject=subject, body=body)


def _send_missing_clicks_email_alert(missing_clicks):
    if dates_helper.utc_now().hour != 14:
        return

    if missing_clicks < MISSING_CLICKS_THRESHOLD:
        return

    emails = config.NOTIFICATION_EMAILS
    subject = '[BIZWIRE] Missing yesterday clicks'
    body = '''Hi,

Missing {} clicks on content ads yesterday.'''.format(missing_clicks)
    email_helper.send_internal_email(recipient_list=emails, subject=subject, body=body)
