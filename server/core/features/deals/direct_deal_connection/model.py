# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from core.common import BaseManager

from . import queryset
from . import validation


class DirectDealConnection(validation.DirectDealConnectionValidatorMixin, models.Model):
    class Meta:
        app_label = "dash"

    objects = BaseManager.from_queryset(queryset.DirectDealConnectionQuerySet)()

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

        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
            self.modified_by = request.user

        self.full_clean()
        super().save(*args, **kwargs)
