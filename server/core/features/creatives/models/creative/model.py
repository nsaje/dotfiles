from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

import dash.constants

from . import entity_permission
from . import instance
from . import manager
from . import queryset
from . import validation


class Creative(
    entity_permission.EntityPermissionMixin,
    instance.CreativeInstanceMixin,
    validation.CreativeValidatorMixin,
    models.Model,
):
    class Meta:
        app_label = "dash"

    objects = manager.CreativeManager.from_queryset(queryset.CreativeQuerySet)()

    _update_fields = []

    agency = models.ForeignKey("Agency", null=True, blank=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, on_delete=models.PROTECT)

    type = models.IntegerField(default=dash.constants.AdType.CONTENT, choices=dash.constants.AdType.get_choices())

    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)
    display_url = models.CharField(max_length=35, blank=True, default="")
    brand_name = models.CharField(max_length=25, blank=True, default="")
    description = models.CharField(max_length=150, blank=True, default="")
    call_to_action = models.CharField(max_length=25, blank=True, default="")

    tags = models.ManyToManyField("CreativeTag")

    batch = models.ForeignKey("CreativeBatch", null=True, blank=True, on_delete=models.PROTECT)

    image = models.ForeignKey("ImageAsset", null=True, on_delete=models.PROTECT)
    image_crop = models.CharField(max_length=25, default=dash.constants.ImageCrop.CENTER)
    icon = models.ForeignKey("ImageAsset", null=True, related_name="creatives", on_delete=models.PROTECT)
    video_asset = models.ForeignKey("VideoAsset", null=True, blank=True, on_delete=models.PROTECT)
    ad_tag = models.TextField(null=True, blank=True)

    trackers = JSONField(null=True, blank=True)

    additional_data = JSONField(null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Created by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Modified by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
