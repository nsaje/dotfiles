# -*- coding: utf-8 -*-

from django.db import models


class OutbrainAccount(models.Model):
    class Meta:
        app_label = "dash"

    marketer_id = models.CharField(unique=True, blank=False, null=False, max_length=255)
    marketer_name = models.CharField(blank=True, null=True, max_length=255)
    used = models.BooleanField(default=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
