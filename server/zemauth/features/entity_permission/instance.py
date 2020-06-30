from django.db import transaction


class EntityPermissionMixin(object):
    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        self.user.invalidate_entity_permission_cache()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.user.invalidate_entity_permission_cache()
        super(EntityPermissionMixin, self).delete(using=using, keep_parents=keep_parents)
