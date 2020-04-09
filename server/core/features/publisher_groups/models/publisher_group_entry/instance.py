class PublisherGroupsEntryMixin(object):
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.placement == "":
            raise ValueError("Placement must not be empty")
        return super().save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields
        )
