# -*- coding: utf-8 -*-

from django.db import models

from . import instance


class SourceCredentials(instance.SourceCredentialsMixin, models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Source Credentials"

    id = models.AutoField(primary_key=True)
    source = models.ForeignKey("Source", on_delete=models.PROTECT)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    credentials = models.TextField(blank=True, null=False)
    sync_reports = models.BooleanField(default=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
