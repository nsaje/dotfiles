# -*- coding: utf-8 -*-
import jsonfield.fields
import tagulous
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import utils.demo_anonymizer
import utils.string_helper
from core.models import tags
from dash import constants
from utils.json_helper import JSONFIELD_DUMP_KWARGS
from utils.settings_fields import CachedOneToOneField

from . import manager
from . import queryset
from .entity_permission import EntityPermissionMixin
from .instance import AccountInstanceMixin
from .validation import AccountValidatorMixin


class Account(EntityPermissionMixin, AccountValidatorMixin, AccountInstanceMixin, models.Model):
    class Meta:
        ordering = ("-created_dt",)

        app_label = "dash"

    _demo_fields = {"name": utils.demo_anonymizer.account_name_from_pool}
    _update_fields = (
        "name",
        "auto_archiving_enabled",
        "agency",
        "outbrain_marketer_id",
        "outbrain_marketer_version",
        "outbrain_internal_marketer_id",
        "salesforce_url",
        "custom_flags",
        "real_time_campaign_stop",
        "entity_tags",
        "is_disabled",
        "default_whitelist",
        "default_blacklist",
        "agency",
        "custom_attributes",
        "salesforce_id",
        "allowed_sources",
        "amplify_review",
    )
    _externally_managed_fields = (
        "id",
        "name",
        "salesforce_url",
        "salesforce_id",
        "is_disabled",
        "custom_attributes",
        "currency",
        "amplify_review",
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, unique=False, blank=False, null=False)
    agency = models.ForeignKey("Agency", on_delete=models.PROTECT, null=True, blank=True)
    auto_archiving_enabled = models.BooleanField(null=False, blank=False, default=True)
    archived = models.BooleanField(default=False)  # materialized field
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )

    default_whitelist = models.ForeignKey(
        "PublisherGroup", related_name="whitelisted_accounts", on_delete=models.PROTECT, null=True, blank=True
    )
    default_blacklist = models.ForeignKey(
        "PublisherGroup", related_name="blacklisted_accounts", on_delete=models.PROTECT, null=True, blank=True
    )

    allowed_sources = models.ManyToManyField("Source")

    outbrain_marketer_id = models.CharField(null=True, blank=True, max_length=255)
    outbrain_marketer_version = models.IntegerField(default=0)
    outbrain_internal_marketer_id = models.CharField(null=True, blank=True, max_length=255)

    salesforce_url = models.URLField(null=True, blank=True, max_length=255)
    salesforce_id = models.IntegerField(null=True, blank=True, help_text="Outbrain custom Salesforce ID.")

    custom_flags = JSONField(null=True, blank=True)
    real_time_campaign_stop = models.BooleanField(
        default=False,
        verbose_name="Default to real time campaign stop",
        help_text="Campaigns of this account will use real time campaign stop instead of landing mode.",
    )

    currency = models.CharField(
        max_length=3, null=True, default=constants.Currency.USD, choices=constants.Currency.get_choices()
    )

    settings = CachedOneToOneField(
        "AccountSettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )

    entity_tags = tagulous.models.TagField(to=tags.EntityTag, blank=True)
    is_disabled = models.BooleanField(default=False, help_text="Agency can be disabled only if is externally managed.")
    custom_attributes = jsonfield.JSONField(
        blank=True,
        default=dict,
        dump_kwargs=JSONFIELD_DUMP_KWARGS,
        help_text="Used only by Outbrain Salesforce to store attributes non existant on Z1.",
    )
    amplify_review = models.NullBooleanField(default=True)

    objects = manager.AccountManager.from_queryset(queryset.AccountQuerySet)()

    def get_sspd_url(self):
        if self.id:
            return settings.SSPD_ACCOUNT_REDIRECT_URL.format(id=self.id)
        else:
            return "N/A"

    def agency_uses_realtime_autopilot(self):
        return self.agency.uses_realtime_autopilot if self.agency else False
