import jsonfield
from django.db import models

import core.models
from utils.json_helper import JSONFIELD_DUMP_KWARGS

from ... import constants
from . import instance
from . import queryset


class RuleHistory(instance.RuleHistoryInstance, models.Model):
    class Meta:
        app_label = "automation"
        verbose_name = "Rule history"
        verbose_name_plural = "Rule history"

    objects = queryset.RuleHistoryQuerySet.as_manager()

    rule = models.ForeignKey("Rule", related_name="history", on_delete=models.CASCADE)
    ad_group = models.ForeignKey(core.models.AdGroup, related_name="rule_history", on_delete=models.PROTECT)

    status = models.IntegerField(
        choices=constants.ApplyStatus.get_choices(), default=constants.ApplyStatus.SUCCESS, db_index=True
    )
    failure_reason = models.IntegerField(
        choices=constants.RuleFailureReason.get_choices(), default=None, null=True, blank=True
    )

    changes = jsonfield.JSONField(blank=True, null=True, dump_kwargs=JSONFIELD_DUMP_KWARGS)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)
