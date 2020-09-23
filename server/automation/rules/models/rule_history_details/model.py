from django.contrib.postgres.fields import JSONField
from django.db import models

from utils import json_helper

from .. import RuleHistory


class RuleHistoryDetails(models.Model):
    rule_history = models.OneToOneField(RuleHistory, on_delete=models.CASCADE, related_name="details")

    conditions = JSONField(encoder=json_helper.JSONEncoder, null=True, blank=True)
    target_condition_values = JSONField(encoder=json_helper.JSONEncoder, null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)
