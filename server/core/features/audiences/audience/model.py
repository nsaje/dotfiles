from django.conf import settings
from django.db import models

import core.models

from . import instance
from . import manager
from . import validation


class Audience(validation.AudienceValidatorMixin, instance.AudienceInstanceMixin, models.Model):
    class Meta:
        app_label = "dash"

    objects = manager.AudienceManager()

    _settings_fields = ["name", "archived"]
    _permissioned_fields = {}

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    pixel = models.ForeignKey(core.models.ConversionPixel, on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    ttl = models.PositiveSmallIntegerField()
    prefill_days = models.PositiveSmallIntegerField(default=0)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT)
