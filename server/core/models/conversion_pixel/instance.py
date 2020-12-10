from django.db import transaction

import dash.constants
import utils.exc
import utils.k1_helper
import utils.redirector

from . import model


class ConversionPixelInstanceMixin:
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
            utils.k1_helper.update_account(self.account, msg="conversion_pixel.update")

        if not skip_propagation and "redirect_url" in changes:
            utils.redirector.update_pixel(self)

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
        self.save()

    def _write_change_history(self, request, changes):
        if "archived" in changes:
            changes_text = "{} conversion pixel named {}.".format(
                "Archived" if self.archived else "Restored", self.name
            )
            self.account.write_history(
                changes_text,
                user=request.user,
                action_type=dash.constants.HistoryActionType.CONVERSION_PIXEL_ARCHIVE_RESTORE,
            )

        if "redirect_url" in changes:
            if self.redirect_url:
                changes_text = "Set redirect url of pixel named {} to {}.".format(self.name, self.redirect_url)
            else:
                changes_text = "Removed redirect url of pixel named {}.".format(self.name)
            self.account.write_history(
                changes_text,
                user=request.user,
                action_type=dash.constants.HistoryActionType.CONVERSION_PIXEL_SET_REDIRECT_URL,
            )

        if "name" in changes:
            changes_text = "Renamed conversion pixel with ID {} to {}.".format(self.id, self.name)
            self.account.write_history(
                changes_text, user=request.user, action_type=dash.constants.HistoryActionType.CONVERSION_PIXEL_RENAME
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.slug == self._SLUG_PLACEHOLDER or not self.slug:
            # if slug is not provided, id is used as a slug.
            # This is here for backwards compatibility. When
            # none of the pixels with actual string slugs are no
            # longer in use, we can get rid of the slugs altogether
            # and use ids instead.
            model.ConversionPixel.objects.filter(pk=self.id).update(slug=str(self.id))
            self.refresh_from_db()
