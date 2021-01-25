# -*- coding: utf-8 -*-

import jsonfield
import tagulous
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from core.models import tags
from dash import constants
from utils.json_helper import JSONFIELD_DUMP_KWARGS
from utils.settings_fields import CachedOneToOneField

from . import manager
from . import queryset
from .entity_permission import EntityPermissionMixin
from .instance import AgencyInstanceMixin
from .validation import AgencyValidatorMixin


class Agency(EntityPermissionMixin, AgencyValidatorMixin, AgencyInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Agencies"
        ordering = ("-created_dt",)

    _update_fields = (
        "name",
        "sales_representative",
        "cs_representative",
        "ob_sales_representative",
        "ob_account_manager",
        "white_label",
        "custom_flags",
        "default_whitelist",
        "default_blacklist",
        "default_csv_separator",
        "default_csv_decimal_separator",
        "is_externally_managed",
        "is_disabled",
        "uses_realtime_autopilot",
        "uses_source_groups",
        "entity_tags",
        "custom_attributes",
        "allowed_sources",
        "available_sources",
        "default_account_type",
        "amplify_review",
    )

    _externally_managed_fields = ("id", "name", "is_disabled", "custom_attributes", "modified_dt", "amplify_review")

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, unique=True, blank=False, null=False)
    sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )
    cs_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )
    ob_sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )
    ob_account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )

    white_label = models.ForeignKey(
        "Whitelabel", null=True, blank=True, related_name="agencies", on_delete=models.PROTECT
    )
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )
    default_account_type = models.IntegerField(
        default=constants.AccountType.UNKNOWN, choices=constants.AccountType.get_choices()
    )
    allowed_sources = models.ManyToManyField("Source", blank=True)
    available_sources = models.ManyToManyField("Source", blank=True, related_name="available_agencies")
    custom_flags = JSONField(null=True, blank=True)

    default_whitelist = models.OneToOneField(
        "PublisherGroup", related_name="whitelisted_agencies", on_delete=models.PROTECT, null=True, blank=True
    )
    default_blacklist = models.OneToOneField(
        "PublisherGroup", related_name="blacklisted_agencies", on_delete=models.PROTECT, null=True, blank=True
    )

    default_csv_separator = models.CharField(max_length=1, default=",")
    default_csv_decimal_separator = models.CharField(max_length=1, default=".")

    is_externally_managed = models.BooleanField(default=False, help_text="Agency is managed via SalesForce API.")
    is_disabled = models.BooleanField(default=False, help_text="Agency can be disabled only if is externally managed.")
    uses_realtime_autopilot = models.BooleanField(default=True)
    uses_source_groups = models.BooleanField(default=False)

    settings = CachedOneToOneField(
        "AgencySettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )

    entity_tags = tagulous.models.TagField(to=tags.EntityTag, blank=True)
    amplify_review = models.NullBooleanField(default=True)

    custom_attributes = jsonfield.JSONField(
        blank=True,
        default=dict,
        dump_kwargs=JSONFIELD_DUMP_KWARGS,
        help_text="Used only by Outbrain Salesforce to store attributes non existant on Z1.",
    )

    objects = manager.AgencyManager.from_queryset(queryset.AgencyQuerySet)()
