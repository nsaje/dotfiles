import dataclasses
import datetime
import decimal
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union

from django.db import transaction

import core.features.bid_modifiers
import core.features.goals
import core.models
import utils.dates_helper
import utils.exc
import utils.metrics_compat

from .. import config
from .. import constants
from .. import models
from . import actions
from . import exceptions
from . import helpers
from .actions import ValueChangeData

ACTION_TYPE_APPLY_FN_MAPPING = {
    constants.ActionType.INCREASE_BID: actions.adjust_bid,
    constants.ActionType.DECREASE_BID: actions.adjust_bid,
    constants.ActionType.INCREASE_BUDGET: actions.adjust_autopilot_daily_budget,
    constants.ActionType.DECREASE_BUDGET: actions.adjust_autopilot_daily_budget,
    constants.ActionType.INCREASE_BID_MODIFIER: actions.adjust_bid_modifier,
    constants.ActionType.DECREASE_BID_MODIFIER: actions.adjust_bid_modifier,
    constants.ActionType.SEND_EMAIL: actions.send_email,
    constants.ActionType.TURN_OFF: actions.turn_off,
    constants.ActionType.BLACKLIST: actions.blacklist,
    constants.ActionType.ADD_TO_PUBLISHER_GROUP: actions.add_to_publisher_group,
}


@dataclasses.dataclass
class ConditionValues:
    left_operand_value: Union[str, float]
    right_operand_value: Union[str, float]

    def to_dict(self) -> Dict[str, Optional[Union[str, float]]]:
        return {"left_operand_value": self.left_operand_value, "right_operand_value": self.right_operand_value}


@utils.metrics_compat.timer("automation.rules.apply_rule")
@transaction.atomic
def apply_rule(
    rule: models.Rule,
    ad_group: core.models.AdGroup,
    ad_group_stats: Union[Dict[str, Dict[str, Dict[int, Any]]], Dict],
    ad_group_settings: Dict[str, Union[int, str]],
    content_ads_settings: Dict[int, Dict[str, Union[int, str]]],
    campaign_budget: Dict[str, Any],
    cpa_goal: Optional[core.features.goals.CampaignGoal],
) -> Tuple[Sequence[ValueChangeData], Dict[str, Dict[str, ConditionValues]]]:

    if rule.archived:
        raise exceptions.RuleArchived("Archived rule can not be executed.")

    helpers.ensure_ad_group_valid(rule, ad_group)

    changes = []
    per_target_condition_values = {}
    targets_on_cooldown = _prefetch_targets_on_cooldown(rule, ad_group)
    updates_count = 0
    for target, target_stats in ad_group_stats.items():
        if target in targets_on_cooldown:
            continue

        settings_dict = _construct_target_settings_dict(
            rule, ad_group, target, campaign_budget, ad_group_settings, content_ads_settings
        )
        try:
            values_by_condition = _compute_values_by_condition(rule, target_stats, settings_dict, cpa_goal)
            if _meets_all_conditions(values_by_condition):
                updates_count += 1
                update = _apply_action(target, rule, ad_group, target_stats)
                if update.has_changes():
                    _write_trigger_history(target, rule, ad_group)
                    changes.append(update)
                    per_target_condition_values[target] = {
                        str(condition.id): ConditionValues(left_operand_value=value[0], right_operand_value=value[1])
                        for condition, value in values_by_condition.items()
                    }
        except utils.exc.EntityArchivedError:
            continue

    utils.metrics_compat.incr("automation.rules.apply_rule.target_count", len(ad_group_stats), rule_id=rule.id)
    utils.metrics_compat.incr("automation.rules.apply_rule.update_count", updates_count, rule_id=rule.id)
    return changes, per_target_condition_values


def _prefetch_targets_on_cooldown(rule: models.Rule, ad_group: core.models.AdGroup) -> Set[str]:
    # NOTE: this function assumes rules are run daily. If a rule has 24h cooldown, it should
    # trigger after 23h as well if it's a new date. This is done to account for the job not
    # running at exact same time every day because of materialization. It does not support
    # running rules hourly.
    assert rule.cooldown % 24 == 0, "Support for hourly cooldowns not implemented yet"

    days_to_check = (rule.cooldown // 24) - 1

    local_midnight = utils.dates_helper.get_midnight(utils.dates_helper.local_now())
    local_from_dt = local_midnight - datetime.timedelta(days=days_to_check)
    utc_from_dt = utils.dates_helper.local_to_utc_time(local_from_dt)

    return set(
        models.RuleTriggerHistory.objects.filter(
            rule=rule, ad_group=ad_group, triggered_dt__gte=utc_from_dt
        ).values_list("target", flat=True)
    )


def _construct_target_settings_dict(
    rule: models.Rule,
    ad_group: core.models.AdGroup,
    target: str,
    campaign_budget: Dict[str, Any],
    ad_group_settings: Dict[str, Union[int, str]],
    content_ads_settings: Dict[int, Dict[str, Union[int, str]]],
) -> Dict[str, Union[int, str]]:
    settings_dict = {}
    settings_dict.update(campaign_budget)
    settings_dict.update(ad_group_settings)
    if rule.target_type == constants.TargetType.AD:
        content_ad_settings: Dict[str, Union[int, str]] = content_ads_settings.get(int(target), {})
        settings_dict.update(content_ad_settings)
    return settings_dict


def _compute_values_by_condition(
    rule: models.Rule,
    target_stats: Dict[str, Dict[int, Any]],
    settings_dict: Dict[str, Union[int, str]],
    cpa_goal: Optional[core.features.goals.CampaignGoal],
):
    values_by_condition = {}
    for condition in rule.conditions.all():
        left_operand_value, right_operand_value = _prepare_operands(
            rule, condition, target_stats, settings_dict, cpa_goal
        )
        values_by_condition[condition] = left_operand_value, right_operand_value
    return values_by_condition


def _meets_all_conditions(values_by_condition) -> bool:
    for condition, condition_values in values_by_condition.items():
        left_operand_value, right_operand_value = condition_values
        if not _meets_condition(condition.operator, left_operand_value, right_operand_value):
            return False
    return True


def _prepare_operands(
    rule: models.Rule,
    condition: models.RuleCondition,
    target_stats: Dict[str, Dict[int, Any]],
    settings_dict: Dict[str, Union[int, str]],
    cpa_goal: Optional[core.features.goals.CampaignGoal],
):
    _validate_condition(condition)
    if (
        condition.left_operand_type in constants.METRIC_STATS_MAPPING
        or condition.left_operand_type in constants.METRIC_CONVERSIONS_MAPPING
    ):
        return _prepare_stats_operands(rule, condition, target_stats, cpa_goal)
    elif condition.left_operand_type in constants.METRIC_SETTINGS_MAPPING:
        return _prepare_settings_operands(condition, settings_dict)

    raise ValueError("Invalid condition type")


def _validate_condition(condition):
    if (
        condition.left_operand_type not in config.VALID_OPERATORS
        or condition.operator not in config.VALID_OPERATORS[condition.left_operand_type]
    ):
        raise ValueError("Invalid operator for left operand")


def _prepare_stats_operands(
    rule: models.Rule,
    condition: models.RuleCondition,
    target_stats: Dict[str, Dict[int, Any]],
    cpa_goal: Optional[core.features.goals.CampaignGoal],
):
    left_operand_value = _prepare_left_stat_operand(rule, condition, target_stats, cpa_goal)
    right_operand_value = _prepare_right_stat_operand(rule, condition, target_stats)
    return left_operand_value, right_operand_value


def _prepare_left_stat_operand(
    rule: models.Rule,
    condition: models.RuleCondition,
    target_stats: Dict[str, Dict[int, Any]],
    cpa_goal: Optional[core.features.goals.CampaignGoal],
):
    if condition.left_operand_type in constants.METRIC_CONVERSIONS_MAPPING:
        return _prepare_left_stat_operand_conversions(rule, condition, target_stats, cpa_goal)
    left_operand_key = constants.METRIC_STATS_MAPPING[condition.left_operand_type]
    window = condition.left_operand_window or rule.window
    left_operand_stat_value = target_stats[left_operand_key].get(window)
    if left_operand_stat_value is None:
        left_operand_stat_value = config.STATS_FIELDS_DEFAULTS[condition.left_operand_type]
    if left_operand_stat_value is None:
        return left_operand_stat_value
    left_operand_modifier = condition.left_operand_modifier or 1.0
    return left_operand_stat_value * left_operand_modifier


def _prepare_left_stat_operand_conversions(
    rule: models.Rule,
    condition: models.RuleCondition,
    target_stats: Dict[str, Dict[int, Any]],
    cpa_goal: Optional[core.features.goals.CampaignGoal],
):
    attribution = condition.conversion_pixel_attribution
    conversion_window = condition.conversion_pixel_window
    if condition.conversion_pixel is None:
        if cpa_goal is None:
            raise exceptions.NoCPAGoal(
                "Conversion pixel could not be determined from campaign goals - no CPA goal is set on the ad group’s campaign"
            )
        # NOTE: the exact conversion pixel is determined during prefetch
        slug = cpa_goal.conversion_goal.pixel.slug
        if not conversion_window:
            conversion_window = cpa_goal.conversion_goal.conversion_window
        if not attribution:
            # NOTE: using default since campaign goal doesn't contain this information yet
            attribution = constants.ConversionAttributionType.CLICK
    else:
        slug = condition.conversion_pixel.slug
    metric_key_prefix = constants.METRIC_CONVERSIONS_MAPPING[condition.left_operand_type]
    metric_key_suffix = constants.METRIC_CONVERSIONS_SUFFIX[attribution]
    metric_key = metric_key_prefix + metric_key_suffix
    conversion_stats = target_stats.get("conversions", {})
    condition_window = condition.left_operand_window or rule.window
    value = conversion_stats.get(condition_window, {}).get(slug, {}).get(conversion_window, {}).get(metric_key)
    if value is None:
        value = config.CONVERSION_FIELDS_DEFAULTS[condition.left_operand_type]
    return value


def _prepare_right_stat_operand(
    rule: models.Rule, condition: models.RuleCondition, target_stats: Dict[str, Dict[int, Any]]
):
    # TODO: handle constants
    if condition.right_operand_type == constants.ValueType.ABSOLUTE:
        return float(condition.right_operand_value)
    elif condition.right_operand_type in constants.VALUE_STATS_MAPPING:
        right_operand_key = constants.VALUE_STATS_MAPPING[condition.right_operand_type]
        right_operand_window = condition.right_operand_window or rule.window
        right_operand_stat_value = target_stats[right_operand_key][right_operand_window]
        if right_operand_stat_value is None:
            return right_operand_stat_value
        try:
            right_operand_modifier = float(condition.right_operand_value)
        except ValueError:
            right_operand_modifier = 1.0
        return right_operand_stat_value * right_operand_modifier
    raise ValueError("Invalid right operand")


def _prepare_settings_operands(condition, settings_dict):
    assert condition.right_operand_type in [
        constants.ValueType.ABSOLUTE,
        constants.ValueType.CONSTANT,
    ]  # TODO: support remaining right operand types
    field_name = constants.METRIC_SETTINGS_MAPPING[condition.left_operand_type]
    left_value = _get_settings_field(field_name, settings_dict)
    right_value = condition.right_operand_value
    if condition.left_operand_type in config.INT_OPERANDS:
        right_value = int(right_value)
    if condition.left_operand_type in config.FLOAT_OPERANDS:
        right_value = float(right_value)
    elif condition.left_operand_type in config.DATE_OPERANDS:
        right_value = datetime.date.fromisoformat(right_value)
        if condition.left_operand_modifier:
            left_value += datetime.timedelta(days=condition.left_operand_modifier)
    elif condition.left_operand_type in config.DECIMAL_OPERANDS:
        right_value = decimal.Decimal(right_value)
    return left_value, right_value


def _get_settings_field(field_name, settings_dict):
    ad_group_end_date_field = constants.METRIC_SETTINGS_MAPPING[constants.MetricType.AD_GROUP_END_DATE]
    if field_name == ad_group_end_date_field:
        if settings_dict[ad_group_end_date_field] is None:
            campaign_budget_end_date_field = constants.METRIC_SETTINGS_MAPPING[
                constants.MetricType.CAMPAIGN_BUDGET_END_DATE
            ]
            return settings_dict[campaign_budget_end_date_field]
    return settings_dict[field_name]


def _meets_condition(operator: int, left_value, right_value) -> bool:
    if left_value is None or right_value is None:
        return False
    if operator == constants.Operator.EQUALS:
        return left_value == right_value
    if operator == constants.Operator.NOT_EQUALS:
        return left_value != right_value
    if operator == constants.Operator.LESS_THAN:
        return left_value < right_value
    if operator == constants.Operator.GREATER_THAN:
        return left_value > right_value
    if operator == constants.Operator.CONTAINS:
        return right_value in left_value
    if operator == constants.Operator.NOT_CONTAINS:
        return right_value not in left_value
    if operator == constants.Operator.STARTS_WITH:
        return left_value.startswith(right_value)
    if operator == constants.Operator.ENDS_WITH:
        return left_value.endswith(right_value)
    raise ValueError("Invalid operator type")


def _apply_action(target, rule, ad_group, target_stats):
    apply_fn = ACTION_TYPE_APPLY_FN_MAPPING[rule.action_type]
    return apply_fn(target, rule, ad_group, target_stats=target_stats)


def _write_trigger_history(target: str, rule: models.Rule, ad_group: core.models.AdGroup) -> None:
    models.RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target=target)
