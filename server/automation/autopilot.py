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
from utils import pagerduty_helper

logger = logging.getLogger(__name__)


def update_ad_group_source_cpc(ad_group_source, new_cpc):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    resource = {'cpc_cc': new_cpc}
    settings_writer.set(resource, None)


def persist_cpc_change_to_admin_log(ad_group_source, yesterday_spend, previous_cpc, new_cpc, daily_budget):
    models.AutopilotAdGroupSourceBidCpcLog(
        campaign=ad_group_source.ad_group.campaign,
        ad_group=ad_group_source.ad_group,
        ad_group_source=ad_group_source,
        yesterdays_spend_cc=yesterday_spend,
        previous_cpc_cc=previous_cpc,
        new_cpc_cc=new_cpc,
        current_daily_budget_cc=daily_budget
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
        yesterdays_spend <= 0
    ]):
        return current_cpc
    if type(current_daily_budget) != float:
        current_daily_budget = float(current_daily_budget)
    if type(yesterdays_spend) != float:
        yesterdays_spend = float(yesterdays_spend)
    if type(current_cpc) != decimal.Decimal:
        current_cpc = decimal.Decimal(current_cpc)
    spending_perc = yesterdays_spend / current_daily_budget - 1
    new_cpc = current_cpc
    for row in automation.settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if row[0] <= spending_perc <= row[1]:
            new_cpc += current_cpc * decimal.Decimal(row[2])
            new_cpc = new_cpc.quantize(
                decimal.Decimal('0.01'),
                rounding=decimal.ROUND_HALF_UP)
            break
    if (new_cpc < automation.settings.AUTOPILOT_MINIMUM_CPC or
            new_cpc > automation.settings.AUTOPILOT_MAXIMUM_CPC):
        return current_cpc
    return new_cpc


def send_autopilot_CPC_changes_email(campaign_name, campaign_id, account_name, emails, changesData):
    changesText = []
    for adg, changes in changesData.iteritems():
        changesText.append(
            u'''

AdGroup: {}:'''.format(adg)
        )
        for change in changes:
            changesText.append(
                u'''
- changed CPC bid on {} from ${} to ${}'''.format(change[0], change[1], change[2])
            )

    campaign_url = settings.BASE_URL + '/campaigns/{}/'.format(campaign_id)
    body = u'''Hi account manager of {camp}

On your campaign {camp}, {account}, which is set to auto-pilot, the system made the following changes:{changes}

Please check {camp_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=campaign_url,
        changes=''.join(changesText)
    )

    try:
        send_mail(
            'Campaign budget low - {camp}, {account}'.format(
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
