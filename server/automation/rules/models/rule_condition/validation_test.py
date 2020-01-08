from contextlib import contextmanager

from django.test import TestCase

import utils.exc

from ... import config
from ... import constants
from ... import exceptions
from . import model


class RuleConditionValidationTest(TestCase):
    def setUp(self):
        self.rule_condition = model.RuleCondition(
            operator=constants.Operator.EQUALS,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            left_operand_window=None,
            left_operand_modifier=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_window=None,
            right_operand_value="300",
        )

    def test_validate_operator(self):
        self.rule_condition.clean({"operator": constants.Operator.EQUALS})
        with self._assert_multiple_validation_error([exceptions.InvalidOperator]):
            self.rule_condition.clean({"operator": 999})

    def test_validate_left_operand_type(self):
        self.rule_condition.clean({"left_operand_type": constants.MetricType.CLICKS})
        self.assertFalse(constants.MetricType.VIDEO_START in config.VALID_LEFT_OPERAND_TYPES)
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandType]):
            self.rule_condition.clean({"left_operand_type": constants.MetricType.VIDEO_START})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandType]):
            self.rule_condition.clean({"left_operand_type": 999})

    def test_validate_left_operand_window(self):
        self.rule_condition.clean({"left_operand_window": constants.MetricWindow.LIFETIME})
        self.rule_condition.clean({"left_operand_window": None})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandWindow]):
            self.rule_condition.clean({"left_operand_window": 999})

    def test_validate_left_operand_modifier(self):
        self.rule_condition.clean({"left_operand_modifier": 0.5})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandModifier]):
            self.rule_condition.clean({"left_operand_modifier": -1})
        with self._assert_multiple_validation_error([exceptions.InvalidLeftOperandModifier]):
            self.rule_condition.clean(
                {"left_operand_modifier": 0.5, "left_operand_type": constants.MetricType.AVG_TIME_ON_SITE}
            )
        self.assertFalse(constants.MetricType.AVG_TIME_ON_SITE in config.PERCENT_MODIFIER_LEFT_OPERAND_TYPES)
        self.rule_condition.left_operand_type = constants.MetricType.AVG_TIME_ON_SITE
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