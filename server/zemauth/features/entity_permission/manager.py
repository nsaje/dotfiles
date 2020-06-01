# -*- coding: utf-8 -*-

from django.db import models
from django.db import transaction


class EntityPermissionManager(models.Manager):
    @transaction.atomic
    def create(self, user, permission, agency=None, account=None):
        """
        Create a new object with the given kwargs, saving it to the database if necessary
        and returning the created object.
        """
        item, _ = self.get_or_create(user=user, agency=agency, account=account, permission=permission)
        return item
