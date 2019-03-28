# -*- coding: utf-8 -*-

import jsonfield
import tagulous
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import core.features.deals
import core.features.yahoo_accounts
import core.models
from core.models import tags
from dash import constants
from utils.json_helper import JSONFIELD_DUMP_KWARGS
from utils.settings_fields import CachedOneToOneField

from . import manager
from . import queryset
from .instance import AgencyInstanceMixin
from .validation import AgencyValidatorMixin


class Agency(AgencyValidatorMixin, AgencyInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Agencies"
        ordering = ("-created_dt",)

    _update_fields = (
        "name",
        "sales_representative",
        "cs_representative",
        "cs_representative",
        "ob_representative",
        "white_label",
        "users",
        "new_accounts_use_bcm_v2",
        "allowed_sources",
        "custom_flags",
        "default_whitelist",
        "default_blacklist",
        "yahoo_account",
        "default_csv_separator",
        "default_csv_decimal_separator",
        "is_externally_managed",
        "is_disabled",
        "entity_tags",
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, unique=True, blank=False, null=False)
    sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )
    cs_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )
    ob_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )

    white_label = models.ForeignKey(
        "Whitelabel", null=True, blank=True, related_name="agencies", on_delete=models.PROTECT
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )
    default_account_type = models.IntegerField(
        default=constants.AccountType.UNKNOWN, choices=constants.AccountType.get_choices()
    )
    new_accounts_use_bcm_v2 = models.BooleanField(
        default=True,
        verbose_name="Margins v2",
        help_text=(
            "New accounts created by this agency's users will have " "license fee and margin included into all costs."
        ),
    )
    allowed_sources = models.ManyToManyField("Source", blank=True)
    custom_flags = JSONField(null=True, blank=True)

    default_whitelist = models.OneToOneField(
        "PublisherGroup", related_name="whitelisted_agencies", on_delete=models.PROTECT, null=True, blank=True
    )
    default_blacklist = models.OneToOneField(
        "PublisherGroup", related_name="blacklisted_agencies", on_delete=models.PROTECT, null=True, blank=True
    )

    yahoo_account = models.ForeignKey(
        core.features.yahoo_accounts.YahooAccount, on_delete=models.PROTECT, null=True, blank=True
    )

    default_csv_separator = models.CharField(max_length=1, default=",")
    default_csv_decimal_separator = models.CharField(max_length=1, default=".")
    is_externally_managed = models.BooleanField(default=False, help_text="Agency is managed via SalesForce API.")
    is_disabled = models.BooleanField(default=False, help_text="Agency can be disabled only if is externally managed.")
    settings = CachedOneToOneField(
        "AgencySettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )

    entity_tags = tagulous.models.TagField(to=tags.EntityTag, blank=True)
    custom_attributes = jsonfield.JSONField(
        blank=True,
        default=dict,
        dump_kwargs=JSONFIELD_DUMP_KWARGS,
        help_text="Used only by Outbrain Salesforce to store attributes non existant on Z1.",
    )

    objects = manager.AgencyManager.from_queryset(queryset.AgencyQuerySet)()
