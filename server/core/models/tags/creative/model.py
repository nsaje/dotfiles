import tagulous.models
import tagulous.settings
from django.db import models

from . import instance
from . import manager
from . import queryset
from . import validation


class CreativeTag(instance.CreativeTagMixin, validation.CreativeTagValidatorMixin, tagulous.models.TagTreeModel):
    class Meta:
        app_label = "dash"
        ordering = ("name",)
        unique_together = (("name", "agency"), ("name", "account"))

    objects = manager.CreativeTagManager.from_queryset(queryset.CreativeTagQuerySet)()

    # We must guarantee tag uniqueness only on agency or account level
    name = models.CharField(unique=False, max_length=tagulous.settings.NAME_MAX_LENGTH)

    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)
