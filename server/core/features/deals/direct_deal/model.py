# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from . import instance
from . import manager
from . import queryset
from . import validation


class DirectDeal(instance.DirectDealMixin, validation.DirectDealValidatorMixin, models.Model):
    class Meta:
        app_label = "dash"

    objects = manager.DirectDealManager.from_queryset(queryset.DirectDealQuerySet)()

    _settings_fields = ["deal_id", "description", "name", "floor_price", "valid_from_date", "valid_to_date"]
    _permissioned_fields = {}

    id = models.AutoField(primary_key=True)
    deal_id = models.CharField(max_length=100, null=False, blank=True)
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=127, null=False, blank=False)
    source = models.ForeignKey("Source", null=False, blank=False, on_delete=models.PROTECT)
    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)
    floor_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    valid_from_date = models.DateField(verbose_name="Valid from", null=True, blank=True)
    valid_to_date = models.DateField(verbose_name="Valid to", null=True, blank=True)
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

    def __str__(self):
        return self.deal_id

    def get_number_of_connected_accounts(self):
        return len(self.directdealconnection_set.filter(account__isnull=False))

    def get_number_of_connected_campaigns(self):
        return len(self.directdealconnection_set.filter(campaign__isnull=False))

    def get_number_of_connected_adgroups(self):
        return len(self.directdealconnection_set.filter(adgroup__isnull=False))
