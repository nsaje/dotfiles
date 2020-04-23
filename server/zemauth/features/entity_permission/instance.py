from django.db import transaction


class EntityPermissionMixin(object):
    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
