import datetime
from decimal import Decimal
from django.db import transaction
import logging
import traceback

import dash
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
from utils.statsd_helper import statsd_gauge
from utils import dates_helper

logger = logging.getLogger(__name__)


def run_autopilot(ad_groups=None, adjust_cpcs=True, adjust_budgets=True, initialization=False):
    if not ad_groups:
        ad_groups_on_ap, ad_group_settings_on_ap = autopilot_helpers.get_active_ad_groups_on_autopilot()
    else:
        ad_groups_on_ap = dash.models.AdGroup.objects.filter(id__in=ad_groups)
        ad_group_settings_on_ap = dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_groups_on_ap).\
            group_current_settings().select_related('ad_group')
    data = prefetch_autopilot_data(ad_groups_on_ap)
    email_changes_data = {}

    for adg_settings in ad_group_settings_on_ap:
        adg = adg_settings.ad_group
        budget_changes = {}
        cpc_changes = {}
        if adjust_budgets and adg_settings.autopilot_state == AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            budget_changes = autopilot_budgets.\
                get_autopilot_daily_budget_recommendations(adg, adg_settings.autopilot_daily_budget, data[adg])
        if adjust_cpcs:
            cpc_changes = autopilot_cpc.get_autopilot_cpc_recommendations(adg, data[adg], budget_changes=budget_changes)
        try:
            with transaction.atomic():
                set_autopilot_changes(cpc_changes, budget_changes)
                persist_autopilot_changes_to_log(cpc_changes, budget_changes, data[adg], adg_settings.autopilot_state)
            email_changes_data = _get_autopilot_campaign_changes_data(
                adg, email_changes_data, cpc_changes, budget_changes)
        except Exception as e:
            _report_autopilot_exception(adg, e)

    autopilot_helpers.send_autopilot_changes_emails(email_changes_data, data, initialization)

    # TODO Report to statsd.


def initialize_budget_autopilot_on_ad_group(ad_group):
    paused_ad_group_sources = _get_autopilot_active_sources_settings([ad_group], AdGroupSettingsState.INACTIVE)
    new_budgets = {}
    data = {}
    for ag_source_setting in paused_ad_group_sources:
        ag_source = ag_source_setting.ad_group_source
        new_budgets[ag_source] = {
            'old_budget': ag_source_setting.daily_budget_cc,
            'new_budget': max(autopilot_settings.MIN_SOURCE_BUDGET, ag_source.source.source_type.min_daily_budget),
            'budget_comments': [automation.constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE]
        }
        data[ag_source] = {
            'old_cpc_cc': ag_source_setting.cpc_cc,
            'old_budget': ag_source_setting.daily_budget_cc,
            'yesterdays_spend_cc': None,
            'yesterdays_clicks': None
        }
    try:
        with transaction.atomic():
            set_autopilot_changes({}, new_budgets)
            persist_autopilot_changes_to_log({}, new_budgets, data, AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
    except Exception as e:
        _report_autopilot_exception(ad_group, e)
    run_autopilot(ad_groups=[ad_group.id], adjust_cpcs=False, adjust_budgets=True, initialization=True)


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


def persist_autopilot_changes_to_log(cpc_changes, budget_changes, data, autopilot_state):
    for ag_source in data.keys():
        old_budget = data[ag_source]['old_budget']
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
            cpc_comments=', '.join(automation.constants.CpcChangeComment.get_text(comment) for comment in
                                   cpc_changes[ag_source]['cpc_comments']) if cpc_changes else '',
            budget_comments=', '.join(automation.constants.DailyBudgetChangeComment.get_text(c) for c in
                                      budget_changes[ag_source]['budget_comments']) if budget_changes else ''
        ).save()


def set_autopilot_changes(cpc_changes={}, budget_changes={}):
    for ag_source in set(cpc_changes.keys() + budget_changes.keys()):
        changes = {}
        if cpc_changes and cpc_changes[ag_source]['old_cpc_cc'] != cpc_changes[ag_source]['new_cpc_cc']:
            changes['cpc_cc'] = cpc_changes[ag_source]['new_cpc_cc']
        if budget_changes and budget_changes[ag_source]['old_budget'] != budget_changes[ag_source]['new_budget']:
            changes['daily_budget_cc'] = budget_changes[ag_source]['new_budget']
        if changes:
            autopilot_helpers.update_ad_group_source_values(ag_source, changes)


def prefetch_autopilot_data(ad_groups):
    enabled_ag_sources_settings = _get_autopilot_active_sources_settings(ad_groups)
    sources = [s.ad_group_source.source.id for s in enabled_ag_sources_settings]
    yesterday_data, days_ago_data, campaign_goals = _fetch_data(ad_groups, sources)
    data = {}
    for source_setting in enabled_ag_sources_settings:
        ag_source = source_setting.ad_group_source
        adg = ag_source.ad_group
        columns = autopilot_settings.GOALS_COLUMNS.get(campaign_goals.get(adg.campaign))
        row, yesterdays_spend_cc, yesterdays_clicks = _find_corresponding_source_data(
            ag_source, days_ago_data, yesterday_data)
        if adg not in data:
            data[adg] = {}
        data[adg][ag_source] = {}
        spend_perc = yesterdays_spend_cc / max(source_setting.daily_budget_cc, autopilot_settings.MIN_SOURCE_BUDGET)
        data[adg][ag_source]['spend_perc'] = spend_perc if spend_perc else Decimal('0')
        data[adg][ag_source]['yesterdays_spend_cc'] = yesterdays_spend_cc
        data[adg][ag_source]['yesterdays_clicks'] = yesterdays_clicks
        data[adg][ag_source]['old_budget'] = source_setting.daily_budget_cc
        data[adg][ag_source]['old_cpc_cc'] = source_setting.cpc_cc
        for col in columns:
            if col == 'spend_perc':
                continue
            data[adg][ag_source][col] = autopilot_settings.GOALS_WORST_VALUE.get(col)
            if col in row and row[col]:
                data[adg][ag_source][col] = row[col]
    return data


def _get_autopilot_active_sources_settings(ad_groups, ad_group_setting_state=AdGroupSettingsState.ACTIVE):
    ag_sources = dash.views.helpers.get_active_ad_group_sources(dash.models.AdGroup, ad_groups)
    ag_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source_id__in=ag_sources).group_current_settings().select_related('ad_group_source__source')
    if ad_group_setting_state:
        return [ag_source_setting for ag_source_setting in ag_sources_settings if
                ag_source_setting.state == ad_group_setting_state]
    return ag_sources_settings


def _fetch_data(ad_groups, sources):
    today = dates_helper.local_today()
    yesterday = today - datetime.timedelta(days=1)
    days_ago = yesterday - datetime.timedelta(days=autopilot_settings.AUTOPILOT_DATA_LOOKBACK_DAYS)

    yesterday_data = reports.api_contentads.query(
        yesterday,
        yesterday,
        breakdown=['ad_group', 'source'],
        ad_group=ad_groups,
        source=sources
    )

    days_ago_data = reports.api_contentads.query(
        days_ago,
        yesterday,
        breakdown=['ad_group', 'source'],
        ad_group=ad_groups,
        source=sources
    )

    campaign_goals = _get_autopilot_campaigns_goals(ad_groups)

    return yesterday_data, days_ago_data, campaign_goals


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
            yesterdays_spend_cc = Decimal(r.get('billing_cost'))
            yesterdays_clicks = r.get('clicks')
            break
    return row, yesterdays_spend_cc, yesterdays_clicks


def _get_autopilot_campaigns_goals(ad_groups):
    # TODO When Campaign Goals Epic Finishes
    goals = {}
    for adg in ad_groups:
        if adg.campaign not in goals:
            goals[adg.campaign] = 'bounce_and_spend'
    return goals


def _report_autopilot_exception(adg, e):
    logger.exception(u'Autopilot failed operating on ad group {}-{} because an exception was raised: {}'.format(
                     adg,
                     str(adg.id),
                     traceback.format_exc(e)))
    desc = {
        'ad_group': adg.id
    }
    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
        incident_key='automation_autopilot_error',
        description=u'Autopilot failed operating on ad group because an exception was raised: {}'.format(
            traceback.format_exc(e)),
        details=desc
    )
