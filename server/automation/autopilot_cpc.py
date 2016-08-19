import decimal
import logging

from automation.constants import CpcChangeComment
from dash.constants import SourceType
from automation import autopilot_settings

logger = logging.getLogger(__name__)

ACCOUNT_SOURCE_CPC_CONSTRAINTS = {
    # King Content - Cisco
    (324, SourceType.OUTBRAIN): (decimal.Decimal('0.65'), None),
}


def get_autopilot_cpc_recommendations(ad_group, data, budget_changes=None):
    active_sources = data.keys()
    recommended_changes = {}
    for ag_source in active_sources:
        recommended_changes[ag_source] = {}
        cpc_change_comments = []
        daily_budget = budget_changes[ag_source]['new_budget'] if budget_changes else data[ag_source]['old_budget']
        old_cpc_cc = data[ag_source]['old_cpc_cc']
        yesterdays_spend = data[ag_source]['yesterdays_spend_cc']

        proposed_cpc, calculation_comments = calculate_new_autopilot_cpc(
            old_cpc_cc,
            daily_budget,
            yesterdays_spend)
        cpc_change_comments += calculation_comments
        source_type = ag_source.source.source_type
        max_decimal_places = _get_cpc_max_decimal_places(source_type.cpc_decimal_places)
        proposed_cpc = _round_cpc(proposed_cpc, decimal_places=max_decimal_places)
        proposed_cpc = _threshold_ad_group_constraints(proposed_cpc, ad_group, cpc_change_comments,
                                                       max_decimal_places)
        proposed_cpc = _threshold_source_constraints(proposed_cpc, source_type, cpc_change_comments)
        proposed_cpc = _threshold_account_source_constraints(ad_group.campaign.account_id,
                                                             proposed_cpc,
                                                             source_type,
                                                             cpc_change_comments)
        new_cpc_cc = proposed_cpc
        cpc_change_not_allowed_comments = set(cpc_change_comments) -\
            set(autopilot_settings.CPC_CHANGE_ALLOWED_COMMENTS)
        if cpc_change_not_allowed_comments:
            cpc_change_comments = cpc_change_not_allowed_comments
            new_cpc_cc = old_cpc_cc

        recommended_changes[ag_source] = {
            'old_cpc_cc': old_cpc_cc,
            'new_cpc_cc': new_cpc_cc,
            'cpc_comments': cpc_change_comments
        }
    return recommended_changes


def _round_cpc(num, decimal_places=autopilot_settings.AUTOPILOT_CPC_MAX_DEC_PLACES, rounding=decimal.ROUND_HALF_UP):
    return num.quantize(
        pow(10, decimal.Decimal(-decimal_places)),
        rounding=rounding)


def calculate_new_autopilot_cpc(current_cpc, current_daily_budget, yesterdays_spend):
    underspend_perc = yesterdays_spend / current_daily_budget - 1
    current_cpc, cpc_change_comments = _get_calculate_cpc_comments(current_cpc, current_daily_budget, yesterdays_spend)
    if cpc_change_comments:
        return (current_cpc, cpc_change_comments)
    new_cpc = current_cpc
    for change_interval in autopilot_settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if change_interval['underspend_upper_limit'] <= underspend_perc <= change_interval['underspend_lower_limit']:
            new_cpc += current_cpc * change_interval['bid_cpc_proc_increase']
            if change_interval['bid_cpc_proc_increase'] == decimal.Decimal('0'):
                return (current_cpc, [CpcChangeComment.OPTIMAL_SPEND])
            if change_interval['bid_cpc_proc_increase'] < 0:
                new_cpc = _threshold_reducing_cpc(current_cpc, new_cpc)
            else:
                new_cpc = _threshold_increasing_cpc(current_cpc, new_cpc)
            new_cpc = _round_cpc(new_cpc)
            break
    if autopilot_settings.AUTOPILOT_MIN_CPC > new_cpc:
        return (autopilot_settings.AUTOPILOT_MIN_CPC, cpc_change_comments +
                [CpcChangeComment.UNDER_AUTOPILOT_MIN_CPC])
    if autopilot_settings.AUTOPILOT_MAX_CPC < new_cpc:
        return (autopilot_settings.AUTOPILOT_MAX_CPC, cpc_change_comments +
                [CpcChangeComment.OVER_AUTOPILOT_MAX_CPC])
    return (new_cpc, cpc_change_comments)


def _get_calculate_cpc_comments(current_cpc, current_daily_budget, yesterdays_spend):
    cpc_change_comments = []
    if not current_daily_budget or current_daily_budget <= 0:
        cpc_change_comments.append(CpcChangeComment.BUDGET_NOT_SET)
    if not current_cpc or current_cpc <= 0:
        cpc_change_comments.append(CpcChangeComment.CPC_NOT_SET)
    if current_cpc > autopilot_settings.AUTOPILOT_MAX_CPC:
        current_cpc = autopilot_settings.AUTOPILOT_MAX_CPC
        cpc_change_comments.append(CpcChangeComment.CURRENT_CPC_TOO_HIGH)
    if current_cpc < autopilot_settings.AUTOPILOT_MIN_CPC:
        current_cpc = autopilot_settings.AUTOPILOT_MIN_CPC
        cpc_change_comments.append(CpcChangeComment.CURRENT_CPC_TOO_LOW)
    return current_cpc, cpc_change_comments


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


def _threshold_account_source_constraints(account_id, proposed_cpc, source_type, cpc_change_comments):
    if (account_id, source_type.type) not in ACCOUNT_SOURCE_CPC_CONSTRAINTS:
        return proposed_cpc

    min_cpc, max_cpc = ACCOUNT_SOURCE_CPC_CONSTRAINTS[(account_id, source_type.type)]
    if max_cpc and proposed_cpc > max_cpc:
        cpc_change_comments += [CpcChangeComment.OVER_ACCOUNT_SOURCE_MIN_CPC]
        return max_cpc
    if min_cpc and proposed_cpc < min_cpc:
        cpc_change_comments += [CpcChangeComment.UNDER_ACCOUNT_SOURCE_MIN_CPC]
        return min_cpc
    return proposed_cpc


def _threshold_source_constraints(proposed_cpc, source_type, cpc_change_comments):
    min_cpc, max_cpc = _get_source_type_min_max_cpc(source_type)
    if proposed_cpc > max_cpc:
        cpc_change_comments += [CpcChangeComment.OVER_SOURCE_MAX_CPC]
        return max_cpc
    if proposed_cpc < min_cpc:
        cpc_change_comments += [CpcChangeComment.UNDER_SOURCE_MIN_CPC]
        return min_cpc
    return proposed_cpc


def _get_cpc_max_decimal_places(source_dec_places):
    return min(source_dec_places, autopilot_settings.AUTOPILOT_CPC_MAX_DEC_PLACES) if source_dec_places else\
        autopilot_settings.AUTOPILOT_CPC_MAX_DEC_PLACES


def _get_source_type_min_max_cpc(source_type):
    return source_type.min_cpc, source_type.max_cpc


def _threshold_ad_group_constraints(proposed_cpc, ad_group, cpc_change_comments, max_cpc_decimal_places):
    ag_settings = ad_group.get_current_settings()
    if ag_settings.cpc_cc and proposed_cpc > ag_settings.cpc_cc:
        cpc_change_comments += [CpcChangeComment.OVER_AD_GROUP_MAX_CPC]
        return _round_cpc(ag_settings.cpc_cc, decimal_places=max_cpc_decimal_places, rounding=decimal.ROUND_DOWN)
    return proposed_cpc
