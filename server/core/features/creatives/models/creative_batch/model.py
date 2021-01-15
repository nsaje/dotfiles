from django.conf import settings
from django.db import models

import core.models.tags.creative.shortcuts
import dash.constants

from . import instance
from . import manager
from . import queryset
from . import validation


class CreativeBatch(
    core.models.tags.creative.shortcuts.CreativeTagMixin,
    instance.CreativeBatchInstanceMixin,
    validation.CreativeBatchValidatorMixin,
    models.Model,
):
    class Meta:
        app_label = "dash"

    objects = manager.CreativeBatchManager.from_queryset(queryset.CreativeBatchQuerySet)()

    _update_fields = [
        "name",
        "status",
        "original_filename",
        "image_crop",
        "display_url",
        "brand_name",
        "description",
        "call_to_action",
    ]

    name = models.CharField(max_length=1024)

    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)

    status = models.IntegerField(
        default=dash.constants.CreativeBatchStatus.IN_PROGRESS, choices=dash.constants.CreativeBatchStatus.get_choices()
    )

    original_filename = models.CharField(max_length=1024, null=False, default="", blank=True)

    image_crop = models.TextField(null=True, blank=True, default=dash.constants.ImageCrop.CENTER)
    display_url = models.TextField(null=True, blank=True, default="")
    brand_name = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")
    call_to_action = models.TextField(null=True, blank=True, default="")

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Created by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
