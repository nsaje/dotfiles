import datetime
import logging
import traceback

from django.core.mail import send_mail

import dash
from automation import autopilot_settings
import automation.helpers
from automation.constants import DailyBudgetChangeComment, CpcChangeComment
from dash import constants
import dash.models
from utils import pagerduty_helper, url_helper

logger = logging.getLogger(__name__)


def get_active_ad_groups_on_autopilot(autopilot_state=None):
    states = [autopilot_state]
    if not autopilot_state:
        states = [constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
                  constants.AdGroupSettingsAutopilotState.ACTIVE_CPC]

    ad_groups_on_autopilot = []
    ad_group_settings_on_autopilot = []
    ad_group_settings = dash.models.AdGroupSettings.objects.all().group_current_settings()\
        .select_related('ad_group')
    for ags in ad_group_settings:
        if ags.autopilot_state in states:
            ad_group = ags.ad_group
            ad_groups_sources_settings = dash.models.AdGroupSourceSettings.objects.\
                filter(ad_group_source__ad_group=ad_group).group_current_settings()
            if ad_group.get_running_status(ags, ad_groups_sources_settings) == constants.AdGroupRunningStatus.ACTIVE:
                ad_groups_on_autopilot.append(ad_group)
                ad_group_settings_on_autopilot.append(ags)
    return ad_groups_on_autopilot, ad_group_settings_on_autopilot


def ad_group_source_is_synced(ad_group_source):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=autopilot_settings.SYNC_IS_RECENT_HOURS
    )
    last_sync = ad_group_source.last_successful_sync_dt
    if last_sync is None:
        return False
    return last_sync >= min_sync_date


def update_ad_group_source_values(ad_group_source, changes):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    settings_writer.set(changes, None)


def send_autopilot_changes_emails(email_changes_data, data):
    for camp, changes_data in email_changes_data.iteritems():
        send_autopilot_changes_email(camp.name,
                                     camp.id,
                                     camp.account.name,
                                     autopilot_settings.DEBUG_EMAILS,
                                     changes_data)


def send_autopilot_changes_email(campaign_name, campaign_id, account_name, emails, changes_data):
    changesText = []
    for adgroup, adgroup_changes in changes_data.iteritems():
        changesText.append(_get_email_adgroup_text(adgroup))
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name):
            changesText.append(_get_email_source_changes_text(ag_source, adgroup_changes[ag_source]))

    body = u'''Hi account manager of {account}

On the ad groups in campaign {camp}, which are set to auto-pilot, the system made the following changes:{changes}

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
            u'Zemanta <{}>'.format(automation.autopilot_settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Auto-pilot e-mail for campaign %s to %s was not sent' +
                         'because an exception was raised:',
                         campaign_name,
                         u''.join(emails))
        desc = {
            'campaign_name': campaign_name,
            'email': ''.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_autopilot_email',
            description='Auto-pilot e-mail for campaign was not sent because an exception was raised: {}'.
                        format(traceback.format_exc(e)),
            details=desc
        )


def _get_email_adgroup_text(adgroup):
    return u'''

AdGroup: {adg_name} ({adg_url}):'''.format(
        adg_name=adgroup.name,
        adg_url=url_helper.get_full_z1_url('/ad_groups/{}/sources/'.format(adgroup.id)),
    )


def _get_email_source_changes_text(ag_source, changes):
    cpc_changed = changes['old_cpc_cc'] != changes['new_cpc_cc']
    budget_pilot_on = all(b in changes for b in ['new_budget', 'old_budget'])
    budget_changed = budget_pilot_on and changes['old_budget'] != changes['new_budget']

    text = u'\n- on {} '.format(ag_source.source.name)
    if budget_pilot_on:
        if budget_changed:
            text += u'daily budget changed from ${} to ${} and '.format(
                '{0:.2f}'.format(changes['old_budget']),
                '{0:.2f}'.format(changes['new_budget']))
        elif DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET in changes['budget_comments']:
            text += u'daily budget did not change because ' +\
                DailyBudgetChangeComment.get_text(DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET) + ' and '
        else:
            text += u'daily budget did not change and '
    if cpc_changed:
        text += u'bid CPC changed from ${} to ${}'.format(
            changes['old_cpc_cc'].normalize(),
            changes['new_cpc_cc'].normalize())
        if changes['cpc_comments']:
            text += ' because ' + ' and '.join(CpcChangeComment.get_text(c) for c in changes['cpc_comments'])
    elif changes['cpc_comments'] != []:
        text += u'bid CPC remained unchanged at ${} because {}.'.format(
            changes['old_cpc_cc'].normalize(),
            ' and '.join(CpcChangeComment.get_text(c) for c in changes['cpc_comments']))
    else:
        text += u'bid CPC remained unchanged at ${}.'.format(
            changes['old_cpc_cc'].normalize())
    return text
