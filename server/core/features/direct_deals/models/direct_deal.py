# -*- coding: utf-8 -*-

from django.db import models


class DirectDeal(models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    deal_id = models.CharField(max_length=100, null=False, blank=True)

    def __str__(self):
        return self.deal_id
