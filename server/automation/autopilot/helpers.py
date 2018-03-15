from collections import defaultdict
import datetime
import logging

from django.db.models import Q

from automation import campaignstop

import dash
import dash.constants
import dash.models
from .constants import DailyBudgetChangeComment, CpcChangeComment
from . import settings
from utils import url_helper, k1_helper, email_helper

logger = logging.getLogger(__name__)


def get_active_ad_groups_on_autopilot(autopilot_state=None):
    states = [autopilot_state]
    if not autopilot_state:
        states = [dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
                  dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC]

    ad_groups_on_autopilot = []
    ad_group_settings_on_autopilot = []
    ad_group_settings = dash.models.AdGroupSettings.objects.all().group_current_settings()\
        .select_related('ad_group__campaign')
    campaignstop_states = campaignstop.get_campaignstop_states(dash.models.Campaign.objects.all())

    for ags in ad_group_settings:
        if ags.autopilot_state in states:
            ad_group = ags.ad_group
            ad_groups_sources_settings = dash.models.AdGroupSourceSettings.objects.\
                filter(ad_group_source__ad_group=ad_group).group_current_settings()

            ad_group_running = ad_group.get_running_status(ags) == dash.constants.AdGroupRunningStatus.ACTIVE
            ad_group_active = ags.state == dash.constants.AdGroupRunningStatus.ACTIVE
            sources_running = ad_group.get_running_status_by_sources_setting(
                ags,
                ad_groups_sources_settings
            ) == dash.constants.AdGroupRunningStatus.ACTIVE
            campaign_active = campaignstop_states[ad_group.campaign.id]['allowed_to_run']
            if ((campaign_active and ad_group_running and sources_running) or
                    (ags.landing_mode and ad_group_active and sources_running)):
                ad_groups_on_autopilot.append(ad_group)
                ad_group_settings_on_autopilot.append(ags)
    return ad_groups_on_autopilot, ad_group_settings_on_autopilot


def get_autopilot_entities(ad_group=None, campaign=None):
    states = [dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
              dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC]
    ad_groups = (
        dash.models.AdGroup.objects.all()
        .filter_active()
        .filter(Q(settings__autopilot_state__in=states) | Q(campaign__settings__autopilot=True))
        .select_related('settings', 'campaign__settings', 'campaign__account')
        .distinct()
    )
    if ad_group is not None:
        ad_groups = ad_groups.filter(id=ad_group.id)
    if campaign is not None:
        ad_groups = ad_groups.filter(campaign=campaign)

    campaignstop_states = campaignstop.get_campaignstop_states(
        dash.models.Campaign.objects.filter(adgroup__in=ad_groups)
    )
    ad_group_sources = (
        dash.models.AdGroupSource.objects.all()
        .filter(settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        .filter(ad_group_id__in=[ag.id for ag in ad_groups])
        .select_related('source__source_type')
        .select_related('settings')
    )
    ags_per_ag_id = defaultdict(list)
    for ags in ad_group_sources:
        ags_per_ag_id[ags.ad_group_id].append(ags)

    data = defaultdict(dict)
    for ad_group in ad_groups:
        if not campaignstop_states[ad_group.campaign.id]['allowed_to_run']:
            continue

        if (not ad_group.settings.landing_mode and
           ad_group.get_running_status(ad_group.settings) != dash.constants.AdGroupRunningStatus.ACTIVE):
            continue

        ags = ags_per_ag_id[ad_group.id]
        if (ad_group.settings.b1_sources_group_enabled and
           ad_group.settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE):
            ags = _exclude_b1_ad_group_sources(ags)

        if len(ags) == 0:
            continue

        data[ad_group.campaign][ad_group] = ags

    return data


def _exclude_b1_ad_group_sources(ad_group_sources):
    return [ags for ags in ad_group_sources if ags.source.source_type.type != dash.constants.SourceType.B1]


def get_autopilot_active_sources_settings(ad_groups_and_settings,
                                          ad_group_setting_state=dash.constants.AdGroupSettingsState.ACTIVE):
    adgroup_sources = (dash.models.AdGroupSource.objects
                       .filter(ad_group__in=list(ad_groups_and_settings.keys()))
                       .filter(ad_group__settings__archived=False)
                       .select_related('settings__ad_group_source__source__source_type')
                       .select_related('settings__ad_group_source__ad_group__campaign__account'))

    if not ad_group_setting_state:
        return [ags.settings for ags in ad_group_setting_state]

    ret = []
    for ags in adgroup_sources:
        agss = ags.settings
        ad_group_settings = ad_groups_and_settings[agss.ad_group_source.ad_group]
        if ad_group_setting_state == dash.constants.AdGroupSettingsState.ACTIVE:
            if (agss.ad_group_source.source.source_type.type == dash.constants.SourceType.B1 and
                    ad_group_settings.b1_sources_group_enabled and
                    ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE):
                continue
        elif ad_group_setting_state == dash.constants.AdGroupSettingsState.INACTIVE:
            if (agss.ad_group_source.source.source_type.type == dash.constants.SourceType.B1 and
                    ad_group_settings.b1_sources_group_enabled and
                    ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE):
                continue

        if agss.state == ad_group_setting_state:
            ret.append(agss)

    return ret


def ad_group_source_is_synced(ad_group_source):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=settings.SYNC_IS_RECENT_HOURS
    )
    last_sync = ad_group_source.last_successful_sync_dt
    if last_sync is None:
        return False
    return last_sync >= min_sync_date


def update_ad_group_source_values(ad_group_source, changes, system_user=None, landing_mode=None):
    if landing_mode is not None:
        changes['landing_mode'] = landing_mode
    ad_group_source.update(
        system_user=system_user,
        k1_sync=False,
        skip_automation=True,
        skip_validation=True,
        **changes
    )


def update_ad_group_b1_sources_group_values(ad_group, changes, system_user=None):
    new_settings = ad_group.get_current_settings().copy_settings()
    changed = False

    if 'cpc_cc' in changes and new_settings.b1_sources_group_cpc_cc != changes['cpc_cc']:
        changed = True
        new_settings.b1_sources_group_cpc_cc = changes['cpc_cc']
        ad_group_sources_cpcs = dash.views.helpers.get_adjusted_ad_group_sources_cpcs(ad_group, new_settings)
        dash.views.helpers.set_ad_group_sources_cpcs(ad_group_sources_cpcs, ad_group, new_settings)

    if 'daily_budget_cc' in changes and new_settings.b1_sources_group_daily_budget != changes['daily_budget_cc']:
        changed = True
        new_settings.b1_sources_group_daily_budget = changes['daily_budget_cc']

    if not changed:
        return

    k1_helper.update_ad_group(ad_group.pk, msg='AutopilotUpdateAdGroupB1SourcesGroupValues')
    new_settings.system_user = system_user
    new_settings.save(None)


def get_ad_group_sources_minimum_cpc(ad_group_source, bcm_modifiers):
    return max(
        settings.AUTOPILOT_MIN_CPC,
        ad_group_source.source.source_type.get_etfm_min_cpc(bcm_modifiers)
    )


def get_ad_group_sources_minimum_daily_budget(ad_group_source, bcm_modifiers):
    source_min_daily_budget = ad_group_source.source.source_type.get_etfm_min_daily_budget(bcm_modifiers)
    return max(settings.BUDGET_AP_MIN_SOURCE_BUDGET, source_min_daily_budget)


def get_campaign_goal_column(campaign_goal, uses_bcm_v2=False):
    if campaign_goal:
        column_definition = settings.GOALS_COLUMNS[campaign_goal.type]
        if uses_bcm_v2 and 'col_bcm_v2' in column_definition:
            return column_definition['col_bcm_v2']
        return column_definition['col']


def get_campaign_goal_column_importance(campaign_goal):
    if campaign_goal:
        return settings.GOALS_COLUMNS[campaign_goal.type]['importance']


def send_autopilot_changes_emails(email_changes_data, bcm_modifiers_map, initialization):
    for camp, changes_data in email_changes_data.items():
        emails = email_helper.email_manager_list(camp)
        emails.append(settings.AUTOPILOT_EMAIL_FOR_COPIES)
        if initialization:
            send_budget_autopilot_initialisation_email(camp, emails, changes_data)
        else:
            send_autopilot_changes_email(camp, emails, changes_data, bcm_modifiers_map.get(camp))


def send_autopilot_changes_email(campaign, emails, changes_data, bcm_modifiers):
    changes_text = []
    for adgroup, adgroup_changes in changes_data.items():
        changes_text.append(_get_email_adgroup_text(adgroup))
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name.lower()):
            changes_text.append(_get_email_source_changes_text(ag_source.source.name, adgroup_changes[ag_source]))
        changes_text.append(_get_email_adgroup_pausing_suggestions_text(adgroup_changes, bcm_modifiers))

    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': url_helper.get_full_z1_url('/v2/analytics/campaign/{}'.format(campaign.id)),
        'changes': ''.join(changes_text)
    }
    try:
        email_helper.send_official_email(
            recipient_list=emails,
            agency_or_user=campaign.account.agency,
            from_email=settings.AUTOPILOT_EMAIL,
            **email_helper.params_from_template(
                dash.constants.EmailTemplateType.AUTOPILOT_AD_GROUP_CHANGE, **args
            )
        )
    except Exception:
        logger.exception('Autopilot e-mail for campaign %s to %s was not sent' +
                         'because an exception was raised:',
                         campaign.name,
                         ', '.join(emails))


def send_budget_autopilot_initialisation_email(campaign, emails, changes_data):
    changes_text = []
    for adgroup, adgroup_changes in changes_data.items():
        changes_text.append(_get_email_adgroup_text(adgroup))
        for ag_source in sorted(adgroup_changes, key=lambda ag_source: ag_source.source.name.lower()):
            changes_text.append(_get_email_source_changes_text(ag_source.source.name, adgroup_changes[ag_source]))

    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': url_helper.get_full_z1_url('/v2/analytics/campaign/{}'.format(campaign.id)),
        'changes': ''.join(changes_text)
    }
    try:
        email_helper.send_official_email(
            recipient_list=emails,
            agency_or_user=campaign.account.agency,
            from_email=settings.AUTOPILOT_EMAIL,
            **email_helper.params_from_template(
                dash.constants.EmailTemplateType.AUTOPILOT_AD_GROUP_BUDGET_INIT, **args
            )
        )
    except Exception:
        logger.exception('Autopilot e-mail for initialising budget autopilot on an adroup in ' +
                         'campaign %s to %s was not sent because an exception was raised:',
                         campaign.name,
                         ', '.join(emails))


def _get_email_adgroup_text(adgroup):
    return '''

AdGroup: {adg_name} ({adg_url}):'''.format(
        adg_name=adgroup.name,
        adg_url=url_helper.get_full_z1_url('/v2/analytics/adgroup/{}/sources'.format(adgroup.id)),
    )


def _get_email_source_changes_text(source_name, changes):
    cpc_pilot_on = all(c in changes for c in ['old_cpc_cc', 'new_cpc_cc'])
    cpc_changed = cpc_pilot_on and changes['old_cpc_cc'] != changes['new_cpc_cc']
    budget_pilot_on = all(b in changes for b in ['new_budget', 'old_budget'])
    budget_changed = budget_pilot_on and changes['old_budget'] != changes['new_budget']

    text = '\n- on {} '.format(source_name)
    if budget_pilot_on:
        text += _get_budget_changes_text(budget_changed, changes)
        text += ' and ' if cpc_pilot_on else ''
    if cpc_pilot_on:
        text += _get_cpc_changes_text(cpc_changed, changes)
    return text


def _get_email_adgroup_pausing_suggestions_text(adgroup_changes, bcm_modifiers):
    suggested_sources = []
    for ag_source in adgroup_changes:
        changes = adgroup_changes[ag_source]
        if all(b in changes for b in ['new_budget', 'old_budget']) and\
                changes['new_budget'] == get_ad_group_sources_minimum_daily_budget(ag_source, bcm_modifiers):
            suggested_sources.append(ag_source.source.name)
    if suggested_sources:
        return '\n\nTo improve ad group\'s performance, please consider pausing the following media sources: ' +\
               ", ".join(suggested_sources) + '.\n'
    return ''


def _get_budget_changes_text(budget_changed, changes):
    if budget_changed:
        return 'daily spend cap changed from ${} to ${}'.format(
            '{0:.2f}'.format(changes['old_budget']),
            '{0:.2f}'.format(changes['new_budget']))
    elif DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET in changes['budget_comments']:
        return 'daily spend cap did not change because ' +\
            DailyBudgetChangeComment.get_text(DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET)
    else:
        return 'daily spend cap did not change'


def _get_cpc_changes_text(cpc_changed, changes):
    if cpc_changed:
        text = 'bid CPC changed from ${} to ${}'.format(
            changes['old_cpc_cc'].normalize(),
            changes['new_cpc_cc'].normalize())
        if changes['cpc_comments']:
            text += ' because ' + ' and '.join(CpcChangeComment.get_text(c) for c in changes['cpc_comments'])
        return text
    elif changes['cpc_comments'] != []:
        return 'bid CPC remained unchanged at ${} because {}.'.format(
            changes['old_cpc_cc'].normalize(),
            ' and '.join(CpcChangeComment.get_text(c) for c in changes['cpc_comments']))
    return 'bid CPC remained unchanged at ${}.'.format(
        changes['old_cpc_cc'].normalize())
