# -*- coding: utf-8 -*-


from django.contrib.postgres.fields import ArrayField
from django.db import models

from . import bcm_mixin
from . import instance


class SourceType(instance.SourceTypeMixin, models.Model, bcm_mixin.SourceTypeBCMMixin):
    class Meta:
        app_label = "dash"
        verbose_name = "Source Type"
        verbose_name_plural = "Source Types"

    type = models.CharField(max_length=127, unique=True)
    available_actions = ArrayField(models.PositiveSmallIntegerField(), null=True, blank=True)

    min_cpc = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Minimum CPC")
    max_cpc = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum CPC")

    min_cpm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Minimum CPM")
    max_cpm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum CPM")

    cpc_decimal_places = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="CPC Decimal Places")

    min_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Minimum Daily Spend Cap"
    )
    max_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Maximum Daily Spend Cap"
    )

    delete_traffic_metrics_threshold = models.IntegerField(
        default=0,
        blank=False,
        null=False,
        verbose_name="Max clicks allowed to delete per daily report",
        help_text="When we receive an empty report, we don't override existing data but we mark report aggregation as failed. But for smaller changes (as defined by this parameter), we do override existing data since they are not material. Zero value means no reports will get deleted.",
    )
