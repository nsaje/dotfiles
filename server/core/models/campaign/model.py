# -*- coding: utf-8 -*-

import tagulous
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import core.common
import core.models
import dash.constants
import utils.demo_anonymizer
import utils.string_helper
from core.models import tags
from utils.settings_fields import CachedOneToOneField

from . import bcm_mixin
from . import instance
from . import manager
from . import queryset
from . import validation


class Campaign(
    validation.CampaignValidatorMixin,
    instance.CampaignInstanceMixin,
    core.common.PermissionMixin,
    bcm_mixin.CampaignBCMMixin,
    models.Model,
):
    class Meta:
        app_label = "dash"
        indexes = [models.Index(fields=["created_dt"])]

    _demo_fields = {"name": utils.demo_anonymizer.campaign_name_from_pool}

    _clone_fields = ["default_whitelist", "default_blacklist", "custom_flags"]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, editable=True, blank=False, null=False)
    type = models.IntegerField(
        default=dash.constants.CampaignType.CONTENT,
        choices=dash.constants.CampaignType.get_choices(),
        blank=True,
        null=True,
    )
    account = models.ForeignKey("Account", on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)  # materialized field
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True)

    default_whitelist = models.ForeignKey(
        "PublisherGroup", related_name="whitelisted_campaigns", on_delete=models.PROTECT, null=True, blank=True
    )
    default_blacklist = models.ForeignKey(
        "PublisherGroup", related_name="blacklisted_campaigns", on_delete=models.PROTECT, null=True, blank=True
    )
    custom_flags = JSONField(null=True, blank=True)
    real_time_campaign_stop = models.BooleanField(default=False)

    settings = CachedOneToOneField(
        "CampaignSettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )

    entity_tags = tagulous.models.TagField(to=tags.EntityTag, blank=True)

    USERS_FIELD = "users"

    objects = manager.CampaignManager.from_queryset(queryset.CampaignQuerySet)()

    def get_sspd_url(self):
        if self.id:
            return settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=self.id)
        else:
            return "N/A"
