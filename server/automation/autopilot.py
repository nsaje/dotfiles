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
from dash import constants
import reports
from utils import pagerduty_helper

logger = logging.getLogger(__name__)


def update_ad_group_source_cpc(ad_group_source, new_cpc):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    resource = {'cpc_cc': new_cpc}
    settings_writer.set(resource, None)


def persist_cpc_change_to_admin_log(ad_group_source, yesterday_spend, previous_cpc, new_cpc, daily_budget, yesterday_clicks):
    models.AutopilotAdGroupSourceBidCpcLog(
        campaign=ad_group_source.ad_group.campaign,
        ad_group=ad_group_source.ad_group,
        ad_group_source=ad_group_source,
        yesterdays_spend_cc=yesterday_spend,
        previous_cpc_cc=previous_cpc,
        new_cpc_cc=new_cpc,
        current_daily_budget_cc=daily_budget,
        yesterdays_clicks=yesterday_clicks
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
        if (current_source_settings.autopilot_state == dash.constants.AdGroupSourceSettingsAutopilotState.ACTIVE):
            autopilot_sources_settings.append(current_source_settings)
    return autopilot_sources_settings


def ad_group_source_is_on_autopilot(ad_group_source):
    setting = dash.views.helpers.get_ad_group_source_settings(ad_group_source)
    if setting is None:
        return False
    return setting.autopilot_state == constants.AdGroupSourceSettingsAutopilotState.ACTIVE


def calculate_new_autopilot_cpc(current_cpc, current_daily_budget, yesterdays_spend):
    if current_cpc < 0:
        return decimal.Decimal(0)
    if any([
        current_daily_budget is None,
        yesterdays_spend is None,
        current_cpc is None,
        current_daily_budget <= 0,
        yesterdays_spend <= 0,
        current_cpc > automation.settings.AUTOPILOT_MAX_CPC,
        current_cpc < automation.settings.AUTOPILOT_MIN_CPC
    ]):
        return current_cpc
    assert isinstance(current_daily_budget, decimal.Decimal)
    assert isinstance(yesterdays_spend, decimal.Decimal)
    assert isinstance(current_cpc, decimal.Decimal)
    spending_perc = yesterdays_spend / current_daily_budget - 1
    new_cpc = current_cpc
    for row in automation.settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if row['underspend_upper_limit'] <= spending_perc <= row['underspend_lower_limit']:
            new_cpc += current_cpc * decimal.Decimal(row['bid_cpc_procentual_increase'])
            if row['bid_cpc_procentual_increase'] < 0:
                new_cpc = _threshold_lowering_cpc(current_cpc, new_cpc)
            new_cpc = _round_cpc(new_cpc)
            break
    if automation.settings.AUTOPILOT_MIN_CPC > new_cpc:
        return automation.settings.AUTOPILOT_MIN_CPC
    if automation.settings.AUTOPILOT_MAX_CPC < new_cpc:
        return automation.settings.AUTOPILOT_MAX_CPC
    return new_cpc


def _threshold_lowering_cpc(current_cpc, new_cpc):
    if abs(current_cpc - new_cpc) < automation.settings.AUTOPILOT_MIN_LOWERING_CPC_CHANGE:
        return current_cpc - automation.settings.AUTOPILOT_MIN_LOWERING_CPC_CHANGE
    if abs(current_cpc - new_cpc) > automation.settings.AUTOPILOT_MAX_LOWERING_CPC_CHANGE:
        return current_cpc - automation.settings.AUTOPILOT_MAX_LOWERING_CPC_CHANGE
    return new_cpc


def _round_cpc(num):
    return num.quantize(
        decimal.Decimal('0.01'),
        rounding=decimal.ROUND_HALF_UP)


def send_autopilot_CPC_changes_email(campaign_name, campaign_id, account_name, emails, changesData):
    changesText = []
    for adg, changes in changesData.iteritems():
        changesText.append(
            u'''

AdGroup: {adg_name} ({adg_url}):'''.format(
                adg_name=adg[0],
                adg_url=settings.BASE_URL + '/ad_groups/{}/sources/'.format(adg[1])
                )
        )
        for change in changes:
            changesText.append(
                u'''
- changed CPC bid on {} from ${} to ${}'''.format(change['source_name'], change['old_cpc'], change['new_cpc'])
            )

    body = u'''Hi account manager of {camp}

On your campaign {camp}, {account}, which is set to auto-pilot, the system made the following changes:{changes}

Please check {camp_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=settings.BASE_URL + '/campaigns/{}/'.format(campaign_id),
        changes=''.join(changesText)
    )
    try:
        send_mail(
            'Campaign Auto-Pilot Changes - {camp}, {account}'.format(
                camp=campaign_name,
                account=account_name
            ),
            body,
            'Zemanta <{}>'.format(automation.settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception('Auto-pilot bid CPC e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign_name,
                         ''.join(emails))
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


def adjust_autopilot_media_sources_bid_cpcs():
    changes = {}
    for adg in automation.helpers.get_all_active_ad_groups():

        yesterday_spends = reports.api.get_yesterday_cost(ad_group=adg)
        for ad_group_source_settings in get_autopilot_ad_group_sources_settings(adg):
            if ad_group_sources_daily_budget_was_changed_recently(ad_group_source_settings.ad_group_source):
                continue

            yesterday_spend = yesterday_spends.get(ad_group_source_settings.ad_group_source.source_id)

            proposed_cpc = calculate_new_autopilot_cpc(
                ad_group_source_settings.cpc_cc,
                ad_group_source_settings.daily_budget_cc,
                yesterday_spend
            )

            if ad_group_source_settings.cpc_cc == proposed_cpc:
                continue

            persist_cpc_change_to_admin_log(
                ad_group_source_settings.ad_group_source,
                yesterday_spend,
                ad_group_source_settings.cpc_cc,
                proposed_cpc,
                ad_group_source_settings.daily_budget_cc,
                automation.helpers.get_yesterdays_clicks(ad_group_source_settings.ad_group_source)
            )

            update_ad_group_source_cpc(
                ad_group_source_settings.ad_group_source,
                proposed_cpc
            )

            if adg.campaign not in changes:
                changes[adg.campaign] = {}
            if (adg.name, adg.id) not in changes[adg.campaign]:
                changes[adg.campaign][(adg.name, adg.id)] = []
            changes[adg.campaign][(adg.name, adg.id)].append({
                'source_name': ad_group_source_settings.ad_group_source.source.name,
                'old_cpc': ad_group_source_settings.cpc_cc,
                'new_cpc': proposed_cpc
            })

    for camp, adgroup_changes in changes.iteritems():
        send_autopilot_CPC_changes_email(
            camp.name,
            camp.id,
            camp.account.name,
            [camp.get_current_settings().account_manager.email],
            adgroup_changes
        )
