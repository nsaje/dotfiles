from django.db import models

import core.models

from .. import common


class RuleTriggerHistory(common.RuleHistoryInstanceMixin, models.Model):
    class Meta:
        app_label = "automation"
        verbose_name = "Rule trigger history"
        verbose_name_plural = "Rule trigger history"

    objects = common.RuleHistoryQuerySet.as_manager()

    rule = models.ForeignKey("Rule", related_name="trigger_history", on_delete=models.CASCADE)
    ad_group = models.ForeignKey(core.models.AdGroup, related_name="rule_trigger_history", on_delete=models.PROTECT)
    target = models.CharField(max_length=127)
    triggered_dt = models.DateTimeField(auto_now_add=True, verbose_name="Triggered at", db_index=True)
