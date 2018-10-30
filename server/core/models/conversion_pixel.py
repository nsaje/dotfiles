# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.db import models
from django.db import transaction


class ConversionPixel(models.Model):
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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super(ConversionPixel, self).save(*args, **kwargs)

            if not self.slug:
                # if slug is not provided, id is used as a slug.
                # This is here for backwards compatibility. When
                # none of the pixels with actual string slugs are no
                # longer in use, we can get rid of the slugs altogether
                # and use ids instead.
                ConversionPixel.objects.filter(pk=self.id).update(slug=str(self.id))
                self.refresh_from_db()

    def get_url(self):
        return settings.CONVERSION_PIXEL_PREFIX + "{}/{}/".format(self.account.id, self.slug)

    def get_prefix(self):
        return "pixel_{}".format(self.id)

    def get_view_key(self, conversion_window):
        return "{}_{}".format(self.get_prefix(), conversion_window)
