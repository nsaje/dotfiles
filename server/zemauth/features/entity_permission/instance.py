from django.db import transaction

from zemauth.features.entity_permission.constants import REPORTING_PERMISSIONS


class EntityPermissionMixin(object):
    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        self.user.invalidate_entity_permission_cache()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.user.invalidate_entity_permission_cache()
        super(EntityPermissionMixin, self).delete(using=using, keep_parents=keep_parents)

    def is_reporting_permission(self) -> bool:
        return self.permission in REPORTING_PERMISSIONS
