# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.db import models

import utils.dates_helper

from . import instance
from . import manager
from . import validation


class ConversionPixel(validation.ConversionPixelValidatorMixin, instance.ConversionPixelInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("slug", "account")

    objects = manager.ConversionPixelManager()

    _settings_fields = ["name", "archived", "audience_enabled", "additional_pixel", "redirect_url", "notes"]

    _permissioned_fields = {
        "additional_pixel": "zemauth.can_promote_additional_pixel",
        "redirect_url": "zemauth.can_redirect_pixels",
        "notes": "zemauth.can_see_pixel_notes",
    }

    _SLUG_PLACEHOLDER = "temp_slug"

    id = models.AutoField(primary_key=True)
    name = models.CharField(blank=False, null=False, max_length=50)
    account = models.ForeignKey("Account", on_delete=models.PROTECT)
    slug = models.CharField(blank=False, null=False, max_length=32)
    archived = models.BooleanField(default=False)
    audience_enabled = models.BooleanField(default=False)
    additional_pixel = models.BooleanField(default=False)
    last_triggered = models.DateTimeField(blank=True, null=True)
    impressions = models.PositiveIntegerField(default=0)
    redirect_url = models.CharField(max_length=2048, blank=True, null=True)
    notes = models.TextField(blank=True)
    last_sync_dt = models.DateTimeField(default=datetime.datetime.utcnow, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created on")

    def get_url(self):
        return settings.CONVERSION_PIXEL_PREFIX + "{}/{}/".format(self.account.id, self.slug)

    def get_prefix(self):
        return "pixel_{}".format(self.id)

    def get_view_key(self, conversion_window):
        return "{}_{}".format(self.get_prefix(), conversion_window)

    def get_impressions(self, date=None):
        if date is None:
            date = utils.dates_helper.local_yesterday()
        return self.impressions if self.last_triggered and self.last_triggered.date() >= date else 0
