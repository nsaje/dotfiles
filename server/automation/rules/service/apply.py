import dataclasses
import datetime
import traceback
from typing import DefaultDict
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

from django.db import transaction

import core.features.bid_modifiers
import core.models
import utils.dates_helper
import utils.exc

from .. import Rule
from .. import RuleTriggerHistory
from .. import constants
from . import actions
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
class ErrorData:
    target: str
    exc: Exception
    stack_trace: str

    def to_dict(self) -> Dict[str, Dict[str, Optional[str]]]:
        return {self.target: {"message": str(self.exc), "stack_trace": self.stack_trace}}


def apply_rule(
    rule: Rule,
    ad_group: core.models.AdGroup,
    ad_group_stats: Union[DefaultDict[str, DefaultDict[str, DefaultDict[int, Optional[float]]]], Dict],
) -> Tuple[Sequence[ValueChangeData], Sequence[ErrorData]]:
    changes, errors = [], []

    for target, target_stats in ad_group_stats.items():
        if _is_on_cooldown(target, rule, ad_group):
            continue

        if _meets_all_conditions(rule, target_stats):
            with transaction.atomic():
                try:
                    update = _apply_action(target, rule, ad_group, target_stats)
                    if update.has_changes():
                        _write_trigger_history(target, rule, ad_group)
                        changes.append(update)

                except utils.exc.ForbiddenError:
                    continue

                except Exception as e:
                    error_data = ErrorData(target=target, exc=e, stack_trace=traceback.format_exc())
                    errors.append(error_data)

    return changes, errors


def _is_on_cooldown(target: str, rule: Rule, ad_group: core.models.AdGroup) -> bool:
    cooldown_window_start = utils.dates_helper.local_now() - datetime.timedelta(hours=rule.cooldown)
    return RuleTriggerHistory.objects.filter(
        target=target, rule=rule, ad_group=ad_group, triggered_dt__gte=cooldown_window_start
    ).exists()


def _meets_all_conditions(rule: Rule, target_stats: DefaultDict[str, DefaultDict[int, Optional[float]]]) -> bool:
    for condition in rule.conditions.all():
        left_operand_value, right_operand_value = _prepare_operands(condition, target_stats)
        if not _meets_condition(condition.operator, left_operand_value, right_operand_value):
            return False
    return True


def _prepare_operands(condition, target_stats: DefaultDict[str, DefaultDict[int, Optional[float]]]):
    if condition.left_operand_type in constants.METRIC_STATS_MAPPING:
        return _prepare_stats_operands(condition, target_stats)
    elif condition.left_operand_type in constants.METRIC_SETTINGS_MAPPING:
        pass

    raise ValueError("Invalid condition type")


def _prepare_stats_operands(condition, target_stats: DefaultDict[str, DefaultDict[int, Optional[float]]]):
    left_operand_value = _prepare_left_stat_operand(condition, target_stats)
    right_operand_value = _prepare_right_stat_operand(condition, target_stats)
    return left_operand_value, right_operand_value


def _prepare_left_stat_operand(condition, target_stats: DefaultDict[str, DefaultDict[int, Optional[float]]]):
    left_operand_key = constants.METRIC_STATS_MAPPING[condition.left_operand_type]
    left_operand_stat_value = target_stats[left_operand_key][condition.left_operand_window]
    if left_operand_stat_value is None:
        return left_operand_stat_value
    left_operand_modifier = condition.left_operand_modifier or 1.0
    return left_operand_stat_value * left_operand_modifier


def _prepare_right_stat_operand(condition, target_stats: DefaultDict[str, DefaultDict[int, Optional[float]]]):
    # TODO: handle constants
    if condition.right_operand_type == constants.ValueType.ABSOLUTE:
        return float(condition.right_operand_value)
    elif condition.right_operand_type in constants.VALUE_STATS_MAPPING:
        right_operand_key = constants.VALUE_STATS_MAPPING[condition.right_operand_type]
        right_operand_stat_value = target_stats[right_operand_key][condition.right_operand_window]
        if right_operand_stat_value is None:
            return right_operand_stat_value
        try:
            right_operand_modifier = float(condition.right_operand_value)
        except ValueError:
            right_operand_modifier = 1.0
        return right_operand_stat_value * right_operand_modifier
    raise ValueError("Invalid right operand")


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
    raise ValueError("Invalid operator type")


def _apply_action(target, rule, ad_group, target_stats):
    apply_fn = ACTION_TYPE_APPLY_FN_MAPPING[rule.action_type]
    return apply_fn(target, rule, ad_group, target_stats=target_stats)


def _write_trigger_history(target: str, rule: Rule, ad_group: core.models.AdGroup) -> None:
    RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target=target)
