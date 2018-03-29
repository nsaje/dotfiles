from collections import defaultdict
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
from .campaign import calculate_campaigns_daily_budget
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
    entities = helpers.get_autopilot_entities(ad_group=ad_group, campaign=campaign)
    if ad_group is None:  # do not calculate campaign budgets when run for one ad_group only
        campaign_daily_budgets = calculate_campaigns_daily_budget(campaign=campaign)

    data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(entities)
    if not data:
        return {}
    changes_data = {}

    for campaign, ad_groups in entities.items():
        ad_groups = _filter_adgroups_with_data(ad_groups, data)
        if campaign.settings.autopilot:
            budget_changes_map = _get_budget_predictions_for_campaign(
                campaign,
                ad_groups,
                campaign_daily_budgets[campaign],
                data,
                bcm_modifiers_map.get(campaign),
                campaign_goals.get(campaign, {}),
                campaign.account.uses_bcm_v2,
                adjust_budgets,
            )
            cpc_changes_map = {}
            for ad_group in ad_groups:
                cpc_changes_map[ad_group] = _get_cpc_predictions(
                    ad_group,
                    budget_changes_map[ad_group],
                    data[ad_group],
                    bcm_modifiers_map.get(campaign),
                    adjust_cpcs,
                    is_budget_ap_enabled=True,
                )
                changes_data = _get_autopilot_campaign_changes_data(
                    ad_group, changes_data, cpc_changes_map[ad_group], budget_changes_map[ad_group])
            _save_changes_campaign(
                campaign,
                ad_groups,
                data,
                campaign_goals,
                budget_changes_map,
                cpc_changes_map,
                dry_run,
                daily_run,
            )
        else:
            for ad_group in ad_groups:
                budget_changes = _get_budget_predictions_for_adgroup(
                    ad_group,
                    data[ad_group],
                    bcm_modifiers_map.get(campaign),
                    campaign_goals.get(campaign, {}),
                    campaign.account.uses_bcm_v2,
                    adjust_budgets,
                    daily_run,
                )
                cpc_changes = _get_cpc_predictions(
                    ad_group,
                    budget_changes,
                    data[ad_group],
                    bcm_modifiers_map.get(campaign),
                    adjust_cpcs,
                )
                _save_changes(
                    data,
                    campaign_goals,
                    ad_group,
                    budget_changes,
                    cpc_changes,
                    dry_run,
                    daily_run,
                )
                changes_data = _get_autopilot_campaign_changes_data(
                    ad_group, changes_data, cpc_changes, budget_changes)

    if send_mail:
        helpers.send_autopilot_changes_emails(changes_data, bcm_modifiers_map, initialization)
    if report_to_influx:
        # refresh entities from db so we report new data, always report data for all entities
        entities = helpers.get_autopilot_entities()
        _report_adgroups_data_to_influx(entities, campaign_daily_budgets)
        _report_new_budgets_on_ap_to_influx(entities)
    return changes_data


@transaction.atomic
def _save_changes_campaign(campaign, ad_groups, data, campaign_goals, budget_changes_map, cpc_changes_map, dry_run, daily_run):
    if dry_run:
        return
    for ad_group in ad_groups:
        _save_changes(
            data,
            campaign_goals,
            ad_group,
            budget_changes_map[ad_group],
            cpc_changes_map[ad_group],
            dry_run,
            daily_run,
            campaign=campaign,
        )


def _save_changes(data, campaign_goals, ad_group, budget_changes, cpc_changes, dry_run, daily_run, campaign=None):
    if dry_run:
        return
    try:
        with transaction.atomic():
            set_autopilot_changes(cpc_changes, budget_changes, ad_group, dry_run=dry_run)
            persist_autopilot_changes_to_log(
                ad_group,
                cpc_changes,
                budget_changes,
                data[ad_group],
                ad_group.settings.autopilot_state,
                campaign_goals.get(ad_group.campaign),
                is_autopilot_job_run=daily_run,
                campaign=campaign,
            )
        k1_helper.update_ad_group(ad_group.pk, 'run_autopilot')
    except Exception as e:
        _report_autopilot_exception(ad_group, e)


def _filter_adgroups_with_data(ad_groups, data):
    result = {}
    for ad_group, value in ad_groups.items():
        if ad_group not in data:
            logger.warning('Data for ad group %s not prefetched in AP', str(ad_group))
            continue
        result[ad_group] = value
    return result


def _get_budget_predictions_for_adgroup(ad_group, data, bcm_modifiers, campaign_goal, uses_bcm_v2, adjust_budgets, daily_run):
    if ad_group.settings.autopilot_state != dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return {}
    if not adjust_budgets:
        return {}
    if not (daily_run or not ad_group.settings.landing_mode):
        return {}

    return budgets.get_autopilot_daily_budget_recommendations(
        ad_group,
        ad_group.settings.autopilot_daily_budget,
        _filter_data_budget_ap_allrtb(data, ad_group),
        bcm_modifiers,
        campaign_goal.get('goal'),
        uses_bcm_v2,
    )


def _get_budget_predictions_for_campaign(campaign, ad_groups, daily_budget, data, bcm_modifiers, campaign_goal, uses_bcm_v2, adjust_budgets):
    if not campaign.settings.autopilot:
        return {}
    if not adjust_budgets:
        return {}

    campaign_data = {}
    for ad_group in ad_groups:
        campaign_data.update(_filter_data_budget_ap_allrtb(data[ad_group], ad_group))

    changes = budgets.get_autopilot_daily_budget_recommendations(
        campaign,
        daily_budget,
        campaign_data,
        bcm_modifiers,
        campaign_goal.get('goal'),
        uses_bcm_v2,
        ignore_daily_budget_too_small=True,
    )

    grouped_changes = defaultdict(dict)
    for ad_group_source, change in changes.items():
        grouped_changes[ad_group_source.ad_group][ad_group_source] = change

    return grouped_changes


def _filter_data_budget_ap_allrtb(data, ad_group):
    if ad_group.settings.b1_sources_group_enabled:
        data = {ags: v for ags, v in data.items() if
                ags.source == dash.models.AllRTBSource or ags.source.source_type.type != dash.constants.SourceType.B1}
    return data


def _get_cpc_predictions(ad_group, budget_changes, data, bcm_modifiers, adjust_cpcs, is_budget_ap_enabled=False):
    cpc_changes = {}
    rtb_as_one = ad_group.settings.b1_sources_group_enabled
    active_cpc_budget = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    is_budget_ap_enabled = ad_group.settings.autopilot_state == active_cpc_budget or is_budget_ap_enabled
    if adjust_cpcs:
        adjust_rtb_sources = not rtb_as_one or (is_budget_ap_enabled and rtb_as_one)
        cpc_changes = cpc.get_autopilot_cpc_recommendations(
            ad_group,
            data,
            bcm_modifiers,
            budget_changes=budget_changes,
            adjust_rtb_sources=adjust_rtb_sources,
        )
    return cpc_changes


def recalculate_budgets_ad_group(ad_group, send_mail=False):
    changed_sources = set()
    if ad_group.campaign.settings.autopilot:
        run_autopilot(
            campaign=ad_group.campaign,
            adjust_cpcs=False,
            adjust_budgets=True,
            initialization=True,
            send_mail=send_mail,
        )
    else:
        paused_sources_changes = _set_paused_ad_group_sources_to_minimum_values(
            ad_group, ad_group.campaign.get_bcm_modifiers())
        autopilot_changes_data = run_autopilot(
            ad_group=ad_group, adjust_cpcs=False, adjust_budgets=True, initialization=True, send_mail=send_mail)

        for source, changes in paused_sources_changes.items():
            if changes['old_budget'] != changes['new_budget']:
                changed_sources.add(source)
        if autopilot_changes_data:
            for source, changes in autopilot_changes_data[ad_group.campaign][ad_group].items():
                if changes['old_budget'] != changes['new_budget']:
                    changed_sources.add(source)

    return changed_sources


def recalculate_budgets_campaign(campaign, send_mail=False):
    if not campaign.settings.autopilot:
        bcm_modifiers = campaign.get_bcm_modifiers()
        budget_autopilot_adgroups = (
            campaign.adgroup_set.all()
            .filter(settings__autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
            .select_related('settings')
        )
        for ad_group in budget_autopilot_adgroups:
            _set_paused_ad_group_sources_to_minimum_values(ad_group, bcm_modifiers)

    run_autopilot(campaign=campaign, adjust_cpcs=False, adjust_budgets=True, initialization=True, send_mail=send_mail)


def _set_paused_ad_group_sources_to_minimum_values(ad_group, bcm_modifiers):
    all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(ad_group)
    ags_settings = helpers.get_autopilot_active_sources_settings(
        {ad_group: ad_group.settings}, dash.constants.AdGroupSettingsState.INACTIVE)
    if (ad_group.settings.b1_sources_group_enabled and
            ad_group.settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE):
        ags_settings.append(all_rtb_ad_group_source)

    new_budgets = {}
    for ag_source_setting in ags_settings:
        if (ad_group.settings.b1_sources_group_enabled and ag_source_setting != all_rtb_ad_group_source and
                ag_source_setting.ad_group_source.source.source_type.type == dash.constants.SourceType.B1):
            continue
        ag_source = ag_source_setting.ad_group_source if ag_source_setting != all_rtb_ad_group_source else\
            all_rtb_ad_group_source
        old_budget = ad_group.settings.b1_sources_group_daily_budget
        if ag_source != all_rtb_ad_group_source:
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
            persist_autopilot_changes_to_log(ad_group, {}, new_budgets, new_budgets,
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


def persist_autopilot_changes_to_log(ad_group, cpc_changes, budget_changes, data, autopilot_state,
                                     campaign_goal_data=None, is_autopilot_job_run=False, campaign=None):
    rtb_as_one = ad_group.settings.b1_sources_group_enabled
    all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(ad_group)
    for ag_source in list(data.keys()):
        old_budget = data[ag_source]['old_budget']
        goal_c = None
        if campaign_goal_data:
            uses_bcm_v2 = ad_group.campaign.account.uses_bcm_v2
            goal_c = helpers.get_campaign_goal_column(campaign_goal_data['goal'], uses_bcm_v2)
        goal_value = data[ag_source][goal_c] if goal_c and goal_c in data[ag_source] else 0.0
        new_cpc_cc = data[ag_source].get('old_cpc_cc', None)
        if cpc_changes:
            if ag_source in cpc_changes:
                new_cpc_cc = cpc_changes[ag_source]['new_cpc_cc']
            elif rtb_as_one and all_rtb_ad_group_source in cpc_changes:
                new_cpc_cc = cpc_changes[all_rtb_ad_group_source]['new_cpc_cc']
        new_daily_budget = old_budget
        if budget_changes:
            if ag_source in budget_changes:
                new_daily_budget = budget_changes[ag_source]['new_budget']
            elif all_rtb_ad_group_source in budget_changes:
                new_daily_budget = None
        cpc_comments = []
        if ag_source in cpc_changes:
            cpc_comments = cpc_changes[ag_source]['cpc_comments']
        elif rtb_as_one and all_rtb_ad_group_source in cpc_changes:
            cpc_comments = cpc_changes[all_rtb_ad_group_source]['cpc_comments']
        budget_comments = budget_changes[ag_source]['budget_comments'] if\
            budget_changes and ag_source in budget_changes else []

        models.AutopilotLog(
            campaign=campaign,
            ad_group=ad_group,
            autopilot_type=autopilot_state,
            ad_group_source=ag_source if ag_source != all_rtb_ad_group_source else None,
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
            if ag_source.source == dash.models.AllRTBSource:
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


def _report_adgroups_data_to_influx(entities, campaign_daily_budgets):
    ad_group_ids = [ad_group.id for ad_groups_dict in entities.values() for ad_group in ad_groups_dict.keys()]
    num_campaigns_on_campaign_ap = 0
    num_ad_groups_on_campaign_ap = 0
    total_budget_on_campaign_ap = Decimal(0.0)
    num_on_budget_ap = 0
    total_budget_on_budget_ap = Decimal(0.0)
    num_on_cpc_ap = 0
    yesterday_spend_on_cpc_ap = Decimal(0.0)
    yesterday_spend_on_budget_ap = Decimal(0.0)
    yesterday_spend_on_campaign_ap = Decimal(0.0)
    yesterday = dates_helper.local_today() - datetime.timedelta(days=1)
    yesterday_data = redshiftapi.api_breakdowns.query(
        ['ad_group_id'],
        {
            'date__lte': yesterday,
            'date__gte': yesterday,
            'ad_group_id': ad_group_ids,
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
    )
    grouped_yesterday_data = {item['ad_group_id']: item for item in yesterday_data}
    for campaign, ad_groups in entities.items():
        cost_key = 'etfm_cost' if campaign.account.uses_bcm_v2 else 'et_cost'
        if campaign.settings.autopilot:
            num_campaigns_on_campaign_ap += 1
            num_ad_groups_on_campaign_ap += len(ad_groups)
            yesterday_spend = Decimal(0.0)
            for ad_group in ad_groups:
                yesterday_spend += Decimal(grouped_yesterday_data.get(ad_group.id, {}).get(cost_key) or 0)
            yesterday_spend_on_campaign_ap += yesterday_spend
            total_budget_on_campaign_ap += campaign_daily_budgets[campaign]
        else:
            for ad_group in ad_groups:
                yesterday_spend = Decimal(grouped_yesterday_data.get(ad_group.id, {}).get(cost_key) or 0)
                if ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                    num_on_budget_ap += 1
                    total_budget_on_budget_ap += ad_group.settings.autopilot_daily_budget
                    yesterday_spend_on_budget_ap += yesterday_spend
                elif ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
                    num_on_cpc_ap += 1
                    yesterday_spend_on_cpc_ap += yesterday_spend

    influx.gauge('automation.autopilot_plus.adgroups_on', num_on_budget_ap, autopilot='budget_autopilot')
    influx.gauge('automation.autopilot_plus.adgroups_on', num_on_cpc_ap, autopilot='cpc_autopilot')
    influx.gauge('automation.autopilot_plus.adgroups_on', num_ad_groups_on_campaign_ap, autopilot='campaign_autopilot')
    influx.gauge('automation.autopilot_plus.campaigns_on', num_campaigns_on_campaign_ap, autopilot='campaign_autopilot')

    influx.gauge('automation.autopilot_plus.spend', total_budget_on_budget_ap,
                 autopilot='budget_autopilot', type='expected')
    influx.gauge('automation.autopilot_plus.spend', total_budget_on_campaign_ap,
                 autopilot='campaign_autopilot', type='expected')

    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_campaign_ap,
                 autopilot='campaign_autopilot', type='yesterday')
    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_budget_ap,
                 autopilot='budget_autopilot', type='yesterday')
    influx.gauge('automation.autopilot_plus.spend', yesterday_spend_on_cpc_ap,
                 autopilot='cpc_autopilot', type='yesterday')


def _report_new_budgets_on_ap_to_influx(entities):
    total_budget_on_campaign_ap = Decimal(0.0)
    total_budget_on_budget_ap = Decimal(0.0)
    total_budget_on_cpc_ap = Decimal(0.0)
    total_budget_on_all_ap = Decimal(0.0)
    num_sources_on_campaign_ap = 0
    num_sources_on_budget_ap = 0
    num_sources_on_cpc_ap = 0
    active = dash.constants.AdGroupSourceSettingsState.ACTIVE
    rtb_as_one_budget_counted_adgroups = set()
    for campaign, ad_groups in entities.items():
        for ad_group, ad_group_sources in ad_groups.items():
            for ad_group_source in ad_group_sources:
                daily_budget = ad_group_source.settings.daily_budget_cc or Decimal('0')
                if (ad_group.settings.b1_sources_group_enabled and
                        ad_group.settings.b1_sources_group_state == active and
                        ad_group_source.source.source_type.type == dash.constants.SourceType.B1):
                    if ad_group.id in rtb_as_one_budget_counted_adgroups:
                        continue
                    daily_budget = ad_group.settings.b1_sources_group_daily_budget or Decimal('0')
                    rtb_as_one_budget_counted_adgroups.add(ad_group.id)
                total_budget_on_all_ap += daily_budget
                if campaign.settings.autopilot:
                    total_budget_on_campaign_ap += daily_budget
                    num_sources_on_campaign_ap += 1
                elif ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                    total_budget_on_budget_ap += daily_budget
                    num_sources_on_budget_ap += 1
                elif ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
                    total_budget_on_cpc_ap += daily_budget
                    num_sources_on_cpc_ap += 1

    influx.gauge('automation.autopilot_plus.spend', total_budget_on_cpc_ap, autopilot='cpc_autopilot', type='actual')
    influx.gauge('automation.autopilot_plus.spend', total_budget_on_budget_ap,
                 autopilot='budget_autopilot', type='actual')
    influx.gauge('automation.autopilot_plus.spend', total_budget_on_campaign_ap,
                 autopilot='campaign_autopilot', type='actual')

    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_cpc_ap, autopilot='cpc_autopilot')
    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_budget_ap, autopilot='budget_autopilot')
    influx.gauge('automation.autopilot_plus.sources_on', num_sources_on_campaign_ap, autopilot='campaign_autopilot')
