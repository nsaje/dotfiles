import datetime
import logging
import traceback
import textwrap

from django.core.mail import send_mail

import dash
from dash.constants import AdGroupSettingsState
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
    campaigns_in_landing = set(
        dash.models.CampaignSettings.objects.all().filter(
            id__in=dash.models.CampaignSettings.objects.all().group_current_settings(),
            landing_mode=True).values_list('campaign_id', flat=True)
    )

    for ags in ad_group_settings:
        if ags.autopilot_state in states:
            ad_group = ags.ad_group
            ad_groups_sources_settings = dash.models.AdGroupSourceSettings.objects.\
                filter(ad_group_source__ad_group=ad_group).group_current_settings()

            if ad_group.campaign_id in campaigns_in_landing:
                continue

            if ad_group.get_running_status(ags, ad_groups_sources_settings) == constants.AdGroupRunningStatus.ACTIVE:
                ad_groups_on_autopilot.append(ad_group)
                ad_group_settings_on_autopilot.append(ags)
    return ad_groups_on_autopilot, ad_group_settings_on_autopilot


def get_autopilot_active_sources_settings(ad_groups, ad_group_setting_state=AdGroupSettingsState.ACTIVE):
    ag_sources = dash.views.helpers.get_active_ad_group_sources(dash.models.AdGroup, ad_groups)
    ag_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source_id__in=ag_sources).\
        group_current_settings().select_related('ad_group_source__source__source_type')
    if ad_group_setting_state:
        return [ag_source_setting for ag_source_setting in ag_sources_settings if
                ag_source_setting.state == ad_group_setting_state]
    return ag_sources_settings


def ad_group_source_is_synced(ad_group_source):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=autopilot_settings.SYNC_IS_RECENT_HOURS
    )
    last_sync = ad_group_source.last_successful_sync_dt
    if last_sync is None:
        return False
    return last_sync >= min_sync_date


def update_ad_group_source_values(ad_group_source, changes, system_user=None, landing_mode=None):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    return settings_writer.set(changes, None, system_user=system_user, landing_mode=landing_mode, send_to_zwei=False)


def get_ad_group_sources_minimum_cpc(ad_group_source):
    return max(autopilot_settings.AUTOPILOT_MIN_CPC, ad_group_source.source.source_type.min_cpc)


def get_ad_group_sources_minimum_daily_budget(ad_group_source,
                                              ap_type=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET):
    source_min_daily_budget = ad_group_source.source.source_type.min_daily_budget
    if ap_type != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return source_min_daily_budget
    return max(autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET, source_min_daily_budget)


def get_campaign_goal_column(campaign_goal):
    return autopilot_settings.GOALS_COLUMNS.get(campaign_goal.type).get('col')[0] if campaign_goal else None


def get_campaign_goal_column_importance(campaign_goal):
    return autopilot_settings.GOALS_COLUMNS.get(campaign_goal.type).get('col')[1] if campaign_goal else None


def send_autopilot_changes_emails(email_changes_data, data, initialization):
    for camp, changes_data in email_changes_data.iteritems():
        campaign_manager = camp.get_current_settings().campaign_manager
        account_manager = camp.account.get_current_settings().default_account_manager
        email_address = [account_manager.email] + ([campaign_manager.email] if campaign_manager and
                                                   account_manager.email != campaign_manager.email else [])
        if initialization:
            send_budget_autopilot_initialisation_email(
                camp.name,
                camp.id,
                camp.account.name,
                [email_address],
                changes_data)
        else:
            send_autopilot_changes_email(camp.name,
                                         camp.id,
                                         camp.account.name,
                                         email_address,
                                         changes_data)


def send_autopilot_changes_email(campaign_name, campaign_id, account_name, emails, changes_data):
    changesText = []
    for adgroup, adgroup_changes in changes_data.iteritems():
        changesText.append(_get_email_adgroup_text(adgroup))
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name.lower()):
            changesText.append(_get_email_source_changes_text(ag_source, adgroup_changes[ag_source]))

    body = textwrap.dedent(u'''\
    Hi account manager of {account}

    On the ad groups in campaign {camp}, which are set to autopilot, the system made the following changes:{changes}

    Please check {camp_url} for details.

    Yours truly,
    Zemanta
    ''')
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=url_helper.get_full_z1_url('/campaigns/{}/'.format(campaign_id)),
        changes=''.join(changesText)
    )
    try:
        send_mail(
            u'Campaign Autopilot Changes - {camp}, {account}'.format(
                camp=campaign_name,
                account=account_name
            ),
            body,
            u'Zemanta <{}>'.format(automation.autopilot_settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Autopilot e-mail for campaign %s to %s was not sent' +
                         'because an exception was raised:',
                         campaign_name,
                         u', '.join(emails))
        desc = {
            'campaign_name': campaign_name,
            'email': ', '.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_autopilot_email',
            description=u'Autopilot e-mail for campaign was not sent because an exception was raised: {}'.
                        format(traceback.format_exc(e)),
            details=desc
        )


def send_budget_autopilot_initialisation_email(campaign_name, campaign_id, account_name, emails, changes_data):
    changesText = []
    for adgroup, adgroup_changes in changes_data.iteritems():
        changesText.append(_get_email_adgroup_text(adgroup))
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name.lower()):
            changesText.append(_get_email_source_changes_text(ag_source, adgroup_changes[ag_source]))

    body = textwrap.dedent(u'''\
    Hi account manager of {account}

    Bid CPC and Daily Budgets Optimising Autopilot's settings on Your ad group in campaign {camp} have been changed.
    Autopilot made the following changes:{changes}
    - all Paused Media Sources\' Daily Budgets have been set to minimum values.

    Please check {camp_url} for details.

    Yours truly,
    Zemanta
    ''')
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=url_helper.get_full_z1_url('/campaigns/{}/'.format(campaign_id)),
        changes=''.join(changesText)
    )
    try:
        send_mail(
            u'Ad Group put on Bid CPC and Daily Budgets Optimising Autopilot - {account}'.format(
                account=account_name
            ),
            body,
            u'Zemanta <{}>'.format(automation.autopilot_settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Autopilot e-mail for initialising budget autopilot on an adroup in ' +
                         'campaign %s to %s was not sent because an exception was raised:',
                         campaign_name,
                         u', '.join(emails))
        desc = {
            'campaign_name': campaign_name,
            'email': ', '.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_autopilot_budget_initialisation_email',
            description=u'Autopilot e-mail for initialising budget autopilot on an adroup in ' +
                         'campaign was not sent because an exception was raised: {}'.
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
    cpc_pilot_on = all(c in changes for c in ['old_cpc_cc', 'new_cpc_cc'])
    cpc_changed = cpc_pilot_on and changes['old_cpc_cc'] != changes['new_cpc_cc']
    budget_pilot_on = all(b in changes for b in ['new_budget', 'old_budget'])
    budget_changed = budget_pilot_on and changes['old_budget'] != changes['new_budget']

    text = u'\n- on {} '.format(ag_source.source.name)
    if budget_pilot_on:
        text += _get_budget_changes_text(budget_changed, changes)
        text += u' and ' if cpc_pilot_on else u''
    if cpc_pilot_on:
        text += _get_cpc_changes_text(cpc_changed, changes)
    return text


def _get_budget_changes_text(budget_changed, changes):
    if budget_changed:
        return u'daily budget changed from ${} to ${}'.format(
            '{0:.2f}'.format(changes['old_budget']),
            '{0:.2f}'.format(changes['new_budget']))
    elif DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET in changes['budget_comments']:
        return u'daily budget did not change because ' +\
            DailyBudgetChangeComment.get_text(DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET)
    else:
        return u'daily budget did not change'


def _get_cpc_changes_text(cpc_changed, changes):
    if cpc_changed:
        text = u'bid CPC changed from ${} to ${}'.format(
            changes['old_cpc_cc'].normalize(),
            changes['new_cpc_cc'].normalize())
        if changes['cpc_comments']:
            text += u' because ' + u' and '.join(CpcChangeComment.get_text(c) for c in changes['cpc_comments'])
        return text
    elif changes['cpc_comments'] != []:
        return u'bid CPC remained unchanged at ${} because {}.'.format(
            changes['old_cpc_cc'].normalize(),
            u' and '.join(CpcChangeComment.get_text(c) for c in changes['cpc_comments']))
    return u'bid CPC remained unchanged at ${}.'.format(
        changes['old_cpc_cc'].normalize())
