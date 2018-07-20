from django.db import models


class BaseManager(models.Manager):
    def create_unsafe(self, *args, **kwargs):
        """ Provides access to Django's create() method.

            This means no validation will be performed and no other systems will be notified
            of the creation of this object.
        """
        return super(BaseManager, self).create(*args, **kwargs)
