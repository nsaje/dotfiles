import dataclasses
import datetime
import decimal
import traceback
from typing import Any
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
class ErrorData:
    target: str
    exc: Exception
    stack_trace: str

    def to_dict(self) -> Dict[str, Dict[str, Optional[str]]]:
        return {self.target: {"message": str(self.exc), "stack_trace": self.stack_trace}}


@transaction.atomic
def apply_rule(
    rule: models.Rule,
    ad_group: core.models.AdGroup,
    ad_group_stats: Union[Dict[str, Dict[str, Dict[int, Optional[float]]]], Dict],
    ad_group_settings: Dict[str, Union[int, str]],
    content_ads_settings: Dict[int, Dict[str, Union[int, str]]],
    campaign_budget: Dict[str, Any],
) -> Tuple[Sequence[ValueChangeData], Sequence[ErrorData]]:

    helpers.ensure_ad_group_valid(rule, ad_group)

    changes, errors = [], []
    for target, target_stats in ad_group_stats.items():
        if _is_on_cooldown(target, rule, ad_group):
            continue

        settings_dict = _construct_target_settings_dict(
            rule, ad_group, target, campaign_budget, ad_group_settings, content_ads_settings
        )
        try:
            if _meets_all_conditions(rule, target_stats, settings_dict):
                update = _apply_action(target, rule, ad_group, target_stats)
                if update.has_changes():
                    _write_trigger_history(target, rule, ad_group)
                    changes.append(update)
        except utils.exc.EntityArchivedError:
            continue
        except exceptions.ApplyFailedBase:
            # NOTE: apply breaking exception
            raise
        except Exception as e:
            error_data = ErrorData(target=target, exc=e, stack_trace=traceback.format_exc())
            errors.append(error_data)

    return changes, errors


def _is_on_cooldown(target: str, rule: models.Rule, ad_group: core.models.AdGroup) -> bool:
    # NOTE: this function assumes rules are run daily. If a rule has 24h cooldown, it should
    # trigger after 23h as well if it's a new date. This is done to account for the job not
    # running at exact same time every day because of materialization. It does not support
    # running rules hourly.
    assert rule.cooldown % 24 == 0, "Support for hourly cooldowns not implemented yet"

    days_to_check = (rule.cooldown // 24) - 1

    local_midnight = utils.dates_helper.get_midnight(utils.dates_helper.local_now())
    local_from_dt = local_midnight - datetime.timedelta(days=days_to_check)
    utc_from_dt = utils.dates_helper.local_to_utc_time(local_from_dt)

    return models.RuleTriggerHistory.objects.filter(
        target=target, rule=rule, ad_group=ad_group, triggered_dt__gte=utc_from_dt
    ).exists()


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


def _meets_all_conditions(
    rule: models.Rule, target_stats: Dict[str, Dict[int, Optional[float]]], settings_dict: Dict[str, Union[int, str]]
) -> bool:
    for condition in rule.conditions.all():
        left_operand_value, right_operand_value = _prepare_operands(rule, condition, target_stats, settings_dict)
        if not _meets_condition(condition.operator, left_operand_value, right_operand_value):
            return False
    return True


def _prepare_operands(
    rule: models.Rule,
    condition: models.RuleCondition,
    target_stats: Dict[str, Dict[int, Optional[float]]],
    settings_dict: Dict[str, Union[int, str]],
):
    _validate_condition(condition)
    if condition.left_operand_type in constants.METRIC_STATS_MAPPING:
        return _prepare_stats_operands(rule, condition, target_stats)
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
    rule: models.Rule, condition: models.RuleCondition, target_stats: Dict[str, Dict[int, Optional[float]]]
):
    left_operand_value = _prepare_left_stat_operand(rule, condition, target_stats)
    right_operand_value = _prepare_right_stat_operand(rule, condition, target_stats)
    return left_operand_value, right_operand_value


def _prepare_left_stat_operand(
    rule: models.Rule, condition: models.RuleCondition, target_stats: Dict[str, Dict[int, Optional[float]]]
):
    left_operand_key = constants.METRIC_STATS_MAPPING[condition.left_operand_type]
    if condition.left_operand_type in constants.CONVERSION_METRICS and left_operand_key not in target_stats:
        raise ValueError("Missing conversion statistics - campaign possibly missing cpa goal")

    window = condition.left_operand_window or rule.window
    if window in target_stats[left_operand_key]:
        left_operand_stat_value = target_stats[left_operand_key][window]
    else:
        left_operand_stat_value = config.STATS_FIELDS_DEFAULTS[left_operand_key]
    if left_operand_stat_value is None:
        return left_operand_stat_value
    left_operand_modifier = condition.left_operand_modifier or 1.0
    return left_operand_stat_value * left_operand_modifier


def _prepare_right_stat_operand(
    rule: models.Rule, condition: models.RuleCondition, target_stats: Dict[str, Dict[int, Optional[float]]]
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
    raise ValueError("Invalid operator type")


def _apply_action(target, rule, ad_group, target_stats):
    apply_fn = ACTION_TYPE_APPLY_FN_MAPPING[rule.action_type]
    return apply_fn(target, rule, ad_group, target_stats=target_stats)


def _write_trigger_history(target: str, rule: models.Rule, ad_group: core.models.AdGroup) -> None:
    models.RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target=target)
