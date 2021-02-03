from django.db import transaction


class CreativeCandidateInstanceMixin(object):
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def update(self, **updates):
        cleaned_updates = self._clean_updates(updates)
        if not cleaned_updates:
            return

        self._apply_updates(cleaned_updates)
        self.save()

    def _clean_updates(self, updates):
        new_updates = {}
        for field, value in list(updates.items()):
            if field in set(self._update_fields) and value != getattr(self, field):
                new_updates[field] = value
        return new_updates

    def _apply_updates(self, updates):
        for field, value in list(updates.items()):
            setattr(self, field, value)
