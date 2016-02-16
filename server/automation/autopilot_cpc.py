import decimal
import logging

import automation.helpers
import automation.constants
from automation import autopilot_settings

logger = logging.getLogger(__name__)


def get_autopilot_cpc_recommendations(ad_group, data, budget_ap_changes=None):
    active_sources = data.keys()
    recommended_changes = {}
    for ag_source in active_sources:
        recommended_changes[ag_source] = {}
        cpc_change_comments = []
        daily_budget = data[ag_source]['old_budget']
        if budget_ap_changes:
            daily_budget = budget_ap_changes[ag_source]['new_budget']
        old_cpc_cc = data[ag_source]['old_cpc_cc']
        yesterdays_spend = data[ag_source]['yesterdays_spend_cc']
        underspend_perc = data[ag_source]['spend_perc'] - 1
        #TODO REMOVE COMMENT, THIS SHOULD BE IN PRODUCTION!
        #if not autopilot_helpers.ad_group_source_is_synced(ad_group_source_settings.ad_group_source):
        #    cpc_change_comments.append(automation.constants.CpcChangeComment.OLD_DATA)

        source = ag_source.source
        proposed_cpc, calculation_comments = calculate_new_autopilot_cpc(
            old_cpc_cc,
            underspend_perc,
            daily_budget,
            yesterdays_spend)
        cpc_change_comments += calculation_comments
        cpc_change_comments += _check_source_constraints(proposed_cpc, source)
        cpc_change_comments += _check_ad_group_constraints(proposed_cpc, ad_group)
        new_cpc_cc = proposed_cpc if cpc_change_comments == [] else old_cpc_cc
        recommended_changes[ag_source]['old_cpc_cc'] = old_cpc_cc
        recommended_changes[ag_source]['new_cpc_cc'] = new_cpc_cc
        recommended_changes[ag_source]['cpc_comments'] = cpc_change_comments
    return recommended_changes


def _round_cpc(num):
    return num.quantize(
        decimal.Decimal('0.01'),
        rounding=decimal.ROUND_UP)


def calculate_new_autopilot_cpc(current_cpc, underspend_perc, current_daily_budget, yesterdays_spend):
    cpc_change_comments = _get_calculate_cpc_comments(current_cpc, current_daily_budget, yesterdays_spend)
    if cpc_change_comments:
        return (current_cpc, cpc_change_comments)
    new_cpc = current_cpc
    for change_interval in autopilot_settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if change_interval['underspend_upper_limit'] <= underspend_perc <= change_interval['underspend_lower_limit']:
            new_cpc += current_cpc * change_interval['bid_cpc_proc_increase']
            if change_interval['bid_cpc_proc_increase'] == decimal.Decimal('0'):
                return (current_cpc, [automation.constants.CpcChangeComment.OPTIMAL_SPEND])
            if change_interval['bid_cpc_proc_increase'] < 0:
                new_cpc = _threshold_reducing_cpc(current_cpc, new_cpc)
            else:
                new_cpc = _threshold_increasing_cpc(current_cpc, new_cpc)
            new_cpc = _round_cpc(new_cpc)
            break
    if autopilot_settings.AUTOPILOT_MIN_CPC > new_cpc:
        return (autopilot_settings.AUTOPILOT_MIN_CPC, cpc_change_comments)
    if autopilot_settings.AUTOPILOT_MAX_CPC < new_cpc:
        return (autopilot_settings.AUTOPILOT_MAX_CPC, cpc_change_comments)
    return (new_cpc, cpc_change_comments)


def _get_calculate_cpc_comments(current_cpc, current_daily_budget, yesterdays_spend):
    cpc_change_comments = []
    if current_daily_budget is None or current_daily_budget <= 0:
        cpc_change_comments.append(automation.constants.CpcChangeComment.BUDGET_NOT_SET)
    if current_cpc is None or current_cpc <= 0:
        cpc_change_comments.append(automation.constants.CpcChangeComment.CPC_NOT_SET)
    if current_cpc > autopilot_settings.AUTOPILOT_MAX_CPC:
        cpc_change_comments.append(automation.constants.CpcChangeComment.CURRENT_CPC_TOO_HIGH)
    if current_cpc < autopilot_settings.AUTOPILOT_MIN_CPC:
        cpc_change_comments.append(automation.constants.CpcChangeComment.CURRENT_CPC_TOO_LOW)
    return cpc_change_comments


def _threshold_reducing_cpc(current_cpc, new_cpc):
    cpc_change = abs(current_cpc - new_cpc)
    if cpc_change < autopilot_settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE:
        return current_cpc - autopilot_settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE
    if cpc_change > autopilot_settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE:
        return current_cpc - autopilot_settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE
    return new_cpc


def _threshold_increasing_cpc(current_cpc, new_cpc):
    cpc_change = abs(current_cpc - new_cpc)
    if cpc_change < autopilot_settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE:
        return current_cpc + autopilot_settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE
    if cpc_change > autopilot_settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE:
        return current_cpc + autopilot_settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE
    return new_cpc


def _check_source_constraints(proposed_cpc, source):
    min_cpc = source.source_type.min_cpc
    max_cpc = source.source_type.max_cpc
    if proposed_cpc > max_cpc:
        return [automation.constants.CpcChangeComment.OVER_SOURCE_MAX_CPC]
    if proposed_cpc < min_cpc:
        return [automation.constants.CpcChangeComment.UNDER_SOURCE_MIN_CPC]
    return []


def _check_ad_group_constraints(proposed_cpc, ad_group):
    ag_settings = ad_group.get_current_settings()
    if ag_settings.cpc_cc and proposed_cpc > ag_settings.cpc_cc:
        return [automation.constants.CpcChangeComment.OVER_AD_GROUP_MAX_CPC]
    return []
