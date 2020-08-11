# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from . import constants
from . import instance
from . import manager
from . import queryset
from . import validation


class EntityPermission(instance.EntityPermissionMixin, validation.EntityPermissionValidatorMixin, models.Model):
    class Meta:
        unique_together = (("user", "agency", "permission"), ("user", "account", "permission"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    agency = models.ForeignKey("dash.Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("dash.Account", null=True, blank=True, on_delete=models.PROTECT)
    permission = models.CharField(max_length=128, choices=constants.Permission.get_choices(), db_index=True)

    objects = manager.EntityPermissionManager.from_queryset(queryset.EntityPermissionQuerySet)()

    def __str__(self):
        if self.account_id is not None:
            where = "account " + str(self.account_id)
        elif self.agency_id is not None:
            where = "agency " + str(self.agency_id)
        else:
            where = "all accounts"

        return "permission %s on %s" % (self.permission, where)

    def __eq__(self, other):
        return (
            self.user_id == other.user_id
            and self.account_id == other.account_id
            and self.agency_id == other.agency_id
            and self.permission == other.permission
        )

    def __hash__(self):
        return (
            self.user_id.__hash__()
            ^ self.account_id.__hash__()
            ^ self.agency_id.__hash__()
            ^ self.permission.__hash__()
        )
