from django.db import models


class CreativeTagManager(models.Manager):
    def create(self, name, agency=None, account=None):
        """
        Create a new object with the given params, saving it to the database if necessary
        and returning the created object.
        """
        item, _ = self.get_or_create(name=name, agency=agency, account=account)
        return item
