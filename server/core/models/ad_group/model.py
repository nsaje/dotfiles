# -*- coding: utf-8 -*-
import tagulous
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import utils.demo_anonymizer
import utils.string_helper
from core.models import tags
from dash import constants
from utils.settings_fields import CachedOneToOneField

from . import bcm_mixin
from . import instance
from . import manager
from . import queryset
from . import validation


class AdGroup(validation.AdGroupValidatorMixin, instance.AdGroupInstanceMixin, bcm_mixin.AdGroupBCMMixin, models.Model):
    _current_settings = None

    class Meta:
        app_label = "dash"
        ordering = ("name",)

    _demo_fields = {"name": utils.demo_anonymizer.ad_group_name_from_pool}

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    campaign = models.ForeignKey("Campaign", on_delete=models.PROTECT)
    sources = models.ManyToManyField("Source", through="AdGroupSource")
    bidding_type = models.IntegerField(default=constants.BiddingType.CPC, choices=constants.BiddingType.get_choices())
    archived = models.BooleanField(null=True, blank=True, default=False)  # materialized field
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT)

    default_whitelist = models.ForeignKey(
        "PublisherGroup", related_name="whitelisted_ad_groups", on_delete=models.PROTECT, null=True, blank=True
    )
    default_blacklist = models.ForeignKey(
        "PublisherGroup", related_name="blacklisted_ad_groups", on_delete=models.PROTECT, null=True, blank=True
    )

    custom_flags = JSONField(null=True, blank=True)

    settings = CachedOneToOneField(
        "AdGroupSettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )
    amplify_review = models.NullBooleanField(default=None)

    entity_tags = tagulous.models.TagField(to=tags.EntityTag, blank=True)

    objects = manager.AdGroupManager.from_queryset(queryset.AdGroupQuerySet)()
