import datetime

from django.db import models

from . import instance


class ConversionPixel(instance.ConversionPixelMixin, models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("slug", "account")

    id = models.AutoField(primary_key=True)
    name = models.CharField(blank=False, null=False, max_length=50)
    account = models.ForeignKey("Account", on_delete=models.PROTECT)
    slug = models.CharField(blank=False, null=False, max_length=32)
    archived = models.BooleanField(default=False)
    audience_enabled = models.BooleanField(default=False)
    last_triggered = models.DateTimeField(blank=True, null=True)
    impressions = models.PositiveIntegerField(default=0)
    redirect_url = models.CharField(max_length=2048, blank=True, null=True)
    notes = models.TextField(blank=True)
    additional_pixel = models.BooleanField(default=False)
    last_sync_dt = models.DateTimeField(default=datetime.datetime.utcnow, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created on")
