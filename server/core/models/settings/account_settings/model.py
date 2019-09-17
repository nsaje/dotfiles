# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db import transaction

import core.common
import core.features.history
import core.models
import utils.demo_anonymizer
import utils.exc
import utils.string_helper
from dash import constants

from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from . import manager
from . import validation


class AccountSettings(validation.AccountSettingsValidatorMixin, SettingsBase):
    class Meta:
        app_label = "dash"
        ordering = ("-created_dt",)

    objects = manager.AccountSettingsManager()

    _demo_fields = {"name": utils.demo_anonymizer.account_name_from_pool}
    _settings_fields = [
        "name",
        "archived",
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

    @transaction.atomic
    def update(self, request, **kwargs):
        clean_updates = {field: value for field, value in kwargs.items() if field in self._settings_fields}
        changes = self.get_changes(clean_updates)
        if not changes:
            return

        self._validate_update(changes)
        self.clean(changes)

        super().update(request, **changes)

        if changes:
            self._handle_archived(request, changes)

        self._update_account(request, changes)

    def _validate_update(self, changes):
        if self.archived:
            if changes.get("archived") is False:
                if not self.account.can_restore():
                    raise utils.exc.ForbiddenError("Account can not be restored")
            else:
                raise utils.exc.ForbiddenError("Account must not be archived in order to update it.")
        else:
            if changes.get("archived"):
                if not self.account.can_archive():
                    raise utils.exc.ForbiddenError("Account can not be archived.")

    def _update_account(self, request, changes):
        if any(field in changes for field in ["name", "archived"]):
            if "name" in changes:
                self.account.name = changes["name"]
            if "archived" in changes:
                self.account.archived = changes["archived"]
            self.account.save(request)

    def _handle_archived(self, request, changes):
        if changes.get("archived"):
            for campaign in self.account.campaign_set.all():
                campaign.archive(request)

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            "name": "Name",
            "archived": "Archived",
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

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return
        if "salesforce_url" in changes:
            return

        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.account.write_history(changes_text, changes=changes, action_type=action_type, user=user)

    class QuerySet(SettingsQuerySet):
        pass
