from django.db import models

from . import instance
from . import manager
from . import queryset
from . import validation


class CreativeTag(instance.CreativeTagMixin, validation.CreativeTagValidatorMixin, models.Model):
    class Meta:
        app_label = "dash"
        ordering = ("name",)
        unique_together = (("name", "agency"), ("name", "account"))

    objects = manager.CreativeTagManager.from_queryset(queryset.CreativeTagQuerySet)()

    name = models.CharField(max_length=255)

    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)
