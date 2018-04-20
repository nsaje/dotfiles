from django.core.urlresolvers import reverse
from django.db import transaction

import core.entity
import core.history

from dash import constants

from utils import exc
from utils import json_helper


class AccountInstanceMixin:

    def __str__(self):
        return self.name

    def get_long_name(self):
        agency = ''
        if self.agency:
            agency = self.agency.get_long_name() + ', '
        return '{}Account {}'.format(agency, self.name)

    def get_salesforce_id(self):
        return 'b{}'.format(self.pk)

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

    @transaction.atomic
    def archive(self, request):
        if not self.can_archive():
            raise exc.ForbiddenError(
                'Account can\'t be archived.'
            )

        if not self.is_archived():
            current_settings = self.get_current_settings()
            for campaign in self.campaign_set.all():
                campaign.archive(request)

            new_settings = current_settings.copy_settings()
            new_settings.archived = True
            new_settings.save(
                request, action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    @transaction.atomic
    def restore(self, request):
        if not self.can_restore():
            raise exc.ForbiddenError(
                'Account can\'t be restored.'
            )

        if self.is_archived():
            current_settings = self.get_current_settings()
            new_settings = current_settings.copy_settings()
            new_settings.archived = False
            new_settings.save(
                request, action_type=constants.HistoryActionType.ARCHIVE_RESTORE)

    def admin_link(self):
        if self.id:
            return '<a href="/admin/dash/account/%d/">Edit</a>' % self.id
        else:
            return 'N/A'
    admin_link.allow_tags = True

    def get_account_url(self, request):
        account_settings_url = request.build_absolute_uri(
            reverse('admin:dash_account_change', args=(self.pk,))
        )
        campaign_settings_url = account_settings_url.replace(
            'http://', 'https://')
        return campaign_settings_url

    def get_default_blacklist_name(self):
        return "Default blacklist for account {}({})".format(self.name, self.id)

    def get_default_whitelist_name(self):
        return "Default whitelist for account {}({})".format(self.name, self.id)

    def get_publisher_level(self):
        return constants.PublisherBlacklistLevel.ACCOUNT

    def get_account(self):
        return self

    def write_history(self, changes_text, changes=None,
                      user=None, system_user=None, action_type=None):
        if not changes and not changes_text:
            return None

        _, _, agency = core.entity.helpers.generate_parents(account=self)
        return core.history.History.objects.create(
            account=self,
            agency=agency,
            created_by=user,
            system_user=system_user,
            changes=json_helper.json_serializable_changes(changes),
            changes_text=changes_text or "",
            level=constants.HistoryLevel.ACCOUNT,
            action_type=action_type
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
        custom_flags.update(self.custom_flags or {})
        return custom_flags

    def save(self, request, *args, **kwargs):
        if request and not request.user.is_anonymous():
            self.modified_by = request.user
        super().save(*args, **kwargs)
