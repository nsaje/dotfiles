# -*- coding: utf-8 -*-

from django.db import models

import core.common
import core.models
from dash import constants

from . import instance
from . import queryset


class CpcConstraint(instance.CpcConstraintInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    min_cpc = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Minimum CPC")
    max_cpc = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Maximum CPC")
    agency = models.ForeignKey(
        "Agency", null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    account = models.ForeignKey(
        "Account", null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    campaign = models.ForeignKey(
        "Campaign", null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    ad_group = models.ForeignKey(
        "AdGroup", null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    source = models.ForeignKey(
        "Source", null=True, blank=True, related_name="cpc_constraints", on_delete=models.PROTECT
    )
    constraint_type = models.IntegerField(
        default=constants.CpcConstraintType.MANUAL, choices=constants.CpcConstraintType.get_choices()
    )
    reason = models.TextField(null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    objects = core.common.BaseManager.from_queryset(queryset.CpcConstraintQuerySet)()
