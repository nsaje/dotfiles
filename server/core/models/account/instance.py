from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe

import core.features.deals
import core.features.history
import core.models
from dash import constants
from utils import exc
from utils import json_helper


class AccountInstanceMixin:
    def __str__(self):
        return self.name

    def get_long_name(self):
        agency = ""
        if self.agency:
            agency = self.agency.get_long_name() + ", "
        return "{}Account {}".format(agency, self.name)

    def get_salesforce_id(self):
        return "b{}".format(self.pk)

    def get_current_settings(self):
        return self.settings

    def can_archive(self):
        for campaign in self.campaign_set.all():
            if not campaign.can_archive():
                return False

        return True

    def can_restore(self):
        return True

    def is_archived(self):
        current_settings = self.get_current_settings()
        return current_settings.archived

    def is_agency(self):
        return self.agency is not None

    @property
    def is_externally_managed(self):
        if self.is_agency():
            return self.agency.is_externally_managed
        return False

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError("Account can't be archived.")

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for campaign in self.campaign_set.all():
                campaign.archive(request)

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(request, action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError("Account can't be restored.")

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(request, action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    def admin_link(self):
        if self.id:
            return mark_safe('<a href="/admin/dash/account/%d/">Edit</a>' % self.id)
        else:
            return "N/A"

    def get_account_url(self, request):
        account_settings_url = request.build_absolute_uri(reverse("admin:dash_account_change", args=(self.pk,)))
        campaign_settings_url = account_settings_url.replace("http://", "https://")
        return campaign_settings_url

    def get_default_blacklist_name(self):
        return "Default blacklist for account {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return "Default whitelist for account {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.ACCOUNT

    def get_account(self):
        return self

    def write_history(self, changes_text, changes=None, user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None

        _, _, agency = core.models.helpers.generate_parents(account=self)
        return core.features.history.History.objects.create(
            account=self,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.ACCOUNT,
            action_type=action_type,
        )

    def set_uses_bcm_v2(self, request, enabled):
        self.uses_bcm_v2 = bool(enabled)
        self.save(request)

    @transaction.atomic
    def migrate_to_bcm_v2(self, request):
        if self.uses_bcm_v2:
            return

        for campaign in self.campaign_set.all():
            campaign.migrate_to_bcm_v2(request)

        self.set_uses_bcm_v2(request, True)
        self._migrate_agency(request)

    def _migrate_agency(self, request):
        if self.agency and self.agency.account_set.all_use_bcm_v2():
            self.agency.set_new_accounts_use_bcm_v2(request, True)

    def get_all_custom_flags(self):
        custom_flags = self.agency and self.agency.custom_flags or {}
        if self.custom_flags:
            custom_flags.update({k: v for k, v in self.custom_flags.items() if v})
        return custom_flags

    def get_all_configured_deals(self):
        return core.features.deals.DirectDealConnection.objects.filter(
            Q(account=self.id)
            | Q(agency=self.agency, agency__isnull=False)
            | Q(agency=None, account=None, campaign=None, adgroup=None)
        )

    def save(self, request, *args, **kwargs):
        if request and not request.user.is_anonymous:
            self.modified_by = request.user
        super().save(*args, **kwargs)

    @transaction.atomic
    def update(self, request, **kwargs):
        updates = self._clean_updates(kwargs)
        if not updates:
            return
        self.validate(updates, request=request)
        self._apply_updates_and_save(request, updates)

    def _clean_updates(self, updates):
        new_updates = {}

        for field, value in updates.items():
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates_and_save(self, request, updates):
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
            else:
                setattr(self, field, value)
        self.save(request)
