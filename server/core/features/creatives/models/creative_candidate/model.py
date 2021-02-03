from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.functional import cached_property

import core.models.tags.creative.shortcuts
import dash.constants

from . import instance
from . import manager
from . import queryset
from . import validation


class CreativeCandidate(
    core.models.tags.creative.shortcuts.CreativeTagMixin,
    instance.CreativeCandidateInstanceMixin,
    validation.CreativeCandidateValidatorMixin,
    models.Model,
):
    class Meta:
        app_label = "dash"

    objects = manager.CreativeCandidateManager.from_queryset(queryset.CreativeCandidateQuerySet)()

    _update_fields = [
        "url",
        "title",
        "display_url",
        "brand_name",
        "description",
        "call_to_action",
        "image_url",
        "image_crop",
        "icon_url",
        "video_asset",
        "ad_tag",
        "trackers",
        "trackers_status",
        "image_status",
        "icon_status",
        "url_status",
        "additional_data",
        "original_creative",
        "image_id",
        "image_width",
        "image_height",
        "image_hash",
        "image_file_size",
        "icon_id",
        "icon_width",
        "icon_height",
        "icon_hash",
        "icon_file_size",
    ]

    batch = models.ForeignKey("CreativeBatch", on_delete=models.PROTECT)

    url = models.TextField(null=True, blank=True, default="")
    title = models.TextField(null=True, blank=True, default="")
    display_url = models.TextField(null=True, blank=True, default="")
    brand_name = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")
    call_to_action = models.TextField(null=True, blank=True, default="")

    image_url = models.TextField(null=True, blank=True, default=None)
    image_crop = models.TextField(null=True, blank=True, default=dash.constants.ImageCrop.CENTER)
    icon_url = models.TextField(null=True, blank=True, default=None)
    video_asset = models.ForeignKey("VideoAsset", blank=True, null=True, on_delete=models.PROTECT)
    ad_tag = models.TextField(null=True, blank=True)

    trackers = JSONField(null=True, blank=True)
    trackers_status = JSONField(null=True, blank=True)

    image_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )
    icon_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )
    url_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )

    image_id = models.CharField(max_length=256, null=True, blank=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    image_hash = models.CharField(max_length=128, null=True, blank=True)
    image_file_size = models.PositiveIntegerField(null=True, blank=True)

    icon_id = models.CharField(max_length=256, null=True, blank=True)
    icon_width = models.PositiveIntegerField(null=True, blank=True)
    icon_height = models.PositiveIntegerField(null=True, blank=True)
    icon_hash = models.CharField(max_length=128, null=True, blank=True)
    icon_file_size = models.PositiveIntegerField(null=True, blank=True)

    original_creative = models.ForeignKey("Creative", null=True, blank=True, on_delete=models.CASCADE)

    additional_data = JSONField(null=True, blank=True)

    @cached_property
    def type(self):
        return self.batch.ad_type

    def get_agency(self):
        return self.batch.agency

    def get_account(self):
        return self.batch.account
