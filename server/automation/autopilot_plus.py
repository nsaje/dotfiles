import datetime
from decimal import Decimal
from django.db import transaction
import logging
import traceback

import influx

import actionlog.zwei_actions
import dash
import dash.campaign_goals
from dash.constants import CampaignGoalKPI
from dash import stats_helper
from automation import models
from automation import autopilot_budgets
from automation import autopilot_cpc
from automation import autopilot_helpers
from automation import autopilot_settings
import automation.constants
from dash.constants import AdGroupSettingsState, AdGroupSettingsAutopilotState
import reports.api_contentads
from utils import pagerduty_helper
from utils.statsd_helper import statsd_timer
from utils import statsd_helper
from utils import dates_helper

logger = logging.getLogger(__name__)


@influx.timer('automation.autopilot_plus.run_autopilot')
@statsd_timer('automation.autopilot_plus', 'run_autopilot')
def run_autopilot(ad_groups=None, adjust_cpcs=True, adjust_budgets=True,
                  send_mail=False, initialization=False, report_to_statsd=False):
    if not ad_groups:
        ad_groups_on_ap, ad_group_settings_on_ap = autopilot_helpers.get_active_ad_groups_on_autopilot()
    else:
        ad_groups_on_ap = dash.models.AdGroup.objects.filter(id__in=ad_groups)
        ad_group_settings_on_ap = dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_groups_on_ap).\
            group_current_settings().select_related('ad_group__campaign__account')
    data, campaign_goals = prefetch_autopilot_data(ad_groups_on_ap)
    if not data:
        return {}
    changes_data = {}

    actions = []
    for adg_settings in ad_group_settings_on_ap:
        adg = adg_settings.ad_group
        cpc_changes, budget_changes = _get_autopilot_predictions(
            adjust_budgets, adjust_cpcs, adg, adg_settings, data[adg], campaign_goals.get(adg.campaign))
        try:
            with transaction.atomic():
                actions.extend(set_autopilot_changes(cpc_changes, budget_changes))
                persist_autopilot_changes_to_log(cpc_changes, budget_changes, data[adg],
                                                 adg_settings.autopilot_state, campaign_goals.get(adg.campaign))
            changes_data = _get_autopilot_campaign_changes_data(
                adg, changes_data, cpc_changes, budget_changes)
        except Exception as e:
            _report_autopilot_exception(adg, e)
    actionlog.zwei_actions.send(actions)
    if send_mail:
        autopilot_helpers.send_autopilot_changes_emails(changes_data, data, initialization)
    if report_to_statsd:
        _report_adgroups_data_to_statsd(ad_group_settings_on_ap)
        _report_new_budgets_on_ap_to_statsd(ad_group_settings_on_ap)
    return changes_data


def _get_autopilot_predictions(adjust_budgets, adjust_cpcs, adgroup, adgroup_settings, data, campaign_goal):
    budget_changes = {}
    cpc_changes = {}
    if adjust_budgets and adgroup_settings.autopilot_state == AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        budget_changes = autopilot_budgets.\
            get_autopilot_daily_budget_recommendations(adgroup, adgroup_settings.autopilot_daily_budget,
                                                       data, campaign_goal=campaign_goal)
    if adjust_cpcs:
        cpc_changes = autopilot_cpc.get_autopilot_cpc_recommendations(adgroup, data, budget_changes=budget_changes)
    return cpc_changes, budget_changes


def initialize_budget_autopilot_on_ad_group(ad_group, send_mail=False):
    paused_sources_changes = _set_paused_ad_group_sources_to_minimum_values(ad_group)
    autopilot_changes_data = run_autopilot(ad_groups=[ad_group.id], adjust_cpcs=False,
                                           adjust_budgets=True, initialization=True, send_mail=send_mail)
    changed_sources = set()
    for source, changes in paused_sources_changes.iteritems():
        if changes['old_budget'] != changes['new_budget']:
            changed_sources.add(source)
    if autopilot_changes_data:
        for source, changes in autopilot_changes_data[ad_group.campaign][ad_group].iteritems():
            if changes['old_budget'] != changes['new_budget']:
                changed_sources.add(source)
    return changed_sources


def _set_paused_ad_group_sources_to_minimum_values(ad_group):
    ad_group_sources = autopilot_helpers.get_autopilot_active_sources_settings([ad_group],
                                                                               AdGroupSettingsState.INACTIVE)
    new_budgets = {}
    data = {}
    for ag_source_setting in ad_group_sources:
        ag_source = ag_source_setting.ad_group_source
        new_budgets[ag_source] = {
            'old_budget': ag_source_setting.daily_budget_cc if ag_source_setting.daily_budget_cc else
            autopilot_helpers.get_ad_group_sources_minimum_cpc(ag_source),
            'new_budget': autopilot_helpers.get_ad_group_sources_minimum_daily_budget(ag_source),
            'budget_comments': [automation.constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE]
        }
        data[ag_source] = {
            'old_cpc_cc': ag_source_setting.daily_budget_cc if ag_source_setting.daily_budget_cc else
            autopilot_helpers.get_ad_group_sources_minimum_cpc(ag_source),
            'old_budget': ag_source_setting.daily_budget_cc if ag_source_setting.daily_budget_cc else
            autopilot_helpers.get_ad_group_sources_minimum_daily_budget(ag_source),
            'yesterdays_spend_cc': None,
            'yesterdays_clicks': None
        }
    try:
        with transaction.atomic():
            actions = set_autopilot_changes({}, new_budgets)
            persist_autopilot_changes_to_log({}, new_budgets, data, AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        actionlog.zwei_actions.send(actions)
    except Exception as e:
        _report_autopilot_exception(ad_group_sources, e)
    return new_budgets


def _get_autopilot_campaign_changes_data(ad_group, email_changes_data, cpc_changes, budget_changes):
    camp = ad_group.campaign
    if camp not in email_changes_data:
        email_changes_data[camp] = {}
    email_changes_data[camp][ad_group] = {}
    for s in set(cpc_changes.keys() + budget_changes.keys()):
        email_changes_data[camp][ad_group][s] = {}
        if s in cpc_changes:
            email_changes_data[camp][ad_group][s] = cpc_changes[s].copy()
        if s in budget_changes:
            email_changes_data[camp][ad_group][s].update(budget_changes[s])
    return email_changes_data


def persist_autopilot_changes_to_log(cpc_changes, budget_changes, data, autopilot_state, campaign_goal=None):
    for ag_source in data.keys():
        old_budget = data[ag_source]['old_budget']
        goal_col = autopilot_helpers.get_campaign_goal_column(campaign_goal)
        goal_value = data[ag_source][goal_col] if goal_col in data[ag_source] else 0.0
        models.AutopilotLog(
            ad_group=ag_source.ad_group,
            autopilot_type=autopilot_state,
            ad_group_source=ag_source,
            previous_cpc_cc=data[ag_source]['old_cpc_cc'],
            new_cpc_cc=cpc_changes[ag_source]['new_cpc_cc'] if cpc_changes else data[ag_source]['old_cpc_cc'],
            previous_daily_budget=old_budget,
            new_daily_budget=budget_changes[ag_source]['new_budget'] if budget_changes else old_budget,
            yesterdays_spend_cc=data[ag_source]['yesterdays_spend_cc'],
            yesterdays_clicks=data[ag_source]['yesterdays_clicks'],
            goal_value=goal_value,
            cpc_comments=', '.join(automation.constants.CpcChangeComment.get_text(comment) for comment in
                                   cpc_changes[ag_source]['cpc_comments']) if cpc_changes else '',
            budget_comments=', '.join(automation.constants.DailyBudgetChangeComment.get_text(c) for c in
                                      budget_changes[ag_source]['budget_comments']) if budget_changes else '',
            campaign_goal=campaign_goal.type if campaign_goal else None
        ).save()


def set_autopilot_changes(cpc_changes={}, budget_changes={}, system_user=None, landing_mode=None):
    actions = []
    for ag_source in set(cpc_changes.keys() + budget_changes.keys()):
        changes = {}
        if cpc_changes and cpc_changes[ag_source]['old_cpc_cc'] != cpc_changes[ag_source]['new_cpc_cc']:
            changes['cpc_cc'] = cpc_changes[ag_source]['new_cpc_cc']
        if budget_changes and budget_changes[ag_source]['old_budget'] != budget_changes[ag_source]['new_budget']:
            changes['daily_budget_cc'] = budget_changes[ag_source]['new_budget']
        if changes:
            actions.extend(
                autopilot_helpers.update_ad_group_source_values(ag_source, changes, system_user, landing_mode))
    return actions


def prefetch_autopilot_data(ad_groups):
    enabled_ag_sources_settings = autopilot_helpers.get_autopilot_active_sources_settings(ad_groups)
    sources = [s.ad_group_source.source.id for s in enabled_ag_sources_settings]
    yesterday_data, days_ago_data, conv_days_ago_data, campaign_goals, conv_goals = _fetch_data(ad_groups, sources)
    data = {}
    for source_setting in enabled_ag_sources_settings:
        ag_source = source_setting.ad_group_source
        adg = ag_source.ad_group
        row, yesterdays_spend_cc, yesterdays_clicks = _find_corresponding_source_data(
            ag_source, days_ago_data, yesterday_data)
        if adg not in data:
            data[adg] = {}
        data[adg][ag_source] = _populate_prefetch_adgroup_source_data(ag_source, source_setting,
                                                                      yesterdays_spend_cc, yesterdays_clicks)
        campaign_goal = campaign_goals.get(adg.campaign)
        if campaign_goal:
            col = autopilot_helpers.get_campaign_goal_column(campaign_goal)
            goal_value = autopilot_settings.GOALS_WORST_VALUE.get(col)
            if campaign_goal.type == CampaignGoalKPI.CPA:
                    goal_value = _get_conversion_value(ag_source, conv_days_ago_data,
                                                       campaign_goal.conversion_goal, conv_goals)
            else:
                if col in row and row[col]:
                    goal_value = row[col]
            data[adg][ag_source][col] = goal_value
    return data, campaign_goals


def _get_conversion_value(ag_source, data, conversion_goal, conversion_goals):
    view_key = conversion_goal.get_view_key(conversion_goals)
    for r in data:
        if r['ad_group'] == ag_source.ad_group.id and r['source'] == ag_source.source.id:
            return r.get(view_key)
    return 0


def _populate_prefetch_adgroup_source_data(ag_source, ag_source_setting, yesterdays_spend_cc, yesterdays_clicks):
    data = {}
    budget = ag_source_setting.daily_budget_cc if ag_source_setting.daily_budget_cc else\
        ag_source.source.source_type.min_daily_budget
    data['yesterdays_spend_cc'] = yesterdays_spend_cc
    data['yesterdays_clicks'] = yesterdays_clicks
    data['old_budget'] = budget
    data['old_cpc_cc'] = ag_source_setting.cpc_cc if ag_source_setting.cpc_cc else\
        ag_source.source.default_cpc_cc
    data['spend_perc'] = yesterdays_spend_cc / budget
    return data


def _fetch_data(ad_groups, sources):
    today = dates_helper.local_today()
    yesterday = today - datetime.timedelta(days=1)
    campaign_goals, conversion_goals = _get_autopilot_goals(ad_groups)

    yesterday_data = reports.api_contentads.query(
        yesterday,
        yesterday,
        breakdown=['ad_group', 'source'],
        ad_group=ad_groups,
        source=sources
    )

    days_ago_data = reports.api_contentads.query(
        yesterday - datetime.timedelta(days=autopilot_settings.AUTOPILOT_DATA_LOOKBACK_DAYS),
        yesterday,
        breakdown=['ad_group', 'source'],
        ad_group=ad_groups,
        source=sources
    )

    conversions_days_ago_data = stats_helper.get_stats_with_conversions(
        None,
        yesterday - datetime.timedelta(days=autopilot_settings.AUTOPILOT_CONVERSION_DATA_LOOKBACK_DAYS),
        yesterday,
        breakdown=['ad_group', 'source'],
        conversion_goals=conversion_goals,
        constraints={
            'ad_group': ad_groups,
            'source': sources,
        },
        filter_by_permissions=False)

    return yesterday_data, days_ago_data, conversions_days_ago_data, campaign_goals, conversion_goals


def _find_corresponding_source_data(ag_source, days_ago_data, yesterday_data):
    row = []
    yesterdays_spend_cc = Decimal(0)
    yesterdays_clicks = 0
    for r in days_ago_data:
        if r['ad_group'] == ag_source.ad_group.id and r['source'] == ag_source.source.id:
            row = r
            break
    for r in yesterday_data:
        if r['ad_group'] == ag_source.ad_group.id and r['source'] == ag_source.source.id:
            cost = r.get('cost')
            yesterdays_spend_cc = Decimal(cost) if cost else Decimal('0')
            yesterdays_clicks = r.get('clicks')
            break
    return row, yesterdays_spend_cc, yesterdays_clicks


def _get_autopilot_goals(ad_groups):
    campaign_goals = {}
    conversion_goals = []
    for adg in ad_groups:
        camp = adg.campaign
        if camp not in campaign_goals:
            primary_goal = dash.campaign_goals.get_primary_campaign_goal(camp)
            campaign_goals[camp] = primary_goal
            if primary_goal and primary_goal.type == dash.constants.CampaignGoalKPI.CPA:
                conversion_goals.append(primary_goal.conversion_goal)
    return campaign_goals, conversion_goals


def _report_autopilot_exception(element, e):
    logger.exception(u'Autopilot failed operating on {} because an exception was raised: {}'.format(
                     element,
                     traceback.format_exc(e)))
    desc = {
        'element': element
    }
    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
        incident_key='automation_autopilot_error',
        description=u'Autopilot failed operating on element because an exception was raised: {}'.format(
            traceback.format_exc(e)),
        details=desc
    )


def _report_adgroups_data_to_statsd(ad_groups_settings):
    num_on_budget_ap = 0
    total_budget_on_budget_ap = Decimal(0.0)
    num_on_cpc_ap = 0
    yesterday_spend_on_cpc_ap = Decimal(0.0)
    yesterday_spend_on_budget_ap = Decimal(0.0)
    yesterday = dates_helper.local_today() - datetime.timedelta(days=1)
    yesterday_data = reports.api_contentads.query(yesterday, yesterday, breakdown=['ad_group'],
                                                  ad_group=[ags.ad_group for ags in ad_groups_settings])
    for ad_group_setting in ad_groups_settings:
        yesterday_spend = Decimal('0')
        for row in yesterday_data:
            if row['ad_group'] == ad_group_setting.ad_group.id:
                cost = row.get('cost')
                yesterday_spend = Decimal(cost) if cost else Decimal('0')
                break
        if ad_group_setting.autopilot_state == AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            num_on_budget_ap += 1
            total_budget_on_budget_ap += ad_group_setting.autopilot_daily_budget
            yesterday_spend_on_budget_ap += yesterday_spend
        elif ad_group_setting.autopilot_state == AdGroupSettingsAutopilotState.ACTIVE_CPC:
            num_on_cpc_ap += 1
            yesterday_spend_on_cpc_ap += yesterday_spend

    influx.gauge('automation.autopilot_plus.adgroups_on', num_on_budget_ap, autopilot='budget_autopilot')
    influx.gauge('automation.autopilot_plus.adgroups_on', num_on_cpc_ap, autopilot='cpc_autopilot')
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_budget_autopilot', num_on_budget_ap)
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_cpc_autopilot', num_on_cpc_ap)

    influx.gauge('automation.autopilot_plus.spend', total_budget_on_budget_ap,
                 autopilot='budget_autopilot', type='expected')
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_budget_autopilot_expected_budget',
                               total_budget_on_budget_ap)

    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_budget_ap,
                 autopilot='budget_autopilot', type='yesterday')
    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_cpc_ap,
                 autopilot='cpc_autopilot', type='yesterday')
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_budget_autopilot_yesterday_spend',
                               yesterday_spend_on_budget_ap)
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_cpc_autopilot_yesterday_spend',
                               yesterday_spend_on_cpc_ap)


def _report_new_budgets_on_ap_to_statsd(ad_group_settings):
    total_budget_on_budget_ap = Decimal(0.0)
    total_budget_on_cpc_ap = Decimal(0.0)
    total_budget_on_all_ap = Decimal(0.0)
    num_sources_on_budget_ap = 0
    num_sources_on_cpc_ap = 0
    ad_groups_and_ap_types = {adgs.ad_group: adgs.autopilot_state for adgs in ad_group_settings}
    for ag_source_setting in autopilot_helpers.get_autopilot_active_sources_settings(ad_groups_and_ap_types.keys()):
        ad_group = ag_source_setting.ad_group_source.ad_group
        daily_budget = ag_source_setting.daily_budget_cc if ag_source_setting.daily_budget_cc else Decimal(0)
        total_budget_on_all_ap += daily_budget
        if ad_groups_and_ap_types.get(ad_group) == AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            total_budget_on_budget_ap += daily_budget
            num_sources_on_budget_ap += 1
        elif ad_groups_and_ap_types.get(ad_group) == AdGroupSettingsAutopilotState.ACTIVE_CPC:
            total_budget_on_cpc_ap += daily_budget
            num_sources_on_cpc_ap += 1

    influx.gauge('automation.autopilot_plus.spend', total_budget_on_cpc_ap, autopilot='cpc_autopilot', type='actual')
    influx.gauge('automation.autopilot_plus.spend', total_budget_on_budget_ap,
                 autopilot='budget_autopilot', type='actual')
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_budget_autopilot_actual_budget',
                               total_budget_on_budget_ap)
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_cpc_autopilot_actual_budget',
                               total_budget_on_cpc_ap)
    statsd_helper.statsd_gauge('automation.autopilot_plus.adgroups_on_all_autopilot_actual_budget',
                               total_budget_on_all_ap)

    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_cpc_ap, autopilot='cpc_autopilot')
    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_budget_ap, autopilot='budget_autopilot')
    statsd_helper.statsd_gauge('automation.autopilot_plus.num_sources_on_cpc_ap', num_sources_on_cpc_ap)
    statsd_helper.statsd_gauge('automation.autopilot_plus.num_sources_on_budget_ap', num_sources_on_budget_ap)
