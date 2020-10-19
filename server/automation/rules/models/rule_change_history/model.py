from django.db import models

import core.features.history

from . import manager


class RuleChangeHistory(core.features.history.HistoryModel):
    objects = manager.RuleChangeHistoryManager()

    rule = models.ForeignKey("Rule", related_name="change_history", on_delete=models.CASCADE)
