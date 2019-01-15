# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

import core.models.ad_group
import core.models.source

from . import DirectDeal


class DirectDealConnection(models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    source = models.ForeignKey(core.models.source.Source, null=False, blank=False, on_delete=models.PROTECT)
    exclusive = models.BooleanField(
        help_text="If the deal is exclusive, we will only respond to requests that have this deal."
    )
    agency = models.ForeignKey(core.models.agency.Agency, null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey(core.models.account.Account, null=True, blank=True, on_delete=models.PROTECT)
    campaign = models.ForeignKey(core.models.campaign.Campaign, null=True, blank=True, on_delete=models.PROTECT)
    adgroup = models.ForeignKey(core.models.ad_group.AdGroup, null=True, blank=True, on_delete=models.PROTECT)
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

    def is_global(self):
        if self.adgroup is None and self.agency is None and self.account is None and self.campaign is None:
            return True
        return False

    def save(self, request=None, *args, **kwargs):
        if self.adgroup is None and self.agency is None and self.account is None and self.campaign is None:
            self.exclusive = False

        if self.pk is None and request:
            self.created_by = request.user

        super(DirectDealConnection, self).save(*args, **kwargs)
