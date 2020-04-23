from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence

import automation.models
import automation.rules.constants
import core.features.bid_modifiers.constants
import core.features.goals
import core.models
import dash.constants
import redshiftapi.api_rules
from utils import sort_helper

from ... import constants
from ... import models
from .. import macros


def query_stats(
    target_type: int, rules_map: Dict[core.models.AdGroup, List[models.Rule]]
) -> Dict[int, Dict[str, Dict[str, Dict[int, Optional[float]]]]]:
    ad_groups = list(rules_map.keys())
    raw_stats = redshiftapi.api_rules.query(target_type, ad_groups)
    cpa_ad_groups = _get_cpa_ad_groups(rules_map)
    conversion_stats = redshiftapi.api_rules.query_conversions(target_type, cpa_ad_groups)
    merged_stats = _merge(target_type, cpa_ad_groups, raw_stats, conversion_stats)
    return _format(target_type, merged_stats)


def _get_cpa_ad_groups(rules_map):
    cpa_ad_groups = []
    for ad_group, rules in rules_map.items():
        for rule in rules:
            if ad_group not in cpa_ad_groups and (_has_cpa_operands(rule) or _has_cpa_macros(rule)):
                cpa_ad_groups.append(ad_group)
    return cpa_ad_groups


def _has_cpa_operands(rule):
    for condition in rule.conditions.all():
        if condition.left_operand_type in [
            constants.MetricType.AVG_COST_PER_CONVERSION,
            constants.MetricType.AVG_COST_PER_CONVERSION_VIEW,
            constants.MetricType.AVG_COST_PER_CONVERSION_TOTAL,
        ]:
            return True
    return False


def _has_cpa_macros(rule):
    if rule.action_type == constants.ActionType.SEND_EMAIL:
        if rule.send_email_subject:
            if macros.has_cpa_macros(rule.send_email_subject):
                return True
        if rule.send_email_body:
            if macros.has_cpa_macros(rule.send_email_body):
                return True
    return False


def _merge(target_type, cpa_ad_groups, raw_stats, conversion_stats):
    target_column_keys = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    conversion_stats_by_pixel_breakdown = sort_helper.group_rows_by_breakdown_key(
        target_column_keys + ["slug", "window_key"], conversion_stats
    )
    cpa_ad_groups_map = {ad_group.id: ad_group for ad_group in cpa_ad_groups}
    target_goals_per_campaign = {}

    merged_stats = []
    for row in raw_stats:
        ad_group_id = row["ad_group_id"]
        if ad_group_id not in cpa_ad_groups_map:
            merged_stats.append(row)
            continue

        ad_group = cpa_ad_groups_map[ad_group_id]
        if ad_group.campaign_id not in target_goals_per_campaign:
            target_goals_per_campaign[ad_group.campaign_id] = _get_target_goal(ad_group)

        target_goal = target_goals_per_campaign[ad_group.campaign_id]
        if not target_goal:
            merged_stats.append(row)
            continue

        pixel_rows = conversion_stats_by_pixel_breakdown.get(
            tuple(row[col] for col in target_column_keys) + (target_goal.pixel.slug, row["window_key"])
        )
        merged_stats.append(_merge_row(target_goal, row, pixel_rows))
    return merged_stats


def _merge_row(target_goal, row, pixel_rows):
    merged_row = dict(row)
    if pixel_rows:
        count = sum(x["count"] for x in pixel_rows if x["window"] <= target_goal.conversion_window)
        count_view = sum(x["count_view"] for x in pixel_rows if x["window"] <= target_goal.conversion_window)
        count_total = count + count_view
        local_avg_etfm_cost = float(merged_row["local_etfm_cost"]) / count if count else None
        local_avg_etfm_cost_view = float(merged_row["local_etfm_cost"]) / count_view if count_view else None
        local_avg_etfm_cost_total = float(merged_row["local_etfm_cost"]) / count_total if count_total else None
    else:
        count = None
        count_view = None
        count_total = None
        local_avg_etfm_cost = None
        local_avg_etfm_cost_view = None
        local_avg_etfm_cost_total = None

    merged_row["conversions_click"] = count
    merged_row["conversions_view"] = count_view
    merged_row["conversions_total"] = count_total
    merged_row["local_avg_etfm_cost_per_conversion"] = local_avg_etfm_cost
    merged_row["local_avg_etfm_cost_per_conversion_view"] = local_avg_etfm_cost_view
    merged_row["local_avg_etfm_cost_per_conversion_total"] = local_avg_etfm_cost_total

    return merged_row


def _get_target_goal(ad_group) -> Optional[core.features.goals.ConversionGoal]:
    for goal in ad_group.campaign.campaigngoal_set.all().select_related("conversion_goal__pixel").order_by("-primary"):
        if goal.type == dash.constants.CampaignGoalKPI.CPA:
            return goal.conversion_goal
    return None  # campaign has no cpa goal set


def _format(target_type: int, stats: Sequence[Dict]) -> Dict[int, Dict[str, Dict[str, Dict[int, Optional[float]]]]]:
    target_column_keys = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    formatted_stats: Dict[int, Dict[str, Dict[str, Dict[int, Optional[float]]]]] = {}
    for row in stats:
        ad_group_id = row.pop("ad_group_id", None)
        default_key = ad_group_id if target_type == constants.TargetType.AD_GROUP else None
        target_key_group = tuple(row.pop(t, default_key) for t in target_column_keys)
        window_key = row.pop("window_key", None)

        if (
            not all([ad_group_id, all(target_key_group), window_key])
            or target_key_group[0] in core.features.bid_modifiers.constants.UNSUPPORTED_TARGETS
        ):
            continue

        target_key = "__".join(map(str, target_key_group))

        for metric, value in row.items():
            formatted_stats.setdefault(ad_group_id, {})
            formatted_stats[ad_group_id].setdefault(target_key, {})
            formatted_stats[ad_group_id][target_key].setdefault(metric, {})
            formatted_stats[ad_group_id][target_key][metric][window_key] = value

    return formatted_stats
