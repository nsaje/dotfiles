import datetime
from decimal import Decimal
from django.db import transaction
import logging
import traceback

import influx

import dash.models
import dash.constants
from automation import models
from . import budgets
from . import constants
from . import cpc
from . import helpers
from . import prefetch
import redshiftapi.api_breakdowns
from utils import pagerduty_helper
from utils import dates_helper
from utils import k1_helper

logger = logging.getLogger(__name__)


@influx.timer('automation.autopilot_plus.run_autopilot')
def run_autopilot(ad_group=None, campaign=None, adjust_cpcs=True, adjust_budgets=True,
                  send_mail=False, initialization=False, report_to_influx=False, dry_run=False,
                  daily_run=False):
    ad_groups = None
    if ad_group is not None:
        ad_groups = [ad_group.id]
    if not ad_groups:
        ad_groups_on_ap, ad_group_settings_on_ap = helpers.get_active_ad_groups_on_autopilot()
    else:
        ad_groups_on_ap = dash.models.AdGroup.objects.filter(id__in=ad_groups)
        ad_group_settings_on_ap = dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_groups_on_ap).\
            group_current_settings().select_related('ad_group__campaign__account')

    entities = helpers.get_autopilot_entities(ad_group=ad_group, campaign=campaign)

    data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(entities)
    if not data:
        return {}
    changes_data = {}

    for adg_settings in ad_group_settings_on_ap:
        adg = adg_settings.ad_group
        if adg not in data:
            logger.warning('Data for ad group %s not prefetched in AP', str(adg))
            continue

        run_daily_budget_autopilot = adjust_budgets and (daily_run or not adg_settings.landing_mode)
        cpc_changes, budget_changes = _get_autopilot_predictions(
            run_daily_budget_autopilot, adjust_cpcs, adg, adg_settings,
            data[adg], campaign_goals.get(adg.campaign), bcm_modifiers_map.get(adg.campaign))
        try:
            with transaction.atomic():
                set_autopilot_changes(cpc_changes, budget_changes, adg, dry_run=dry_run)
                if not dry_run:
                    persist_autopilot_changes_to_log(adg_settings, cpc_changes, budget_changes, data[adg],
                                                     adg_settings.autopilot_state,
                                                     campaign_goals.get(adg.campaign),
                                                     is_autopilot_job_run=daily_run)
            changes_data = _get_autopilot_campaign_changes_data(
                adg, changes_data, cpc_changes, budget_changes)
            if not dry_run:
                k1_helper.update_ad_group(adg.pk, 'run_autopilot')
        except Exception as e:
            _report_autopilot_exception(adg, e)
    if send_mail:
        helpers.send_autopilot_changes_emails(changes_data, bcm_modifiers_map, initialization)
    if report_to_influx:
        _report_adgroups_data_to_influx(ad_group_settings_on_ap)
        _report_new_budgets_on_ap_to_influx(ad_group_settings_on_ap)
    return changes_data


def _get_autopilot_predictions(
        adjust_budgets, adjust_cpcs, adgroup, adgroup_settings,
        data, campaign_goal, bcm_modifiers):
    budget_changes = {}
    cpc_changes = {}
    rtb_as_one = adgroup_settings.b1_sources_group_enabled
    active_cpc_budget = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    is_budget_ap_enabled = adgroup_settings.autopilot_state == active_cpc_budget
    if adjust_budgets and is_budget_ap_enabled:
        budget_changes = budgets.get_autopilot_daily_budget_recommendations(
            adgroup, adgroup_settings.autopilot_daily_budget, data, bcm_modifiers,
            campaign_goal=campaign_goal['goal'] if campaign_goal else None, rtb_as_one=rtb_as_one)
    if adjust_cpcs:
        adjust_rtb_sources = not rtb_as_one or (is_budget_ap_enabled and rtb_as_one)
        cpc_changes = cpc.get_autopilot_cpc_recommendations(
            adgroup, adgroup_settings, data, bcm_modifiers,
            budget_changes=budget_changes, adjust_rtb_sources=adjust_rtb_sources)
    return cpc_changes, budget_changes


def initialize_budget_autopilot_on_ad_group(ad_group_settings, send_mail=False):
    ad_group = ad_group_settings.ad_group
    bcm_modifiers = ad_group.campaign.get_bcm_modifiers()
    paused_sources_changes = _set_paused_ad_group_sources_to_minimum_values(ad_group_settings, bcm_modifiers)
    autopilot_changes_data = run_autopilot(ad_group=ad_group, adjust_cpcs=False,
                                           adjust_budgets=True, initialization=True, send_mail=send_mail)
    changed_sources = set()
    for source, changes in paused_sources_changes.items():
        if changes['old_budget'] != changes['new_budget']:
            changed_sources.add(source)
    if autopilot_changes_data:
        for source, changes in autopilot_changes_data[ad_group.campaign][ad_group].items():
            if changes['old_budget'] != changes['new_budget']:
                changed_sources.add(source)
    return changed_sources


def _set_paused_ad_group_sources_to_minimum_values(ad_group_settings, bcm_modifiers):
    ad_group = ad_group_settings.ad_group
    ags_settings = helpers.get_autopilot_active_sources_settings(
        {ad_group: ad_group_settings}, dash.constants.AdGroupSettingsState.INACTIVE)
    if (ad_group_settings.b1_sources_group_enabled and
            ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE):
        ags_settings.append(dash.constants.SourceAllRTB)

    new_budgets = {}
    for ag_source_setting in ags_settings:
        if (ad_group_settings.b1_sources_group_enabled and ag_source_setting != dash.constants.SourceAllRTB and
                ag_source_setting.ad_group_source.source.source_type.type == dash.constants.SourceType.B1):
            continue
        ag_source = ag_source_setting.ad_group_source if ag_source_setting != dash.constants.SourceAllRTB else\
            dash.constants.SourceAllRTB
        old_budget = ad_group_settings.b1_sources_group_daily_budget
        if ag_source != dash.constants.SourceAllRTB:
            old_budget = ag_source_setting.daily_budget_cc if ag_source_setting.daily_budget_cc else\
                helpers.get_ad_group_sources_minimum_cpc(ag_source, bcm_modifiers)
        new_budgets[ag_source] = {
            'old_budget': old_budget,
            'new_budget': helpers.get_ad_group_sources_minimum_daily_budget(ag_source, bcm_modifiers),
            'budget_comments': [constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE]
        }
    try:
        with transaction.atomic():
            set_autopilot_changes({}, new_budgets, ad_group)
            persist_autopilot_changes_to_log(ad_group_settings, {}, new_budgets, new_budgets,
                                             dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
    except Exception as e:
        _report_autopilot_exception(ags_settings, e)
    return new_budgets


def _get_autopilot_campaign_changes_data(ad_group, email_changes_data, cpc_changes, budget_changes):
    camp = ad_group.campaign
    if camp not in email_changes_data:
        email_changes_data[camp] = {}
    email_changes_data[camp][ad_group] = {}
    for s in set(list(cpc_changes.keys()) + list(budget_changes.keys())):
        email_changes_data[camp][ad_group][s] = {}
        if s in cpc_changes:
            email_changes_data[camp][ad_group][s] = cpc_changes[s].copy()
        if s in budget_changes:
            email_changes_data[camp][ad_group][s].update(budget_changes[s])
    return email_changes_data


def persist_autopilot_changes_to_log(ad_group_settings, cpc_changes, budget_changes, data, autopilot_state,
                                     campaign_goal_data=None, is_autopilot_job_run=False):
    rtb_as_one = ad_group_settings.b1_sources_group_enabled
    for ag_source in list(data.keys()):
        old_budget = data[ag_source]['old_budget']
        goal_c = None
        if campaign_goal_data:
            uses_bcm_v2 = ad_group_settings.ad_group.campaign.account.uses_bcm_v2
            goal_c = helpers.get_campaign_goal_column(campaign_goal_data['goal'], uses_bcm_v2)
        goal_value = data[ag_source][goal_c] if goal_c and goal_c in data[ag_source] else 0.0
        new_cpc_cc = data[ag_source].get('old_cpc_cc', None)
        if cpc_changes:
            if ag_source in cpc_changes:
                new_cpc_cc = cpc_changes[ag_source]['new_cpc_cc']
            elif rtb_as_one and dash.constants.SourceAllRTB in cpc_changes:
                new_cpc_cc = cpc_changes[dash.constants.SourceAllRTB]['new_cpc_cc']
        new_daily_budget = old_budget
        if budget_changes:
            if ag_source in budget_changes:
                new_daily_budget = budget_changes[ag_source]['new_budget']
            elif dash.constants.SourceAllRTB in budget_changes:
                new_daily_budget = None
        cpc_comments = []
        if ag_source in cpc_changes:
            cpc_comments = cpc_changes[ag_source]['cpc_comments']
        elif rtb_as_one and dash.constants.SourceAllRTB in cpc_changes:
            cpc_comments = cpc_changes[dash.constants.SourceAllRTB]['cpc_comments']
        budget_comments = budget_changes[ag_source]['budget_comments'] if\
            budget_changes and ag_source in budget_changes else []

        models.AutopilotLog(
            ad_group=ad_group_settings.ad_group,
            autopilot_type=autopilot_state,
            ad_group_source=ag_source if ag_source != dash.constants.SourceAllRTB else None,
            previous_cpc_cc=data[ag_source].get('old_cpc_cc', None),
            new_cpc_cc=new_cpc_cc,
            previous_daily_budget=old_budget,
            new_daily_budget=new_daily_budget,
            yesterdays_spend_cc=data[ag_source].get('yesterdays_spend_cc', None),
            yesterdays_clicks=data[ag_source].get('yesterdays_clicks', None),
            goal_value=goal_value,
            cpc_comments=', '.join(constants.CpcChangeComment.get_text(c) for c in cpc_comments),
            budget_comments=', '.join(constants.DailyBudgetChangeComment.get_text(b)
                                      for b in budget_comments),
            campaign_goal=campaign_goal_data['goal'].type if campaign_goal_data else None,
            campaign_goal_optimal_value=campaign_goal_data['value'] if campaign_goal_data else None,
            is_autopilot_job_run=is_autopilot_job_run,
            is_rtb_as_one=rtb_as_one,
        ).save()


def set_autopilot_changes(cpc_changes={}, budget_changes={}, ad_group=None,
                          system_user=dash.constants.SystemUserType.AUTOPILOT,
                          dry_run=False, landing_mode=None):
    for ag_source in set(list(cpc_changes.keys()) + list(budget_changes.keys())):
        changes = {}
        if (cpc_changes and ag_source in cpc_changes and
                cpc_changes[ag_source]['old_cpc_cc'] != cpc_changes[ag_source]['new_cpc_cc']):
            changes['cpc_cc'] = cpc_changes[ag_source]['new_cpc_cc']
        if (budget_changes and ag_source in budget_changes and
                budget_changes[ag_source]['old_budget'] != budget_changes[ag_source]['new_budget']):
            changes['daily_budget_cc'] = budget_changes[ag_source]['new_budget']
        if changes and not dry_run:
            if ag_source == dash.constants.SourceAllRTB:
                helpers.update_ad_group_b1_sources_group_values(ad_group, changes, system_user)
            else:
                helpers.update_ad_group_source_values(ag_source, changes, system_user, landing_mode)


def _report_autopilot_exception(element, e):
    logger.exception('Autopilot failed operating on {} because an exception was raised: {}'.format(
                     element,
                     traceback.format_exc()))
    desc = {
        'element': ''  # repr(element)
    }
    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
        incident_key='automation_autopilot_error',
        description='Autopilot failed operating on element because an exception was raised: {}'.format(
            traceback.format_exc()),
        details=desc
    )


def _report_adgroups_data_to_influx(ad_groups_settings):
    num_on_budget_ap = 0
    total_budget_on_budget_ap = Decimal(0.0)
    num_on_cpc_ap = 0
    yesterday_spend_on_cpc_ap = Decimal(0.0)
    yesterday_spend_on_budget_ap = Decimal(0.0)
    yesterday = dates_helper.local_today() - datetime.timedelta(days=1)
    yesterday_data = redshiftapi.api_breakdowns.query(
        ['ad_group_id'],
        {
            'date__lte': yesterday,
            'date__gte': yesterday,
            'ad_group_id': [ags.ad_group_id for ags in ad_groups_settings]
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
    )
    for ad_group_setting in ad_groups_settings:
        yesterday_spend = Decimal('0')
        for row in yesterday_data:
            if row['ad_group_id'] == ad_group_setting.ad_group.id:
                if ad_group_setting.ad_group.campaign.account.uses_bcm_v2:
                    yesterday_spend = Decimal(row['etfm_cost'] or 0)
                else:
                    yesterday_spend = Decimal(row['et_cost'] or 0)
                break
        if ad_group_setting.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            num_on_budget_ap += 1
            total_budget_on_budget_ap += ad_group_setting.autopilot_daily_budget
            yesterday_spend_on_budget_ap += yesterday_spend
        elif ad_group_setting.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
            num_on_cpc_ap += 1
            yesterday_spend_on_cpc_ap += yesterday_spend

    influx.gauge('automation.autopilot_plus.adgroups_on', num_on_budget_ap, autopilot='budget_autopilot')
    influx.gauge('automation.autopilot_plus.adgroups_on', num_on_cpc_ap, autopilot='cpc_autopilot')

    influx.gauge('automation.autopilot_plus.spend', total_budget_on_budget_ap,
                 autopilot='budget_autopilot', type='expected')

    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_budget_ap,
                 autopilot='budget_autopilot', type='yesterday')
    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_cpc_ap,
                 autopilot='cpc_autopilot', type='yesterday')


def _report_new_budgets_on_ap_to_influx(ad_group_settings):
    total_budget_on_budget_ap = Decimal(0.0)
    total_budget_on_cpc_ap = Decimal(0.0)
    total_budget_on_all_ap = Decimal(0.0)
    num_sources_on_budget_ap = 0
    num_sources_on_cpc_ap = 0
    ad_groups_and_settings = {adgs.ad_group: adgs for adgs in ad_group_settings}
    active = dash.constants.AdGroupSourceSettingsState.ACTIVE
    rtb_as_one_budget_counted_adgroups = []
    for ag_source_setting in helpers.get_autopilot_active_sources_settings(ad_groups_and_settings):
        ad_group = ag_source_setting.ad_group_source.ad_group
        ag_settings = ad_groups_and_settings.get(ad_group)
        daily_budget = ag_source_setting.daily_budget_cc or Decimal('0')
        if (ag_settings.b1_sources_group_enabled and
                ag_settings.b1_sources_group_state == active and
                ag_source_setting.ad_group_source.source.source_type.type == dash.constants.SourceType.B1):
            if ad_group.id in rtb_as_one_budget_counted_adgroups:
                continue
            daily_budget = ag_settings.b1_sources_group_daily_budget or Decimal('0')
            rtb_as_one_budget_counted_adgroups.append(ad_group.id)
        total_budget_on_all_ap += daily_budget
        if ag_settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            total_budget_on_budget_ap += daily_budget
            num_sources_on_budget_ap += 1
        elif ag_settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
            total_budget_on_cpc_ap += daily_budget
            num_sources_on_cpc_ap += 1

    influx.gauge('automation.autopilot_plus.spend', total_budget_on_cpc_ap, autopilot='cpc_autopilot', type='actual')
    influx.gauge('automation.autopilot_plus.spend', total_budget_on_budget_ap,
                 autopilot='budget_autopilot', type='actual')

    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_cpc_ap, autopilot='cpc_autopilot')
    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_budget_ap, autopilot='budget_autopilot')
