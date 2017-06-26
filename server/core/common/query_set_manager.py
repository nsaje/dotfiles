# -*- coding: utf-8 -*-

from django.db import models


class QuerySetManager(models.Manager):

    def get_queryset(self):
        return self.model.QuerySet(self.model)

    def create_unsafe(self, *args, **kwargs):
        """ Provides access to Django's create() method.

            This means no validation will be performed and no other systems will be notified
            of the creation of this object.
        """
        return super(QuerySetManager, self).create(*args, **kwargs)
