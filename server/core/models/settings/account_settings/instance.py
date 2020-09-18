from django.db import transaction

import utils.exc
import utils.lambda_helper


class AccountSettingsMixin(object):
    @transaction.atomic
    def update(self, request, **kwargs):
        clean_updates = {field: value for field, value in kwargs.items() if field in self._settings_fields}

        changes = self.get_changes(clean_updates)
        if not changes:
            return

        self._validate_update(changes)
        self.clean(changes)

        super().update(request, **changes)

        self._handle_archived(request, changes)
        self._update_account(request, changes)
        return changes

    def _validate_update(self, changes):
        if self.archived:
            if changes.get("archived") is False:
                if not self.account.can_restore():
                    raise utils.exc.ForbiddenError("Account can not be restored")
            elif not self._can_update_archived_account(changes):
                raise utils.exc.EntityArchivedError("Account must not be archived in order to update it.")

    def _can_update_archived_account(self, changes):
        changed_fields = set(changes.keys())
        if not changed_fields.issubset({"whitelist_publisher_groups", "blacklist_publisher_groups"}):
            return False

        # it should be possible to delete a publisher group, even if it's linked to an archived account
        if "whitelist_publisher_groups" in changes and not set(changes["whitelist_publisher_groups"]).issubset(
            self.whitelist_publisher_groups
        ):
            return False
        if "blacklist_publisher_groups" in changes and not set(changes["blacklist_publisher_groups"]).issubset(
            self.blacklist_publisher_groups
        ):
            return False
        return True

    def _handle_archived(self, request, changes):
        if changes.get("archived"):
            for campaign in self.account.campaign_set.all():
                campaign.archive(request)

    def _update_account(self, request, changes):
        if any(field in changes for field in ["name", "archived"]):
            if "name" in changes:
                self.account.name = changes["name"]
            if "archived" in changes:
                self.account.archived = changes["archived"]
            self.account.save(request)

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return
        if "salesforce_url" in changes:
            return

        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)

        if "default_icon" in changes:
            changes["default_icon"] = changes["default_icon"].origin_url or "uploaded image"

        self.account.write_history(changes_text, changes=changes, action_type=action_type, user=user)
