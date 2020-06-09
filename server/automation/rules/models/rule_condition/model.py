from django.db import models

from ... import constants
from . import instance
from . import manager
from . import validation


class RuleCondition(instance.RuleConditionInstanceMixin, validation.RuleConditionValidationMixin, models.Model):
    objects = manager.RuleConditionManager()

    _update_fields = [
        "left_operand_window",
        "left_operand_type",
        "left_operand_modifier",
        "operator",
        "right_operand_window",
        "right_operand_type",
        "right_operand_value",
    ]

    id = models.AutoField(primary_key=True)
    rule = models.ForeignKey("Rule", related_name="conditions", on_delete=models.CASCADE)

    left_operand_window = models.IntegerField(choices=constants.MetricWindow.get_choices(), null=True, blank=True)
    left_operand_type = models.IntegerField(choices=constants.MetricType.get_choices())
    left_operand_modifier = models.FloatField(default=None, null=True, blank=True)

    operator = models.IntegerField(choices=constants.Operator.get_choices())

    right_operand_window = models.IntegerField(choices=constants.MetricWindow.get_choices(), null=True, blank=True)
    right_operand_type = models.IntegerField(choices=constants.ValueType.get_choices())
    right_operand_value = models.CharField(max_length=127)
