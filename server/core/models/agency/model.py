# -*- coding: utf-8 -*-

import tagulous
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import core.features.deals
import core.features.yahoo_accounts
import core.models
from core.models import tags
from dash import constants
from utils.settings_fields import CachedOneToOneField

from . import instance
from . import manager
from . import queryset


class Agency(instance.AgencyInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"
        verbose_name_plural = "Agencies"
        ordering = ("-created_dt",)

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
    whitelabel = models.CharField(
        max_length=255, choices=constants.Whitelabel.get_choices(), editable=True, unique=False, blank=True
    )
    custom_favicon_url = models.CharField(max_length=255, editable=True, blank=True, default="")
    custom_dashboard_title = models.CharField(max_length=255, editable=True, blank=True, default="")
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT)
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

    settings = CachedOneToOneField(
        "AgencySettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )

    entity_tags = tagulous.models.TagField(to=tags.EntityTag, blank=True)

    objects = manager.AgencyManager.from_queryset(queryset.AgencyQuerySet)()
