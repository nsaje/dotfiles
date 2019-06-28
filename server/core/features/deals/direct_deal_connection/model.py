# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from . import validation


class DirectDealConnection(validation.DirectDealsConnectionMixin, models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    source = models.ForeignKey("Source", null=False, blank=False, on_delete=models.PROTECT)
    exclusive = models.BooleanField(
        default=True, help_text="If the deal is exclusive, we will only respond to requests that have this deal."
    )
    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)
    campaign = models.ForeignKey("Campaign", null=True, blank=True, on_delete=models.PROTECT)
    adgroup = models.ForeignKey("AdGroup", null=True, blank=True, on_delete=models.PROTECT)
    deals = models.ManyToManyField("DirectDeal")
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

    @property
    def is_global(self):
        if not any([self.adgroup, self.agency, self.account, self.campaign]):
            return True
        return False

    @property
    def level(self):
        return (
            self.agency
            and "Agency"
            or self.account
            and "Account"
            or self.campaign
            and "Campaign"
            or self.adgroup
            and "Ad group"
            or "Global"
        )

    def save(self, request=None, *args, **kwargs):
        if self.is_global:
            self.exclusive = False

        if self.pk is None and request:
            self.created_by = request.user
        self.full_clean()
        super().save(*args, **kwargs)
