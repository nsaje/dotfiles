from . import validation


class PublisherGroupsEntryMixin(object):
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        validation.validate_placement(self.placement)

        return super().save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields
        )
