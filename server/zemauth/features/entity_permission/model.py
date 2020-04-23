# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from . import constants
from . import instance
from . import manager
from . import queryset
from . import validation


class EntityPermission(instance.EntityPermissionMixin, validation.EntityPermissionValidatorMixin, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    agency = models.ForeignKey("dash.Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("dash.Account", null=True, blank=True, on_delete=models.PROTECT)
    permission = models.CharField(max_length=128, choices=constants.Permission.get_choices())

    objects = manager.EntityPermissionManager.from_queryset(queryset.EntityPermissionQuerySet)()
