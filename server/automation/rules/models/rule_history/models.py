import jsonfield
from django.db import models

import core.models
from utils.json_helper import JSONFIELD_DUMP_KWARGS

from ... import constants
from . import instance
from . import queryset


class RuleTriggerHistory(instance.RuleHistoryInstanceMixin, models.Model):
    class Meta:
        app_label = "automation"
        verbose_name = "Rule trigger history"
        verbose_name_plural = "Rule trigger history"

    objects = queryset.RuleHistoryQuerySet.as_manager()

    rule = models.ForeignKey("Rule", related_name="trigger_history", on_delete=models.PROTECT)
    ad_group = models.ForeignKey(core.models.AdGroup, related_name="rule_trigger_history", on_delete=models.PROTECT)
    target = models.CharField(max_length=127)
    triggered_dt = models.DateTimeField(auto_now_add=True, verbose_name="Triggered at", db_index=True)


class RuleHistory(instance.RuleHistoryInstanceMixin, models.Model):
    class Meta:
        app_label = "automation"
        verbose_name = "Rule history"
        verbose_name_plural = "Rule history"

    objects = queryset.RuleHistoryQuerySet.as_manager()

    rule = models.ForeignKey("Rule", related_name="history", on_delete=models.PROTECT)
    ad_group = models.ForeignKey(core.models.AdGroup, related_name="rule_history", on_delete=models.PROTECT)
    status = models.IntegerField(choices=constants.ApplyStatus.get_choices(), default=constants.ApplyStatus.SUCCESS)
    changes_text = models.TextField(blank=False, null=False)
    changes = jsonfield.JSONField(blank=False, null=False, dump_kwargs=JSONFIELD_DUMP_KWARGS)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)
    # TODO: AUTOCAMP: structure yet to be finalized
