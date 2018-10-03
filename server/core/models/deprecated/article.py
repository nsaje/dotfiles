# -*- coding: utf-8 -*-

from django.db import models


class Article(models.Model):
    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)

    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        app_label = "dash"
        get_latest_by = "created_dt"
        unique_together = ("ad_group", "url", "title")
