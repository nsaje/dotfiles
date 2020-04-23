# -*- coding: utf-8 -*-

from django.db import models
from django.db import transaction

from . import model


class EntityPermissionManager(models.Manager):
    @transaction.atomic
    def create(self, user, permission, agency=None, account=None):
        item = self._prepare(user, permission, agency, account)
        item.save()
        return item

    @staticmethod
    def _prepare(user, permission, agency=None, account=None):
        item = model.EntityPermission(user=user, agency=agency, account=account, permission=permission)
        return item
