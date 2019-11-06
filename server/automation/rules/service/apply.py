import datetime
from typing import DefaultDict
from typing import Dict
from typing import Union

from django.db import transaction

import core.features.bid_modifiers
import core.models
import utils.dates_helper

from .. import Rule
from .. import RuleTriggerHistory
from .. import constants
from . import actions

ACTION_TYPE_APPLY_FN_MAPPING = {
    constants.ActionType.INCREASE_BID_MODIFIER: actions.adjust_bid_modifier,
    constants.ActionType.DECREASE_BID_MODIFIER: actions.adjust_bid_modifier,
}


def apply_rule(
    rule: Rule,
    ad_group: core.models.AdGroup,
    ad_group_stats: Union[DefaultDict[str, DefaultDict[str, DefaultDict[int, Union[None, int, float]]]], Dict],
) -> None:
    for target, target_stats in ad_group_stats.items():
        if _is_on_cooldown(target, rule, ad_group):
            continue

        if _meets_all_conditions(rule, target_stats):
            with transaction.atomic():
                if _apply_action(target, rule, ad_group):
                    _write_trigger_history(target, rule, ad_group)


def _is_on_cooldown(target: str, rule: Rule, ad_group: core.models.AdGroup) -> bool:
    cooldown_period_start = utils.dates_helper.local_now() - datetime.timedelta(hours=rule.cooldown)
    return RuleTriggerHistory.objects.filter(
        target=target, rule=rule, ad_group=ad_group, triggered_dt__gte=cooldown_period_start
    ).exists()


def _meets_all_conditions(
    rule: Rule, target_stats: DefaultDict[str, DefaultDict[int, Union[None, int, float]]]
) -> bool:
    for condition in rule.conditions.all():
        left_operand_key = constants.METRIC_MV_COLUMNS_MAPPING[condition.left_operand_type]
        left_operand_stat_value = target_stats[left_operand_key][condition.left_operand_window]
        if left_operand_stat_value is None:
            return False

        left_operand_value = left_operand_stat_value * condition.left_operand_modifier

        if condition.right_operand_type in [constants.ValueType.ABSOLUTE, constants.ValueType.CONSTANT]:
            right_operand_value = type(left_operand_value)(condition.right_operand_value)
        else:
            right_operand_key = constants.VALUE_MV_COLUMNS_MAPPING[condition.right_operand_type]
            right_operand_stat_value = target_stats[right_operand_key][condition.right_operand_window]
            if right_operand_stat_value is None:
                return False

            try:
                right_operand_modifier = float(condition.right_operand_value)
            except ValueError:
                right_operand_modifier = 1.0  # "1.0" value default if right side spend when creating conditions?

            right_operand_value = right_operand_stat_value * right_operand_modifier

        if not _meets_condition(condition.operator, left_operand_value, right_operand_value):
            return False

    return True


def _meets_condition(operator: int, left_value, right_value) -> bool:
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

    raise ValueError("Invalid operator type")


def _apply_action(target: str, rule: Rule, ad_group: core.models.AdGroup) -> bool:
    apply_fn = ACTION_TYPE_APPLY_FN_MAPPING[rule.action_type]
    return apply_fn(target, rule, ad_group)


def _write_trigger_history(target: str, rule: Rule, ad_group: core.models.AdGroup) -> None:
    RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target=target)
