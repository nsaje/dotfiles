# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models

from . import entity_permission
from . import instance
from . import manager
from . import queryset
from . import validation


class PublisherGroup(
    entity_permission.EntityPermissionMixin,
    validation.PublisherGroupValidatorMixin,
    instance.PublisherGroupMixin,
    models.Model,
):
    class Meta:
        app_label = "dash"
        ordering = ("pk",)

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, editable=True, blank=False, null=False)

    # it can be defined per account, agency or globally
    account = models.ForeignKey("Account", on_delete=models.PROTECT, null=True, blank=True)
    agency = models.ForeignKey("Agency", on_delete=models.PROTECT, null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )

    implicit = models.BooleanField(default=False)
    default_include_subdomains = models.BooleanField(default=True)

    objects = manager.PublisherGroupManager.from_queryset(queryset.PublisherGroupQuerySet)()

    def __str__(self):
        return "{} ({})".format(self.name, self.id)
