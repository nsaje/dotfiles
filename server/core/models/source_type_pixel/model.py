# -*- coding: utf-8 -*-

from django.db import models


class SourceTypePixel(models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("pixel", "source_type")

    pixel = models.ForeignKey("ConversionPixel", on_delete=models.PROTECT)
    url = models.CharField(max_length=255)
    source_pixel_id = models.CharField(max_length=127)
    source_type = models.ForeignKey("SourceType", on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created on")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
