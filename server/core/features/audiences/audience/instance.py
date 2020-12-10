from django.db import transaction
from django.db.models import Q

from dash import constants
from utils import exc
from utils import k1_helper


class AudienceInstanceMixin:
    def __str__(self):
        return self.name

    @transaction.atomic
    def update(self, request, skip_validation=False, skip_permission_check=False, skip_propagation=False, **updates):
        changes = self._clean_updates(request, updates, skip_permission_check)
        if not changes:
            return

        if not skip_validation:
            self.clean(changes)

        self._apply_changes_and_save(request, changes)

        if not skip_propagation:
            self._write_change_history(request, changes)
            k1_helper.update_account(self.pixel.account, msg="audience.update")

    def _clean_updates(self, request, updates, skip_permission_check):
        user = request.user if request else None
        new_updates = {}

        for field, value in list(updates.items()):
            required_permission = not skip_permission_check and self._permissioned_fields.get(field)
            if required_permission and not (user is None or user.has_perm(required_permission)):
                continue
            if field in set(self._settings_fields) and value != getattr(self, field):
                new_updates[field] = value

        return new_updates

    def _apply_changes_and_save(self, request, changes):
        for field, value in list(changes.items()):
            if field in self._settings_fields:
                setattr(self, field, value)
        self._save()

    def _write_change_history(self, request, changes):
        if "archived" in changes:
            changes_text = "{} audience '{}'.".format("Archived" if self.archived else "Restored", self.name)
            self.add_to_history(
                request.user,
                constants.HistoryActionType.AUDIENCE_ARCHIVE
                if self.archived
                else constants.HistoryActionType.AUDIENCE_RESTORE,
                changes_text,
            )

        if "name" in changes:
            self.add_to_history(
                request.user,
                constants.HistoryActionType.AUDIENCE_UPDATE,
                "Changed name of audience with ID {} to '{}'.".format(self.id, self.name),
            )

    def can_archive(self):
        if self.get_ad_groups_using_audience():
            return False
        return True

    def get_ad_groups_using_audience(self):
        #  Circular import workaround
        import core.models.ad_group

        ad_groups_using_audience = core.models.ad_group.AdGroup.objects.filter(
            campaign__account_id=self.pixel.account_id
        ).filter(
            Q(settings__audience_targeting__contains=self.id)
            | Q(settings__exclusion_audience_targeting__contains=self.id)
        )
        return ad_groups_using_audience

    def add_to_history(self, user, action_type, history_changes_text):
        self.pixel.account.write_history(history_changes_text, changes=None, action_type=action_type, user=user)

    def _save(self, *args, **kwargs):
        """Proxy method for the parent method, which must be used in methods"""
        super().save(args, kwargs)

    def save(self, *args, **kwargs):
        raise exc.ForbiddenError("Using the save method directly is prohibited.")
