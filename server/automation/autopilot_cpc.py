import decimal
import logging

from automation.constants import CpcChangeComment
from automation import autopilot_settings
from dash import cpc_constraints
import dash.constants

logger = logging.getLogger(__name__)


def get_autopilot_cpc_recommendations(ad_group, adgroup_settings, data, budget_changes=None, adjust_rtb_sources=True):
    recommended_changes = {}
    ag_sources = data.keys()
    SourceAllRTB = dash.constants.SourceAllRTB
    adjust_automatic_mode_rtb_cpcs = adjust_rtb_sources and SourceAllRTB in data
    for ag_source in ag_sources:
        source_type = ag_source.source.source_type if ag_source != SourceAllRTB else SourceAllRTB
        if not adjust_rtb_sources and source_type != SourceAllRTB and source_type.type == dash.constants.SourceType.B1:
            continue
        if adjust_rtb_sources and source_type == SourceAllRTB:
            continue

        recommended_changes[ag_source] = {}
        cpc_change_comments = []
        old_cpc_cc = data[ag_source]['old_cpc_cc']

        if not adjust_automatic_mode_rtb_cpcs or (adjust_automatic_mode_rtb_cpcs and
                                                  source_type.type != dash.constants.SourceType.B1):
            proposed_cpc, calculation_comments = calculate_new_autopilot_cpc(
                old_cpc_cc,
                budget_changes[ag_source]['new_budget'] if budget_changes else data[ag_source]['old_budget'],
                data[ag_source]['yesterdays_spend_cc'])
        elif adjust_automatic_mode_rtb_cpcs and source_type.type == dash.constants.SourceType.B1:
            proposed_cpc, calculation_comments = calculate_new_autopilot_cpc_automatic_mode_rtb(
                old_cpc_cc,
                budget_changes[SourceAllRTB]['new_budget'] if budget_changes else data[SourceAllRTB]['old_budget'],
                data[SourceAllRTB]['yesterdays_spend_cc'],
                data[ag_source]['goal_performance'])

        cpc_change_comments += calculation_comments
        max_decimal_places = _get_cpc_max_decimal_places(ag_source.source.source_type.cpc_decimal_places if
                                                         ag_source != SourceAllRTB else SourceAllRTB.DECIMAL_PLACES)
        proposed_cpc = _round_cpc(proposed_cpc, decimal_places=max_decimal_places)
        proposed_cpc = _threshold_ad_group_constraints(proposed_cpc, ad_group, cpc_change_comments,
                                                       max_decimal_places)
        proposed_cpc = _threshold_cpc_constraints(ad_group,
                                                  ag_source.source if ag_source != SourceAllRTB else SourceAllRTB,
                                                  old_cpc_cc, proposed_cpc, cpc_change_comments,
                                                  [s.source if s != SourceAllRTB else SourceAllRTB for s in ag_sources])
        proposed_cpc = _threshold_source_constraints(proposed_cpc, source_type, adgroup_settings, cpc_change_comments)

        new_cpc_cc = proposed_cpc
        cpc_change_not_allowed_comments = set(cpc_change_comments) -\
            set(autopilot_settings.CPC_CHANGE_ALLOWED_COMMENTS)
        if cpc_change_not_allowed_comments:
            cpc_change_comments = cpc_change_not_allowed_comments
            new_cpc_cc = old_cpc_cc

        if isinstance(new_cpc_cc, float):
            logger.warning('Autopilot: CPC value %s was float on ad group %s',
                           str(new_cpc_cc), ad_group)
            new_cpc_cc = decimal.Decimal(new_cpc_cc)

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
            budget_fulfillment_factor = change_interval['bid_cpc_proc_increase']
            new_cpc += current_cpc * budget_fulfillment_factor
            if change_interval['bid_cpc_proc_increase'] == decimal.Decimal('0'):
                return (current_cpc, [CpcChangeComment.OPTIMAL_SPEND])
            new_cpc = _round_cpc(_threshold_cpc_min_change(budget_fulfillment_factor < 0.0, current_cpc, new_cpc))
            break

    return _threshold_autopilot_min_max_cpc(new_cpc, cpc_change_comments)


def calculate_new_autopilot_cpc_automatic_mode_rtb(current_cpc, rtb_daily_budget, rtb_yesterdays_spend, performance):
    underspend_perc = rtb_yesterdays_spend / rtb_daily_budget - 1
    current_cpc, cpc_change_comments = _get_calculate_cpc_comments(current_cpc, rtb_daily_budget, rtb_yesterdays_spend)
    if cpc_change_comments:
        return (current_cpc, cpc_change_comments)

    budget_fulfillment_factor = decimal.Decimal('0.0')
    for change_interval in autopilot_settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if change_interval['underspend_upper_limit'] <= underspend_perc <= change_interval['underspend_lower_limit']:
            budget_fulfillment_factor = change_interval['bid_cpc_proc_increase']
            break

    performance_factor = decimal.Decimal('1.0')
    for change_interval in autopilot_settings.AUTOPILOT_CPC_CHANGE_PERFORMANCE_FACTOR_TABLE:
        if change_interval['performance_upper_limit'] >= performance >= change_interval['performance_lower_limit']:
            performance_factor = change_interval['performance_factor']
            break
    new_cpc = (current_cpc + current_cpc * budget_fulfillment_factor) * performance_factor

    new_cpc = _threshold_cpc_min_change(new_cpc < current_cpc, current_cpc, new_cpc)
    new_cpc = _round_cpc(new_cpc)
    return _threshold_autopilot_min_max_cpc(new_cpc, cpc_change_comments)


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


def _threshold_cpc_constraints(ad_group, source, old_cpc, proposed_cpc, cpc_change_comments, sources):
    new_cpc = proposed_cpc
    if source == dash.constants.SourceAllRTB:
        constrained_cpcs = set()
        for s in sources:
            if s != dash.constants.SourceAllRTB and s.source_type.type == dash.constants.SourceType.B1:
                constrained_cpcs.add(cpc_constraints.adjust_cpc(proposed_cpc, ad_group=ad_group, source=s))
        new_cpc = min(constrained_cpcs) if old_cpc < proposed_cpc else max(constrained_cpcs)
    else:
        new_cpc = cpc_constraints.adjust_cpc(proposed_cpc, ad_group=ad_group, source=source)

    if new_cpc != proposed_cpc:
        cpc_change_comments += [CpcChangeComment.CPC_CONSTRAINT_APPLIED]
    return new_cpc


def _threshold_source_constraints(proposed_cpc, source_type, adgroup_settings, cpc_change_comments):
    min_cpc, max_cpc = _get_source_type_min_max_cpc(source_type, adgroup_settings)
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


def _get_source_type_min_max_cpc(source_type, adgroup_settings):
    if source_type == dash.constants.SourceAllRTB:
        return dash.constants.SourceAllRTB.MIN_CPC, dash.constants.SourceAllRTB.MAX_CPC
    return source_type.get_min_cpc(adgroup_settings), source_type.max_cpc


def _threshold_ad_group_constraints(proposed_cpc, ad_group, cpc_change_comments, max_cpc_decimal_places):
    ag_settings = ad_group.get_current_settings()
    if ag_settings.cpc_cc and proposed_cpc > ag_settings.cpc_cc:
        cpc_change_comments += [CpcChangeComment.OVER_AD_GROUP_MAX_CPC]
        return _round_cpc(ag_settings.cpc_cc, decimal_places=max_cpc_decimal_places, rounding=decimal.ROUND_DOWN)
    return proposed_cpc


def _threshold_cpc_min_change(reducing, current_cpc, new_cpc):
    if reducing:
        return _threshold_reducing_cpc(current_cpc, new_cpc)
    return _threshold_increasing_cpc(current_cpc, new_cpc)


def _threshold_autopilot_min_max_cpc(cpc, cpc_change_comments):
    if autopilot_settings.AUTOPILOT_MIN_CPC > cpc:
        return (autopilot_settings.AUTOPILOT_MIN_CPC, cpc_change_comments +
                [CpcChangeComment.UNDER_AUTOPILOT_MIN_CPC])
    if autopilot_settings.AUTOPILOT_MAX_CPC < cpc:
        return (autopilot_settings.AUTOPILOT_MAX_CPC, cpc_change_comments +
                [CpcChangeComment.OVER_AUTOPILOT_MAX_CPC])
    return (cpc, cpc_change_comments)
