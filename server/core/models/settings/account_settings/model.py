# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

import core.features.publisher_groups
import core.models
import utils.demo_anonymizer
from dash import constants

from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from . import instance
from . import manager
from . import validation


class AccountSettings(validation.AccountSettingsValidatorMixin, instance.AccountSettingsMixin, SettingsBase):
    class Meta:
        app_label = "dash"
        ordering = ("-created_dt",)

    objects = manager.AccountSettingsManager()

    _demo_fields = {"name": utils.demo_anonymizer.account_name_from_pool}
    _settings_fields = [
        "name",
        "archived",
        "default_icon",
        "default_account_manager",
        "default_sales_representative",
        "default_cs_representative",
        "ob_representative",
        "account_type",
        "whitelist_publisher_groups",
        "blacklist_publisher_groups",
        "salesforce_url",
        "auto_add_new_sources",
        "frequency_capping",
    ]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)
    account = models.ForeignKey("Account", on_delete=models.PROTECT)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)

    default_icon = models.ForeignKey(core.models.ImageAsset, null=True, on_delete=models.PROTECT)
    default_account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT
    )
    default_sales_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT
    )
    default_cs_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT
    )
    ob_representative = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.PROTECT
    )
    account_type = models.IntegerField(
        default=constants.AccountType.UNKNOWN, choices=constants.AccountType.get_choices()
    )

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    salesforce_url = models.URLField(null=True, blank=True, max_length=255)

    auto_add_new_sources = models.BooleanField(default=False)

    archived = models.BooleanField(default=False)
    changes_text = models.TextField(blank=True, null=True)

    frequency_capping = models.PositiveIntegerField(blank=True, null=True)

    def get_base_default_icon_url(self):
        if not self.default_icon:
            return None

        return self.default_icon.get_base_url()

    def get_default_icon_url(self, size=None):
        if not self.default_icon:
            return None

        if size is None:
            size = self.default_icon.width

        return self.default_icon.get_url(width=size, height=size)

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            "name": "Name",
            "archived": "Archived",
            "default_icon": "Default icon",
            "default_account_manager": "Account Manager",
            "default_sales_representative": "Sales Representative",
            "default_cs_representative": "Customer Success Representative",
            "ob_representative": "Outbrain Representative",
            "account_type": "Account Type",
            "whitelist_publisher_groups": "Whitelist publisher groups",
            "blacklist_publisher_groups": "Blacklist publisher groups",
            "salesforce_url": "SalesForce",
            "auto_add_new_sources": "Automatically add new sources",
            "frequency_capping": "Frequency Capping",
        }
        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == "archived":
            value = str(value)
        elif prop_name == "default_icon":
            return value.origin_url or "uploaded image"
        elif prop_name in (
            "default_account_manager",
            "default_sales_representative",
            "default_cs_representative",
            "ob_representative",
        ):
            # FIXME:circular dependency
            import dash.views.helpers

            value = dash.views.helpers.get_user_full_name_or_email(value)
        elif prop_name in ("whitelist_publisher_groups", "blacklist_publisher_groups"):
            if not value:
                value = ""
            else:
                names = core.features.publisher_groups.PublisherGroup.objects.filter(pk__in=value).values_list(
                    "name", flat=True
                )
                value = ", ".join(names)
        elif prop_name == "account_type":
            value = constants.AccountType.get_text(value)
        return value

    class QuerySet(SettingsQuerySet):
        pass
