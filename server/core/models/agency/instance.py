from django.db import models

import core.features.history
from dash import constants
from utils import exc
from utils import json_helper


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
        self.clean()
        self._apply_updates_and_save(request, updates)

    def _clean_updates(self, updates):
        new_updates = {}

        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates_and_save(self, request, updates):
        for field, value in updates.items():
            if field == "is_disabled":
                for account in self.account_set.all():
                    account.update(request, is_disabled=value)
            if field == "entity_tags":
                if value:
                    self.entity_tags.add(*value)
                else:
                    self.entity_tags.clear()
                continue
            setattr(self, field, value)
        self.save(request)
