# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from . import instance
from . import manager
from . import queryset
from . import validation


class DirectDealConnection(
    validation.DirectDealConnectionValidatorMixin, instance.DirectDealConnectionMixin, models.Model
):
    class Meta:
        app_label = "dash"

    objects = manager.DirectDealConnectionManager.from_queryset(queryset.DirectDealConnectionQuerySet)()

    id = models.AutoField(primary_key=True)
    exclusive = models.BooleanField(
        default=True, help_text="If the deal is exclusive, we will only respond to requests that have this deal."
    )
    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)
    campaign = models.ForeignKey("Campaign", null=True, blank=True, on_delete=models.PROTECT)
    adgroup = models.ForeignKey("AdGroup", null=True, blank=True, on_delete=models.PROTECT)
    deal = models.ForeignKey("DirectDeal", null=False, blank=False, on_delete=models.CASCADE)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Created by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Modified by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
