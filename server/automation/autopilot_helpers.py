import datetime
import logging
import traceback

from django.core.mail import send_mail

import dash
from dash.constants import AdGroupSettingsState, EmailTemplateType
from automation import autopilot_settings
import automation.helpers
from automation.constants import DailyBudgetChangeComment, CpcChangeComment
from dash import constants
import dash.models
from utils import pagerduty_helper, url_helper
from utils.email_helper import format_email, email_manager_list

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

            if (ad_group.get_running_status(ags) == constants.AdGroupRunningStatus.ACTIVE and
               ad_group.get_running_status_by_sources_setting(ags, ad_groups_sources_settings) ==
               constants.AdGroupRunningStatus.ACTIVE):
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
    dash.api.set_ad_group_source_settings(
        ad_group_source, changes, None, system_user=system_user, landing_mode=landing_mode, ping_k1=False)


def update_ad_group_values(ad_group, changes, system_user=None, landing_mode=None):
    print 'UPDATING ADGROUP SETTINGS: ', changes # TODO DAVORINNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN


def get_ad_group_sources_minimum_cpc(ad_group_source):
    return max(autopilot_settings.AUTOPILOT_MIN_CPC, ad_group_source.source.source_type.min_cpc)


def get_ad_group_sources_minimum_daily_budget(ad_group_source,
                                              ap_type=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET):
    if ad_group_source == 'b1_sources':
        source_min_daily_budget = constants.SourceAllRTB.MIN_DAILY_BUDGET
    else:
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
        emails = email_manager_list(camp)
        emails.append(autopilot_settings.AUTOPILOT_EMAIL_FOR_COPIES)
        if initialization:
            send_budget_autopilot_initialisation_email(camp, emails, changes_data)
        else:
            send_autopilot_changes_email(camp, emails, changes_data)


def send_autopilot_changes_email(campaign, emails, changes_data):
    changesText = []
    for adgroup, adgroup_changes in changes_data.iteritems():
        changesText.append(_get_email_adgroup_text(adgroup))
        if 'b1_sources' in adgroup_changes:
            changesText.append(_get_email_source_changes_text('RTB Sources', adgroup_changes['b1_sources']))
            adgroup_changes.pop('b1_sources', None)
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name.lower()):
            changesText.append(_get_email_source_changes_text(ag_source.source.name, adgroup_changes[ag_source]))
        changesText.append(_get_email_adgroup_pausing_suggestions_text(adgroup_changes))

    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': url_helper.get_full_z1_url('/campaigns/{}/'.format(campaign.id)),
        'changes': ''.join(changesText)
    }
    subject, body, _ = format_email(EmailTemplateType.AUTOPILOT_AD_GROUP_CHANGE, **args)
    try:
        print body # TODO DAVORIN !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        send_mail(
            subject,
            body,
            u'Zemanta <{}>'.format(automation.autopilot_settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Autopilot e-mail for campaign %s to %s was not sent' +
                         'because an exception was raised:',
                         campaign.name,
                         u', '.join(emails))
        desc = {
            'campaign_name': campaign.name,
            'email': ', '.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
            incident_key='automation_autopilot_email',
            description=u'Autopilot e-mail for campaign was not sent because an exception was raised: {}'.
                        format(traceback.format_exc(e)),
            details=desc
        )


def send_budget_autopilot_initialisation_email(campaign, emails, changes_data):
    changesText = []
    for adgroup, adgroup_changes in changes_data.iteritems():
        changesText.append(_get_email_adgroup_text(adgroup))
        if 'b1_sources' in adgroup_changes:
            changesText.append(_get_email_source_changes_text('RTB Sources', adgroup_changes['b1_sources']))
            adgroup_changes.pop('b1_sources', None)
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name.lower()):
            changesText.append(_get_email_source_changes_text(ag_source.source.name, adgroup_changes[ag_source]))

    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': url_helper.get_full_z1_url('/campaigns/{}/'.format(campaign.id)),
        'changes': ''.join(changesText)
    }
    subject, body, _ = format_email(EmailTemplateType.AUTOPILOT_AD_GROUP_BUDGET_INIT, **args)
    try:
        send_mail(
            subject,
            body,
            u'Zemanta <{}>'.format(automation.autopilot_settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Autopilot e-mail for initialising budget autopilot on an adroup in ' +
                         'campaign %s to %s was not sent because an exception was raised:',
                         campaign.name,
                         u', '.join(emails))
        desc = {
            'campaign_name': campaign.name,
            'email': ', '.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
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


def _get_email_source_changes_text(source_name, changes):
    cpc_pilot_on = all(c in changes for c in ['old_cpc_cc', 'new_cpc_cc'])
    cpc_changed = cpc_pilot_on and changes['old_cpc_cc'] != changes['new_cpc_cc']
    budget_pilot_on = all(b in changes for b in ['new_budget', 'old_budget'])
    budget_changed = budget_pilot_on and changes['old_budget'] != changes['new_budget']

    text = u'\n- on {} '.format(source_name)
    if budget_pilot_on:
        text += _get_budget_changes_text(budget_changed, changes)
        text += u' and ' if cpc_pilot_on else u''
    if cpc_pilot_on:
        text += _get_cpc_changes_text(cpc_changed, changes)
    return text


def _get_email_adgroup_pausing_suggestions_text(adgroup_changes):
    suggested_sources = []
    for ag_source in adgroup_changes:
        changes = adgroup_changes[ag_source]
        if all(b in changes for b in ['new_budget', 'old_budget']) and\
                changes['new_budget'] == get_ad_group_sources_minimum_daily_budget(ag_source):
            suggested_sources.append(ag_source.source.name if ag_source != 'b1_sources' else 'RTB Sources')
    if suggested_sources:
        return '\n\nTo improve ad group\'s performance, please consider pausing the following media sources: ' +\
               ", ".join(suggested_sources) + '.\n'
    return ''


def _get_budget_changes_text(budget_changed, changes):
    if budget_changed:
        return u'daily spend cap changed from ${} to ${}'.format(
            '{0:.2f}'.format(changes['old_budget']),
            '{0:.2f}'.format(changes['new_budget']))
    elif DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET in changes['budget_comments']:
        return u'daily spend cap did not change because ' +\
            DailyBudgetChangeComment.get_text(DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET)
    else:
        return u'daily spend cap did not change'


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
