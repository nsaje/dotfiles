from django.db import transaction


class DirectDealMixin(object):
    @transaction.atomic
    def save(self, request=None, *args, **kwargs):
        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
            self.modified_by = request.user

        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def update(self, request, **kwargs):
        updates = self._clean_updates(request, kwargs)
        if not updates:
            return

        # TODO (msuber): add history support
        self._apply_updates_and_save(request, updates)

    def _clean_updates(self, request, updates):
        user = request.user if request else None
        cleaned_updates = {}

        for field, value in list(updates.items()):
            required_permission = self._permissioned_fields.get(field)
            if required_permission and not (user is None or user.has_perm(required_permission)):
                continue
            if field in set(self._settings_fields) and value != getattr(self, field):
                cleaned_updates[field] = value

        return cleaned_updates

    def _apply_updates_and_save(self, request, changes):
        for field, value in list(changes.items()):
            if field in self._settings_fields:
                setattr(self, field, value)
        self.save(request)
