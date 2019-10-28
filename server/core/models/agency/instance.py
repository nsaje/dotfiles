from django.db import models

import core.features.history
from dash import constants
from utils import exc
from utils import json_helper

from .validation import OUTBRAIN_SALESFORCE_SERVICE_USER


class AgencyInstanceMixin:
    def __str__(self):
        return self.name

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/agency/%d/">Edit</a>' % self.id
        else:
            return "N/A"

    def get_long_name(self):
        return "Agency {}".format(self.name)

    def get_salesforce_id(self):
        return "a{}".format(self.pk)

    def get_current_settings(self):
        if not self.pk:
            raise exc.BaseError("Account settings can't be fetched because acount hasn't been saved yet.")

        # FIXME:circular dependency
        import core.models.settings

        settings = core.models.settings.AgencySettings.objects.filter(agency_id=self.pk).order_by("-created_dt").first()
        if not settings:
            settings = core.models.settings.AgencySettings(agency=self)

        return settings

    def get_all_configured_deals(self):
        return core.features.deals.DirectDealConnection.objects.filter(
            models.Q(agency=self.id) | models.Q(agency=None, account=None, campaign=None, adgroup=None)
        )

    def write_history(self, changes_text, changes=None, user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None
        return core.features.history.History.objects.create(
            agency=self,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.AGENCY,
            action_type=action_type,
        )

    def set_new_accounts_use_bcm_v2(self, request, enabled):
        self.new_accounts_use_bcm_v2 = bool(enabled)
        self.save(request)

    def save(self, request, *args, **kwargs):
        if request and not request.user.is_anonymous:
            self.modified_by = request.user
        super().save(*args, **kwargs)

    def update(self, request, **kwargs):
        updates = self._clean_updates(kwargs)
        if not updates:
            return
        self.validate(updates, request=request)
        self._apply_updates_and_save(request, updates)

    def _clean_updates(self, updates):
        new_updates = {}

        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates_and_save(self, request, updates):
        sub_accounts_updates = dict()

        for field, value in updates.items():
            if field == "entity_tags":
                self.entity_tags.clear()
                if value:
                    self.entity_tags.add(*value)
            elif field == "allowed_sources":
                self.allowed_sources.clear()
                if value:
                    self.allowed_sources.add(*value)
            elif field == "users":
                self.users.clear()
                if value:
                    self.users.add(*value)
            elif field == "is_disabled":
                self.is_disabled = value
                sub_accounts_updates["is_disabled"] = value
            elif field == "cs_representative":
                self.cs_representative = value
                sub_accounts_updates["default_cs_representative"] = value
            elif field == "sales_representative":
                self.sales_representative = value
                sub_accounts_updates["default_sales_representative"] = value
            elif field == "ob_representative":
                self.ob_representative = value
                sub_accounts_updates["ob_representative"] = value
            elif field == "default_account_type":
                self.default_account_type = value
                sub_accounts_updates["account_type"] = value
            elif field == "yahoo_account":
                self.yahoo_account = value
                sub_accounts_updates["yahoo_account"] = value
            else:
                setattr(self, field, value)
        self.save(request)
        self._update_sub_accounts(request, **sub_accounts_updates)

    def _update_sub_accounts(self, request, **updates):
        if self.is_externally_managed and request.user.email != OUTBRAIN_SALESFORCE_SERVICE_USER:
            return
        if updates:
            for account in self.account_set.filter(archived=False):

                account.update(request, **updates)
                account.settings.update(request, **updates)
