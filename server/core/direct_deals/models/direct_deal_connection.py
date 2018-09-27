# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

import core.models.ad_group
import core.models.agency
import core.models.source
from . import DirectDeal


class DirectDealConnection(models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    source = models.ForeignKey(core.models.source.Source, null=False, blank=False, on_delete=models.PROTECT)
    exclusive = models.BooleanField()
    adgroup = models.ForeignKey(core.models.ad_group.AdGroup, null=True, blank=True, on_delete=models.PROTECT)
    agency = models.ForeignKey(core.models.agency.Agency, null=True, blank=True, on_delete=models.PROTECT)
    deals = models.ManyToManyField(DirectDeal)

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

    def save(self, request=None, *args, **kwargs):
        if self.adgroup is None and self.agency is None:
            self.exclusive = False

        if self.pk is None and request:
            self.created_by = request.user

        super(DirectDealConnection, self).save(*args, **kwargs)
