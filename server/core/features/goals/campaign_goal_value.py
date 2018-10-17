# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class CampaignGoalValue(models.Model):
    class Meta:
        app_label = "dash"
        ordering = ["created_dt"]

    campaign_goal = models.ForeignKey("CampaignGoal", related_name="values", on_delete=models.PROTECT)
    value = models.DecimalField(max_digits=15, decimal_places=5)
    local_value = models.DecimalField(
        max_digits=15, decimal_places=5, null=True, blank=True
    )  # TODO(nsaje): remove null&blank after migration

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Created by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
