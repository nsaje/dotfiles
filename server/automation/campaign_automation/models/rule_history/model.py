import jsonfield
from django.db import models

import core.models
from utils.json_helper import JSONFIELD_DUMP_KWARGS

from . import queryset


class RuleHistory(models.Model):
    class Meta:
        app_label = "automation"
        verbose_name = "Rule history"
        verbose_name_plural = "Rule history"

    objects = queryset.RuleHistoryQuerySet.as_manager()

    rule = models.ForeignKey("Rule", related_name="history", on_delete=models.PROTECT)
    ad_group = models.ForeignKey(core.models.AdGroup, related_name="rule_history", on_delete=models.PROTECT)
    changes_text = models.TextField(blank=False, null=False)
    changes = jsonfield.JSONField(blank=False, null=False, dump_kwargs=JSONFIELD_DUMP_KWARGS)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)
    # TODO: AUTOCAMP: structure yet to be finalized

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise AssertionError("Updating rule history object is not allowed.")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssertionError("Deleting rule history object is not allowed.")
