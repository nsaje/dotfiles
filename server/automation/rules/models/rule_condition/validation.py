import datetime

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
            self._validate_right_operand_type,
            self._validate_right_operand_window,
            self._validate_right_operand_value,
            self._validate_conversion_pixel,
            self._validate_conversion_pixel_window,
            self._validate_conversion_pixel_attribution,
            changes=changes,
        )

    def _validate_operator(self, changes):
        operator = changes.get("operator", self.operator)
        if operator not in constants.Operator.get_all():
            raise exceptions.InvalidOperator("Invalid operator")
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if left_operand_type not in config.VALID_OPERATORS or operator not in config.VALID_OPERATORS[left_operand_type]:
            raise exceptions.InvalidOperator("Invalid operator for metric")

    def _validate_left_operand_type(self, changes):
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if left_operand_type not in config.VALID_LEFT_OPERAND_TYPES_FOR_RULE_TARGET[self.rule.target_type]:
            raise exceptions.InvalidLeftOperandType("Invalid metric type")

    def _validate_left_operand_window(self, changes):
        left_operand_window = changes.get("left_operand_window", self.left_operand_window)
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if left_operand_window and left_operand_window not in constants.MetricWindow.get_all():
            raise exceptions.InvalidLeftOperandWindow("Invalid operand window")
        if left_operand_window and not (
            left_operand_type in constants.METRIC_STATS_MAPPING
            or left_operand_type in constants.METRIC_CONVERSIONS_MAPPING
        ):
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
            if left_operand_type in config.PERCENT_MODIFIER_LEFT_OPERAND_TYPES and left_operand_modifier < 0:
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
        left_operand_type = changes.get("left_operand_type", self.left_operand_type)
        if left_operand_type in config.INT_OPERANDS:
            try:
                int(right_operand_value)
            except ValueError:
                raise exceptions.InvalidRightOperandValue("Invalid value")
        elif left_operand_type in config.FLOAT_OPERANDS:
            try:
                float(right_operand_value)
            except ValueError:
                raise exceptions.InvalidRightOperandValue("Invalid value")
        elif left_operand_type in config.DATE_OPERANDS:
            try:
                datetime.date.fromisoformat(right_operand_value)
            except ValueError:
                raise exceptions.InvalidRightOperandValue("Invalid value")

    def _validate_conversion_pixel(self, changes):
        conversion_pixel = changes.get("conversion_pixel", self.conversion_pixel)
        if not conversion_pixel:
            return

        agency = self.rule.agency
        if agency and conversion_pixel.account.agency != agency:
            raise exceptions.InvalidConversionPixel("Conversion pixel does not belong to the rule's agency")

        account = self.rule.account
        if account and conversion_pixel.account != account:
            raise exceptions.InvalidConversionPixel("Conversion pixel does not belong to the rule's account")

    def _validate_conversion_pixel_window(self, changes):
        conversion_pixel = changes.get("conversion_pixel", self.conversion_pixel)
        conversion_pixel_window = changes.get("conversion_pixel_window", self.conversion_pixel_window)

        if conversion_pixel and not conversion_pixel_window:
            raise exceptions.InvalidConversionPixelWindow("Conversion pixel window must not be empty")

    def _validate_conversion_pixel_attribution(self, changes):
        conversion_pixel = changes.get("conversion_pixel", self.conversion_pixel)
        conversion_pixel_attribution = changes.get("conversion_pixel_attribution", self.conversion_pixel_attribution)

        if conversion_pixel and not conversion_pixel_attribution:
            raise exceptions.InvalidConversionPixelAttribution("Conversion pixel attribution must not be empty")
