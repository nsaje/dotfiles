from django.db import models

from ... import constants


class RuleCondition(models.Model):
    id = models.AutoField(primary_key=True)
    rule = models.ForeignKey("Rule", related_name="conditions", on_delete=models.PROTECT)

    left_operand_window = models.IntegerField(choices=constants.MetricWindow.get_choices())
    left_operand_type = models.IntegerField(choices=constants.MetricType.get_choices())
    left_operand_value = models.CharField(max_length=127)

    operator = models.IntegerField(choices=constants.Operator.get_choices())

    right_operand_window = models.IntegerField(choices=constants.MetricWindow.get_choices())
    right_operand_type = models.IntegerField(choices=constants.ValueType.get_choices())
    right_operand_value = models.CharField(max_length=127)
