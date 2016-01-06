import datetime
import pytz
import decimal
import traceback
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

import dash
from automation import models
import automation.helpers
import automation.settings
import automation.constants
from dash import constants
import reports
from utils import pagerduty_helper, url_helper
from utils.statsd_helper import statsd_timer
from utils.statsd_helper import statsd_gauge

logger = logging.getLogger(__name__)


def update_ad_group_source_cpc(ad_group_source, new_cpc):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    resource = {'cpc_cc': new_cpc}
    settings_writer.set(resource, None)


def persist_cpc_change_to_admin_log(
        ad_group_source,
        yesterday_spend,
        previous_cpc,
        new_cpc,
        daily_budget,
        yesterday_clicks,
        comments):
    models.AutopilotAdGroupSourceBidCpcLog(
        campaign=ad_group_source.ad_group.campaign,
        ad_group=ad_group_source.ad_group,
        ad_group_source=ad_group_source,
        yesterdays_spend_cc=yesterday_spend,
        previous_cpc_cc=previous_cpc,
        new_cpc_cc=new_cpc,
        current_daily_budget_cc=daily_budget,
        yesterdays_clicks=yesterday_clicks,
        comments=', '.join(automation.constants.CpcChangeComment.get_text(comment) for comment in comments)
    ).save()


def ad_group_sources_daily_budget_was_changed_recently(ad_group_source):
    now_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    now = now_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    yesterday = datetime.datetime(now.year, now.month, now.day) - datetime.timedelta(days=1)
    try:
        current_budget = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source
            ).latest('created_dt').daily_budget_cc
        budget_before_yesterday_midnight = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source
            ).filter(
            created_dt__lte=yesterday,
            ).latest('created_dt').daily_budget_cc
    except ObjectDoesNotExist:
        return True

    if current_budget != budget_before_yesterday_midnight:
        return True

    source_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source=ad_group_source,
        created_dt__gte=yesterday,
        created_dt__lte=now
        )
    for setting in source_settings:
        if setting.daily_budget_cc != current_budget:
            return True
    return False


def get_autopilot_ad_group_sources_settings(adgroup):
    autopilot_sources_settings = []
    for current_source_settings in automation.helpers.get_active_ad_group_sources_settings(adgroup):
        if current_source_settings.autopilot_state != dash.constants.AdGroupSourceSettingsAutopilotState.ACTIVE:
            continue
        autopilot_sources_settings.append(current_source_settings)
        if current_source_settings.cpc_cc is not None and current_source_settings.daily_budget_cc is not None:
            continue
        source_state = automation.helpers.get_latest_ad_group_source_state(current_source_settings.ad_group_source)
        if current_source_settings.cpc_cc is None and source_state is not None and source_state.cpc_cc is not None:
            current_source_settings.cpc_cc = source_state.cpc_cc
        if current_source_settings.daily_budget_cc is None and source_state is not None and source_state.daily_budget_cc is not None:
            current_source_settings.daily_budget_cc = source_state.daily_budget_cc
    return autopilot_sources_settings


def ad_group_source_is_on_autopilot(ad_group_source):
    setting = ad_group_source.get_current_settings_or_none()
    if setting is None:
        return False
    return setting.autopilot_state == constants.AdGroupSourceSettingsAutopilotState.ACTIVE


def _ad_group_source_is_synced(ad_group_source):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=automation.settings.SYNC_IS_RECENT_HOURS
    )
    last_sync = ad_group_source.last_successful_sync_dt
    if last_sync is None:
        return False
    return last_sync >= min_sync_date


def calculate_new_autopilot_cpc(current_cpc, current_daily_budget, yesterdays_spend):
    cpc_change_comments = _get_calculate_cpc_comments(current_cpc, current_daily_budget, yesterdays_spend)
    spending_perc = _calculate_spending_perc(yesterdays_spend, current_daily_budget)
    if spending_perc is not None and spending_perc > automation.settings.AUTOPILOT_MAX_ALLOWED_SPENDING:
        cpc_change_comments.append(automation.constants.CpcChangeComment.HIGH_OVERSPEND)

    if cpc_change_comments:
        return (current_cpc, cpc_change_comments)

    new_cpc = current_cpc
    for change_interval in automation.settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if change_interval['underspend_upper_limit'] <= spending_perc <= change_interval['underspend_lower_limit']:
            new_cpc += current_cpc * change_interval['bid_cpc_procentual_increase']
            if change_interval['bid_cpc_procentual_increase'] == decimal.Decimal('0'):
                return (current_cpc, [automation.constants.CpcChangeComment.OPTIMAL_SPEND])
            if change_interval['bid_cpc_procentual_increase'] < 0:
                new_cpc = _threshold_reducing_cpc(current_cpc, new_cpc)
            else:
                new_cpc = _threshold_increasing_cpc(current_cpc, new_cpc)
            new_cpc = _round_cpc(new_cpc)
            break
    if automation.settings.AUTOPILOT_MIN_CPC > new_cpc:
        return (automation.settings.AUTOPILOT_MIN_CPC, cpc_change_comments)
    if automation.settings.AUTOPILOT_MAX_CPC < new_cpc:
        return (automation.settings.AUTOPILOT_MAX_CPC, cpc_change_comments)
    return (new_cpc, cpc_change_comments)


def _get_calculate_cpc_comments(current_cpc, current_daily_budget, yesterdays_spend):
    cpc_change_comments = []
    if current_daily_budget is None or current_daily_budget <= 0:
        cpc_change_comments.append(automation.constants.CpcChangeComment.BUDGET_NOT_SET)
    if yesterdays_spend is None or yesterdays_spend <= 0:
        cpc_change_comments.append(automation.constants.CpcChangeComment.NO_YESTERDAY_SPEND)
    if current_cpc is None or current_cpc <= 0:
        cpc_change_comments.append(automation.constants.CpcChangeComment.CPC_NOT_SET)
    if current_cpc > automation.settings.AUTOPILOT_MAX_CPC:
        cpc_change_comments.append(automation.constants.CpcChangeComment.CURRENT_CPC_TOO_HIGH)
    if current_cpc < automation.settings.AUTOPILOT_MIN_CPC:
        cpc_change_comments.append(automation.constants.CpcChangeComment.CURRENT_CPC_TOO_LOW)
    return cpc_change_comments


def _calculate_spending_perc(yesterdays_spend, current_daily_budget):
    if not isinstance(yesterdays_spend, decimal.Decimal) and yesterdays_spend is not None:
        yesterdays_spend = decimal.Decimal(yesterdays_spend)
    if current_daily_budget is not None and yesterdays_spend is not None and current_daily_budget > 0:
        return yesterdays_spend / current_daily_budget - 1
    return None


def _threshold_reducing_cpc(current_cpc, new_cpc):
    cpc_change = abs(current_cpc - new_cpc)
    if cpc_change < automation.settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE:
        return current_cpc - automation.settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE
    if cpc_change > automation.settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE:
        return current_cpc - automation.settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE
    return new_cpc


def _threshold_increasing_cpc(current_cpc, new_cpc):
    cpc_change = abs(current_cpc - new_cpc)
    if cpc_change < automation.settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE:
        return current_cpc + automation.settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE
    if cpc_change > automation.settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE:
        return current_cpc + automation.settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE
    return new_cpc


def _check_source_constraints(proposed_cpc, source_min_cpc, source_max_cpc):
    if proposed_cpc > source_max_cpc:
        return [automation.constants.CpcChangeComment.OVER_SOURCE_MAX_CPC]
    if proposed_cpc < source_min_cpc:
        return [automation.constants.CpcChangeComment.UNDER_SOURCE_MIN_CPC]
    return []


def _round_cpc(num):
    return num.quantize(
        decimal.Decimal('0.01'),
        rounding=decimal.ROUND_UP)


def send_autopilot_CPC_changes_email(campaign_name, campaign_id, account_name, emails, changes_data):
    changesText = []
    for adgroup, source_changes in changes_data.iteritems():
        changesText.append(_get_email_adgroup_text(adgroup))
        source_changes.sort(key=lambda k: k['source_name'])
        for change in source_changes:
            changesText.append(_get_email_source_changes_text(change))

    body = u'''Hi account manager of {camp}

On your campaign {camp}, {account}, which is set to auto-pilot, the system made the following changes:{changes}

Please check {camp_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=url_helper.get_full_z1_url('/campaigns/{}/'.format(campaign_id)),
        changes=''.join(changesText)
    )
    try:
        send_mail(
            u'Campaign Auto-Pilot Changes - {camp}, {account}'.format(
                camp=campaign_name,
                account=account_name
            ),
            body,
            u'Zemanta <{}>'.format(automation.settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Auto-pilot bid CPC e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign_name,
                         u''.join(emails))
        desc = {
            'campaign_name': campaign_name,
            'email': ''.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_bid_cpc_autopilot_email',
            description='Auto-pilot bid CPC e-mail for campaign was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc
        )


def _get_email_adgroup_text(adgroup):
    return u'''

AdGroup: {adg_name} ({adg_url}):'''.format(
        adg_name=adgroup[0],
        adg_url=url_helper.get_full_z1_url('/ad_groups/{}/sources/'.format(adgroup[1])),
    )


def _get_email_source_changes_text(change):
    if change['comments'] == []:
        return u'''
- changed CPC bid on {} from ${} to ${}'''.format(
            change['source_name'],
            change['old_cpc'].normalize(),
            change['new_cpc'].normalize())
    return u'''
- no changes on {} because {}'''.format(
        change['source_name'],
        ' and '.join(automation.constants.CpcChangeComment.get_text(comment) for comment in change['comments']))


@statsd_timer('automation.autopilot', 'adjust_autopilot_media_sources_bid_cpcs')
def adjust_autopilot_media_sources_bid_cpcs():
    changes = {}
    for adgroup in automation.helpers.get_all_active_ad_groups():

        yesterday_spends = reports.api.get_yesterday_cost(ad_group=adgroup)
        for ad_group_source_settings in get_autopilot_ad_group_sources_settings(adgroup):
            cpc_change_comments = []

            if ad_group_sources_daily_budget_was_changed_recently(ad_group_source_settings.ad_group_source):
                cpc_change_comments.append(automation.constants.CpcChangeComment.BUDGET_MANUALLY_CHANGED)

            if not _ad_group_source_is_synced(ad_group_source_settings.ad_group_source):
                cpc_change_comments.append(automation.constants.CpcChangeComment.OLD_DATA)

            yesterday_spend = yesterday_spends.get(ad_group_source_settings.ad_group_source.source_id)

            proposed_cpc, calculation_comments = calculate_new_autopilot_cpc(
                ad_group_source_settings.cpc_cc,
                ad_group_source_settings.daily_budget_cc,
                yesterday_spend)
            cpc_change_comments += calculation_comments
            cpc_change_comments += _check_source_constraints(
                proposed_cpc,
                ad_group_source_settings.ad_group_source.source.source_type.min_cpc,
                ad_group_source_settings.ad_group_source.source.source_type.max_cpc)
            new_cpc = proposed_cpc if cpc_change_comments == [] else ad_group_source_settings.cpc_cc
            persist_cpc_change_to_admin_log(
                ad_group_source_settings.ad_group_source,
                yesterday_spend,
                ad_group_source_settings.cpc_cc,
                new_cpc,
                ad_group_source_settings.daily_budget_cc,
                automation.helpers.get_yesterdays_clicks(ad_group_source_settings.ad_group_source),
                cpc_change_comments
            )

            if adgroup.campaign not in changes:
                changes[adgroup.campaign] = {}
            if (adgroup.name, adgroup.id) not in changes[adgroup.campaign]:
                changes[adgroup.campaign][(adgroup.name, adgroup.id)] = []
            changes[adgroup.campaign][(adgroup.name, adgroup.id)].append({
                'source_name': ad_group_source_settings.ad_group_source.source.name,
                'old_cpc': ad_group_source_settings.cpc_cc,
                'new_cpc': new_cpc,
                'comments': cpc_change_comments
            })

            if ad_group_source_settings.cpc_cc != proposed_cpc and cpc_change_comments == []:
                update_ad_group_source_cpc(
                    ad_group_source_settings.ad_group_source,
                    proposed_cpc
                )

    for camp, adgroup_changes in changes.iteritems():
        send_autopilot_CPC_changes_email(
            camp.name,
            camp.id,
            camp.account.name,
            [camp.get_current_settings().campaign_manager.email],
            adgroup_changes
        )
    report_autopilot_metrics()


def report_autopilot_metrics():
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today_min = datetime.datetime.combine(today, datetime.time.min)
    today_max = datetime.datetime.combine(today, datetime.time.max)

    _report_trends_metrics(today_min, today_max)
    _report_cpc_autopilot_log_sources_count_metrics(today_min, today_max)


def _report_cpc_autopilot_log_sources_count_metrics(today_min, today_max):
    sources_on_autopilot_logs_count = automation.models.AutopilotAdGroupSourceBidCpcLog.objects.filter(
        created_dt__range=(today_min, today_max)).values('ad_group_source_id').distinct().count()
    statsd_gauge('automation.autopilot.cpc_autopilot_log_sources_count', sources_on_autopilot_logs_count)


def _report_trends_metrics(today_min, today_max):
    todays_changed_cpc_logs = automation.models.AutopilotAdGroupSourceBidCpcLog.objects.filter(
        created_dt__range=(today_min, today_max), comments='')
    yesterdays_changed_cpc_logs = automation.models.AutopilotAdGroupSourceBidCpcLog.objects.filter(
        created_dt__range=(today_min - datetime.timedelta(days=1), today_max - datetime.timedelta(days=1)),
        ad_group_source_id__in=todays_changed_cpc_logs.values('ad_group_source_id').distinct(),
        comments='')
    _report_spend_trends(todays_changed_cpc_logs, yesterdays_changed_cpc_logs)
    _report_clicks_trends(todays_changed_cpc_logs, yesterdays_changed_cpc_logs)


def _report_spend_trends(todays_changed_cpc_logs, yesterdays_changed_cpc_logs):
    spend_trends = []
    for source in yesterdays_changed_cpc_logs.values('ad_group_source_id').distinct().values_list('ad_group_source_id'):
        yesterdays = yesterdays_changed_cpc_logs.filter(ad_group_source=source).latest('created_dt')
        todays = todays_changed_cpc_logs.filter(ad_group_source=source).latest('created_dt')
        if yesterdays.current_daily_budget_cc <= 0 or todays.current_daily_budget_cc <= 0:
            continue
        yesterdays_spend = (yesterdays.yesterdays_spend_cc / yesterdays.current_daily_budget_cc) - 1
        todays_spend = (todays.yesterdays_spend_cc / todays.current_daily_budget_cc) - 1
        spend_trends.append(
            abs(automation.settings.AUTOPILOT_OPTIMAL_SPEND-yesterdays_spend) - abs(automation.settings.AUTOPILOT_OPTIMAL_SPEND-todays_spend)
        )

    if len(spend_trends) > 0:
        statsd_gauge('automation.autopilot.avg_trend_of_spend_towards_optimal_spend',
                     sum(spend_trends) / decimal.Decimal(len(spend_trends)))
        statsd_gauge('automation.autopilot.perc_of_improved_spends',
                     sum([1 for spend in spend_trends if spend > decimal.Decimal('0')]) / float(len(spend_trends)))


def _report_clicks_trends(todays_changed_cpc_logs, yesterdays_changed_cpc_logs):
    click_increases = []
    for source in yesterdays_changed_cpc_logs.values('ad_group_source_id').distinct().values_list('ad_group_source_id'):
        yesterdays = yesterdays_changed_cpc_logs.filter(ad_group_source=source).latest('created_dt')
        todays = todays_changed_cpc_logs.filter(ad_group_source=source).latest('created_dt')
        if yesterdays.yesterdays_clicks <= 0 or todays.yesterdays_clicks <= 0:
            continue
        click_increases.append(todays.yesterdays_clicks / float(yesterdays.yesterdays_clicks) - 1)

    if len(click_increases) > 0:
        statsd_gauge('automation.autopilot.avg_proc_increase_in_clicks',
                     sum(click_increases) / float(len(click_increases)))
        statsd_gauge('automation.autopilot.perc_of_increased_clicks',
                     sum([1 for clicks in click_increases if clicks > 0]) / float(len(click_increases)))
