from django.db import transaction


class CreativeBatchInstanceMixin(object):
    def save(self, request=None, *args, **kwargs):
        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def update(self, request, **updates):
        cleaned_updates = self._clean_updates(updates)
        if not cleaned_updates:
            return

        self._apply_updates(cleaned_updates)
        self.save(request)

    def _clean_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in list(updates.items()):
            setattr(self, field, value)
