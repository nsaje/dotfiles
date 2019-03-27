# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import ArrayField
from django.db import models


class DemoMapping(models.Model):
    class Meta:
        app_label = "dash"

    real_account = models.OneToOneField("Account", on_delete=models.PROTECT, related_name="+")
    demo_account_name = models.CharField(max_length=127, editable=True, unique=True, blank=False, null=False)
    demo_campaign_name_pool = ArrayField(
        models.CharField(max_length=127, editable=True, unique=True, blank=False, null=False)
    )
    demo_ad_group_name_pool = ArrayField(
        models.CharField(max_length=127, editable=True, unique=True, blank=False, null=False)
    )
