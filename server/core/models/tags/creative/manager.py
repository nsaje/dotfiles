import tagulous.models.models

from . import queryset


class CreativeTagManager(tagulous.models.models.TagTreeModelManager):
    def get_queryset(self):
        return queryset.CreativeTagQuerySet(self.model, using=self._db)

    def create(self, name, agency=None, account=None):
        """
        Create a new object with the given params, saving it to the database if necessary
        and returning the created object.
        """
        item, _ = self.get_or_create(name=name, agency=agency, account=account)
        return item
