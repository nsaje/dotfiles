# -*- coding: utf-8 -*-

import jsonfield
from django.db import models

from utils.json_helper import JSONFIELD_DUMP_KWARGS
from utils.settings_fields import CachedOneToOneField

from . import instance
from . import manager
from . import queryset


class AdGroupSource(instance.AdGroupSourceInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("source", "ad_group")
        indexes = [models.Index(fields=["ad_review_only"])]

    source = models.ForeignKey("Source", on_delete=models.PROTECT)
    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT)

    source_credentials = models.ForeignKey("SourceCredentials", null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={}, dump_kwargs=JSONFIELD_DUMP_KWARGS)

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_reports_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_status_sync_dt = models.DateTimeField(blank=True, null=True)
    can_manage_content_ads = models.BooleanField(null=False, blank=False, default=False)

    source_content_ad_id = models.CharField(max_length=100, null=True, blank=True)
    blockers = jsonfield.JSONField(blank=True, default={}, dump_kwargs=JSONFIELD_DUMP_KWARGS)

    settings = CachedOneToOneField(
        "AdGroupSourceSettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )
    ad_review_only = models.NullBooleanField(default=None)

    objects = manager.AdGroupSourceManager.from_queryset(queryset.AdGroupSourceQuerySet)()
