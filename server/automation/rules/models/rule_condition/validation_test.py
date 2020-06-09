from contextlib import contextmanager

from django.test import TestCase

import utils.exc
from utils.magic_mixer import magic_mixer

from ... import config
from ... import constants
from ... import exceptions
from .. import Rule
from . import model


class RuleConditionValidationTest(TestCase):
    def setUp(self):
        self.rule = magic_mixer.blend(Rule)
        self.rule_condition = model.RuleCondition(
            rule=self.rule,
            operator=constants.Operator.GREATER_THAN,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            left_operand_window=None,
            left_operand_modifier=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_window=None,
            right_operand_value="300",
        )

    def test_validate_operator(self):
        self.rule_condition.clean({"operator": constants.Operator.LESS_THAN})
        with self._assert_multiple_validation_error([exceptions.InvalidOperator]):
            self.rule_condition.clean({"operator": constants.Operator.EQUALS})
        with self._assert_multiple_validation_error([exceptions.InvalidOperator]):
            self.rule_condition.clean({"operator": 999})

        self.assertFalse(constants.Operator.CONTAINS in config.VALID_OPERATORS[constants.MetricType.TOTAL_SPEND])
        with self._assert_multiple_validation_error([exceptions.InvalidOperator]):
            self.rule_condition.clean(
                {"operator": constants.Operator.CONTAINS, "left_operand_type": constants.MetricType.TOTAL_SPEND}
            )

    def test_validate_operator_days_since_type(self):
        # NOTE: this test handles an edge case where "days since" settings use date operators but have number
        # values and makes sure that those settings don't get assigned "number" operators by accident
        self.rule.target_type = constants.TargetType.AD
        for left_operand_type in [
            constants.MetricType.DAYS_SINCE_ACCOUNT_CREATED,
            constants.MetricType.DAYS_SINCE_CAMPAIGN_CREATED,
            constants.MetricType.DAYS_SINCE_AD_GROUP_CREATED,
            constants.MetricType.DAYS_SINCE_AD_CREATED,
        ]:
            self.rule_condition.clean({"operator": constants.Operator.EQUALS, "left_operand_type": left_operand_type})
        with self._assert_multiple_validation_error([exceptions.InvalidOperator]):
            self.rule_condition.clean(
                {"operator": constants.Operator.EQUALS, "left_operand_type": constants.MetricType.CLICKS}
            )

    def test_validate_ad_target_metrics(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandType]):
            self.rule_condition.clean(
                {"operator": constants.Operator.EQUALS, "left_operand_type": constants.MetricType.DAYS_SINCE_AD_CREATED}
            )

    def test_validate_left_operand_type(self):
        self.rule_condition.clean({"left_operand_type": constants.MetricType.CLICKS})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandType, exceptions.InvalidOperator]):
            self.rule_condition.clean({"left_operand_type": 999})

    def test_validate_left_operand_window(self):
        self.rule_condition.clean({"left_operand_window": constants.MetricWindow.LIFETIME})
        self.rule_condition.clean({"left_operand_window": None})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandWindow]):
            self.rule_condition.clean({"left_operand_window": 999})

    def test_validate_left_operand_modifier(self):
        self.rule_condition.clean({"left_operand_modifier": None})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandModifier]):
            self.rule_condition.clean(
                {"left_operand_type": constants.MetricType.TOTAL_SPEND, "left_operand_modifier": 0.5}
            )
        self.rule_condition.clean(
            {"left_operand_type": constants.MetricType.CAMPAIGN_PRIMARY_GOAL, "left_operand_modifier": 0.5}
        )
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandModifier]):
            self.rule_condition.clean({"left_operand_modifier": -1})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandModifier]):
            self.rule_condition.clean(
                {"left_operand_modifier": 0.5, "left_operand_type": constants.MetricType.AVG_TIME_ON_SITE}
            )
        self.assertFalse(constants.MetricType.ACCOUNT_NAME in config.PERCENT_MODIFIER_LEFT_OPERAND_TYPES)
        self.rule_condition.left_operand_type = constants.MetricType.ACCOUNT_NAME
        self.rule_condition.operator = constants.Operator.CONTAINS
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandModifier]):
            self.rule_condition.clean({"left_operand_modifier": 0.5})

    def test_validate_right_operand_type(self):
        self.rule_condition.clean({"right_operand_type": constants.ValueType.TOTAL_SPEND})
        self.assertFalse(constants.ValueType.TOTAL_SPEND_DAILY_AVG in config.VALID_RIGTH_OPERAND_TYPES)
        with self._assert_multiple_validation_error([exceptions.InvalidRightOperandType]):
            self.rule_condition.clean({"right_operand_type": constants.ValueType.TOTAL_SPEND_DAILY_AVG})
        with self._assert_multiple_validation_error([exceptions.InvalidRightOperandType]):
            self.rule_condition.clean({"right_operand_type": 999})

    def test_validate_right_operand_window(self):
        self.rule_condition.clean({"right_operand_window": None})
        with self._assert_multiple_validation_error([exceptions.InvalidRightOperandWindow]):
            self.rule_condition.clean({"right_operand_window": constants.MetricWindow.LIFETIME})

    def test_validate_right_operand_value(self):
        self.rule_condition.clean({"right_operand_value": 500})
        with self._assert_multiple_validation_error([exceptions.InvalidRightOperandValue]):
            self.rule_condition.clean({"right_operand_value": None})

    @contextmanager
    def _assert_multiple_validation_error(self, exceptions):
        try:
            yield
        except utils.exc.MultipleValidationError as e:
            for err in e.errors:
                self.assertTrue(type(err) in exceptions)
