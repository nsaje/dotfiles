import utils.validation_helper

from ... import config
from ... import constants
from ... import exceptions


class RuleConditionValidationMixin:
    def clean(self, changes):
        utils.validation_helper.validate_multiple(
            self._validate_operator,
            self._validate_left_operand_type,
            self._validate_left_operand_window,
            self._validate_left_operand_modifier,
            self._validate_right_operand_window,
            self._validate_right_operand_value,
            changes=changes,
        )

    def _validate_operator(self, changes):
        if changes.get("operator", self.operator) not in constants.Operator.get_all():
            raise exceptions.InvalidOperator("Invalid operator")

    def _validate_left_operand_type(self, changes):
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if (
            left_operand_type not in constants.MetricType.get_all()
            or left_operand_type not in config.VALID_LEFT_OPERAND_TYPES
        ):
            raise exceptions.InvalidLeftOperandType("Invalid metric type")

    def _validate_left_operand_window(self, changes):
        left_operand_window = changes.get("left_operand_window", self.left_operand_window)
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if left_operand_window and left_operand_type not in config.WINDOW_ADJUSTEMENT_POSSIBLE_TYPES:
            raise exceptions.InvalidLeftOperandWindow("Setting window is not supported for this metric")

    def _validate_left_operand_modifier(self, changes):
        left_operand_modifier = changes.get("left_operand_modifier", self.left_operand_modifier)
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if left_operand_modifier is not None:
            if (
                left_operand_type
                not in config.PERCENT_MODIFIER_LEFT_OPERAND_TYPES | config.DAY_MODIFIER_LEFT_OPERAND_TYPES
            ):
                raise exceptions.InvalidLeftOperandModifier("Invalid modifier")
            if left_operand_modifier < 0:
                raise exceptions.InvalidLeftOperandModifier("Invalid modifier")

    def _validate_right_operand_type(self, changes):
        right_operand_type = changes.get("right_operand_type", self.right_operand_type)
        if (
            right_operand_type not in constants.ValueType.get_all()
            or right_operand_type not in config.VALID_RIGHT_OPERAND_TYPES
        ):
            raise exceptions.InvalidRightOperandType("Invalid value type")

    def _validate_right_operand_window(self, changes):
        right_operand_window = changes.get("right_operand_window", self.right_operand_window)
        if right_operand_window:
            raise exceptions.InvalidRightOperandWindow("Not supported")

    def _validate_right_operand_value(self, changes):
        right_operand_value = changes.get("right_operand_value", self.right_operand_value)
        if not right_operand_value:
            raise exceptions.InvalidRightOperandValue("Invalid value")
