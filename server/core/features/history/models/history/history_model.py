# -*- coding: utf-8 -*-
import jsonfield
from django.conf import settings
from django.db import models

from utils.json_helper import JSONFIELD_DUMP_KWARGS


class HistoryModel(models.Model):
    snapshot = jsonfield.JSONField(blank=False, null=False, dump_kwargs=JSONFIELD_DUMP_KWARGS)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.PROTECT
    )

    def to_dict(self):
        raise NotImplementedError()

    class Meta:
        abstract = True
