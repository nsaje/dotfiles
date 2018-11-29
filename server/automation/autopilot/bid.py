import decimal
import logging

import dash.constants
import dash.models
from dash import cpc_constraints

from . import settings
from .constants import BidChangeComment

logger = logging.getLogger(__name__)


def get_autopilot_bid_recommendations(
    ad_group, data, bcm_modifiers, campaign_goal, budget_changes=None, adjust_rtb_sources=True
):
    recommended_changes = {}
    ag_sources = list(data.keys())
    all_rtb_ad_group_source = _find_all_rtb_ad_group_source(ag_sources)
    adjust_automatic_mode_rtb_bids = adjust_rtb_sources and all_rtb_ad_group_source is not None
    for ag_source in ag_sources:
        source_type = ag_source.source.source_type
        if not adjust_rtb_sources:
            if source_type.type == dash.constants.SourceType.B1:
                continue
            if source_type == dash.models.AllRTBSourceType and not _has_b1_sources(list(data.keys())):
                continue
        if adjust_rtb_sources and source_type == dash.models.AllRTBSourceType:
            continue

        recommended_changes[ag_source] = {}
        bid_change_comments = []
        old_bid = data[ag_source]["old_bid"]

        if not adjust_automatic_mode_rtb_bids or source_type.type != dash.constants.SourceType.B1:
            proposed_bid, calculation_comments = calculate_new_autopilot_bid(
                old_bid,
                budget_changes[ag_source]["new_budget"] if budget_changes else data[ag_source]["old_budget"],
                data[ag_source]["yesterdays_spend_cc"],
                campaign_goal,
                bidding_type=ad_group.bidding_type,
            )
        else:
            proposed_bid, calculation_comments = calculate_new_autopilot_bid_automatic_mode_rtb(
                old_bid,
                budget_changes[all_rtb_ad_group_source]["new_budget"]
                if budget_changes
                else data[all_rtb_ad_group_source]["old_budget"],
                data[all_rtb_ad_group_source]["yesterdays_spend_cc"],
                data[ag_source]["yesterdays_spend_cc"],
                data[ag_source]["goal_performance"],
                campaign_goal,
            )

        bid_change_comments += calculation_comments
        max_decimal_places = _get_bid_max_decimal_places(ag_source.source.source_type.cpc_decimal_places)
        proposed_bid = _round_bid(proposed_bid, decimal_places=max_decimal_places)
        proposed_bid = _threshold_ad_group_constraints(proposed_bid, ad_group, bid_change_comments, max_decimal_places)
        proposed_bid = _threshold_bid_constraints(
            ad_group,
            ag_source.source,
            old_bid,
            proposed_bid,
            bid_change_comments,
            [s.source for s in ag_sources],
            bcm_modifiers,
        )
        proposed_bid = _threshold_source_constraints(
            proposed_bid, source_type, ad_group.settings, bid_change_comments, bcm_modifiers
        )

        new_bid = proposed_bid
        bid_change_not_allowed_comments = set(bid_change_comments) - set(settings.BID_CHANGE_ALLOWED_COMMENTS)
        if bid_change_not_allowed_comments:
            bid_change_comments = bid_change_not_allowed_comments
            new_bid = old_bid

        if isinstance(new_bid, float):
            logger.warning(
                "Autopilot: %s value %s was float on ad group %s",
                "CPM" if ad_group.bidding_type == dash.constants.BiddingType.CPM else "CPC",
                str(new_bid),
                ad_group,
            )
            new_bid = decimal.Decimal(new_bid)

        recommended_changes[ag_source] = {"old_bid": old_bid, "new_bid": new_bid, "bid_comments": bid_change_comments}

    return recommended_changes


def _round_bid(num, decimal_places=settings.AUTOPILOT_BID_MAX_DEC_PLACES, rounding=decimal.ROUND_HALF_UP):
    return num.quantize(pow(10, decimal.Decimal(-decimal_places)), rounding=rounding)


def calculate_new_autopilot_bid(
    current_bid, current_daily_budget, yesterdays_spend, campaign_goal, bidding_type=dash.constants.BiddingType.CPC
):
    underspend_perc = yesterdays_spend / current_daily_budget - 1
    current_bid, bid_change_comments = _get_calculate_bid_comments(
        current_bid, current_daily_budget, yesterdays_spend, bidding_type
    )
    if bid_change_comments:
        return (current_bid, bid_change_comments)

    new_bid = current_bid
    for change_interval in settings.get_autopilot_bid_change_table(bidding_type):
        if change_interval["underspend_upper_limit"] <= underspend_perc <= change_interval["underspend_lower_limit"]:
            budget_fulfillment_factor = change_interval["bid_proc_increase"]
            new_bid += current_bid * budget_fulfillment_factor
            if change_interval["bid_proc_increase"] == decimal.Decimal("0"):
                return (current_bid, [BidChangeComment.OPTIMAL_SPEND])
            new_bid = _threshold_bid_min_change(budget_fulfillment_factor < 0.0, current_bid, new_bid, bidding_type)
            new_bid = _round_bid(new_bid)
            break

    new_bid, bid_change_comments = _threshold_autopilot_min_max_bid(new_bid, bid_change_comments)
    return _threshold_bid_goal(new_bid, bid_change_comments, campaign_goal, bidding_type)


def calculate_new_autopilot_bid_automatic_mode_rtb(
    current_bid,
    rtb_daily_budget,
    rtb_yesterdays_spend,
    source_yesterday_spend,
    performance,
    campaign_goal,
    bidding_type=dash.constants.BiddingType.CPC,
):
    underspend_perc = rtb_yesterdays_spend / rtb_daily_budget - 1
    current_bid, bid_change_comments = _get_calculate_bid_comments(
        current_bid, rtb_daily_budget, rtb_yesterdays_spend, bidding_type
    )
    if bid_change_comments:
        return (current_bid, bid_change_comments)

    budget_fulfillment_factor = decimal.Decimal("0.0")
    for change_interval in settings.get_autopilot_bid_change_table(bidding_type):
        if change_interval["underspend_upper_limit"] <= underspend_perc <= change_interval["underspend_lower_limit"]:
            budget_fulfillment_factor = change_interval["bid_proc_increase"]
            break

    if source_yesterday_spend < settings.get_autopilot_bid_no_spend_threshold(
        bidding_type
    ) and budget_fulfillment_factor < settings.get_autopilot_bid_no_spend_change(bidding_type):
        budget_fulfillment_factor = settings.get_autopilot_bid_no_spend_change(bidding_type)

    performance_factor = decimal.Decimal("1.0")
    for change_interval in settings.get_autopilot_bid_change_performance_factor_table(bidding_type):
        if change_interval["performance_upper_limit"] >= performance >= change_interval["performance_lower_limit"]:
            performance_factor = change_interval["performance_factor"]
            break
    new_bid = (current_bid + current_bid * budget_fulfillment_factor) * performance_factor

    new_bid = _threshold_bid_min_change(new_bid < current_bid, current_bid, new_bid, bidding_type)
    new_bid = _round_bid(new_bid)
    new_bid, bid_change_comments = _threshold_autopilot_min_max_bid(new_bid, bid_change_comments)
    return _threshold_bid_goal(new_bid, bid_change_comments, campaign_goal, bidding_type)


def _get_calculate_bid_comments(current_bid, current_daily_budget, yesterdays_spend, bidding_type):
    max_bid = settings.get_autopilot_max_bid(bidding_type)
    min_bid = settings.get_autopilot_min_bid(bidding_type)

    bid_change_comments = []

    if not current_daily_budget or current_daily_budget <= 0:
        bid_change_comments.append(BidChangeComment.BUDGET_NOT_SET)
    if not current_bid or current_bid <= 0:
        bid_change_comments.append(BidChangeComment.BID_NOT_SET)
    if current_bid > max_bid:
        current_bid = max_bid
        bid_change_comments.append(BidChangeComment.CURRENT_BID_TOO_HIGH)
    if current_bid < min_bid:
        current_bid = min_bid
        bid_change_comments.append(BidChangeComment.CURRENT_BID_TOO_LOW)

    return current_bid, bid_change_comments


def _threshold_bid_constraints(ad_group, source, old_bid, proposed_bid, bid_change_comments, sources, bcm_modifiers):
    # users set min/max CPM on their own
    if ad_group.bidding_type == dash.constants.BiddingType.CPM:
        return proposed_bid

    new_bid = proposed_bid
    if source == dash.models.AllRTBSource:
        constrained_bids = set()
        for s in sources:
            if s != dash.models.AllRTBSource and s.source_type.type == dash.constants.SourceType.B1:
                constrained_bids.add(
                    cpc_constraints.adjust_cpc(proposed_bid, bcm_modifiers, ad_group=ad_group, source=s)
                )
        new_bid = min(constrained_bids) if old_bid < proposed_bid else max(constrained_bids)
    else:
        new_bid = cpc_constraints.adjust_cpc(proposed_bid, bcm_modifiers, ad_group=ad_group, source=source)

    if new_bid != proposed_bid:
        bid_change_comments += [BidChangeComment.BID_CONSTRAINT_APPLIED]
    return new_bid


def _threshold_source_constraints(proposed_bid, source_type, adgroup_settings, bid_change_comments, bcm_modifiers):
    min_bid, max_bid = _get_source_type_min_max_bid(source_type, adgroup_settings, bcm_modifiers)
    if proposed_bid > max_bid:
        bid_change_comments += [BidChangeComment.OVER_SOURCE_MAX_BID]
        return max_bid
    if proposed_bid < min_bid:
        bid_change_comments += [BidChangeComment.UNDER_SOURCE_MIN_BID]
        return min_bid
    return proposed_bid


def _get_bid_max_decimal_places(source_dec_places):
    return (
        min(source_dec_places, settings.AUTOPILOT_BID_MAX_DEC_PLACES)
        if source_dec_places
        else settings.AUTOPILOT_BID_MAX_DEC_PLACES
    )


def _get_source_type_min_max_bid(source_type, adgroup_settings, bcm_modifiers):
    if adgroup_settings.ad_group.bidding_type == dash.constants.BiddingType.CPM:
        min_bid = source_type.get_min_cpm(adgroup_settings, bcm_modifiers)
        max_bid = source_type.get_etfm_max_cpm(bcm_modifiers)
    else:
        min_bid = source_type.get_min_cpc(adgroup_settings, bcm_modifiers)
        max_bid = source_type.get_etfm_max_cpc(bcm_modifiers)
    return min_bid, max_bid


def _threshold_ad_group_constraints(proposed_bid, ad_group, bid_change_comments, max_bid_decimal_places):
    ag_settings = ad_group.get_current_settings()
    ag_max_bid = ag_settings.max_cpm if ad_group.bidding_type == dash.constants.BiddingType.CPM else ag_settings.cpc_cc

    if ag_max_bid and proposed_bid > ag_max_bid:
        bid_change_comments += [BidChangeComment.OVER_AD_GROUP_MAX_BID]
        return _round_bid(ag_max_bid, decimal_places=max_bid_decimal_places, rounding=decimal.ROUND_DOWN)
    return proposed_bid


def _threshold_bid_min_change(reducing, current_bid, new_bid, bidding_type):
    if reducing:
        return _threshold_reducing_bid(current_bid, new_bid, bidding_type)
    return _threshold_increasing_bid(current_bid, new_bid, bidding_type)


def _threshold_reducing_bid(current_bid, new_bid, bidding_type):
    min_reducing_change = settings.get_autopilot_min_reducing_bid_change(bidding_type)
    max_reducing_change = settings.get_autopilot_max_reducing_bid_change(bidding_type)

    bid_change = abs(current_bid - new_bid)
    if bid_change < min_reducing_change:
        return current_bid - min_reducing_change
    if bid_change > max_reducing_change:
        return current_bid - max_reducing_change
    return new_bid


def _threshold_increasing_bid(current_bid, new_bid, bidding_type):
    min_increasing_change = settings.get_autopilot_min_increasing_bid_change(bidding_type)
    max_increasing_change = settings.get_autopilot_max_increasing_bid_change(bidding_type)

    bid_change = abs(current_bid - new_bid)
    if bid_change < min_increasing_change:
        return current_bid + min_increasing_change
    if bid_change > max_increasing_change:
        return current_bid + max_increasing_change
    return new_bid


def _threshold_bid_goal(bid, bid_change_comments, campaign_goal, bidding_type):
    goal = campaign_goal.get("goal")
    if goal and goal.type == dash.constants.CampaignGoalKPI.CPC and bidding_type == dash.constants.BiddingType.CPC:
        min_bid = campaign_goal["value"] * settings.BID_GOAL_THRESHOLD
        if bid < min_bid:
            return (min_bid, bid_change_comments + [BidChangeComment.UNDER_GOAL_BID])
    return (bid, bid_change_comments)


def _threshold_autopilot_min_max_bid(bid, bid_change_comments, bidding_type=dash.constants.BiddingType.CPC):
    min_autopilot_bid = settings.get_autopilot_min_bid(bidding_type)
    max_autopilot_bid = settings.get_autopilot_max_bid(bidding_type)
    if min_autopilot_bid > bid:
        return (min_autopilot_bid, bid_change_comments + [BidChangeComment.UNDER_AUTOPILOT_MIN_BID])
    if max_autopilot_bid < bid:
        return (max_autopilot_bid, bid_change_comments + [BidChangeComment.OVER_AUTOPILOT_MAX_BID])
    return (bid, bid_change_comments)


def _find_all_rtb_ad_group_source(ad_group_sources):
    for ags in ad_group_sources:
        if ags.source == dash.models.AllRTBSource:
            return ags
    return None


def _has_b1_sources(ad_group_sources):
    for ags in ad_group_sources:
        if ags.source.source_type.type == dash.constants.SourceType.B1:
            return True
    return False
