import tagulous.models
from django.contrib.postgres.fields import JSONField
from django.db import models

import dash.constants

from . import manager
from . import queryset
from . import validation


class CreativeCandidate(validation.CreativeCandidateValidatorMixin, models.Model):
    class Meta:
        app_label = "dash"

    objects = manager.CreativeCandidateManager.from_queryset(queryset.CreativeCandidateQuerySet)()

    type = models.IntegerField(choices=dash.constants.AdType.get_choices(), default=dash.constants.AdType.CONTENT)

    url = models.TextField(null=True, blank=True, default="")
    title = models.TextField(null=True, blank=True, default="")
    display_url = models.TextField(null=True, blank=True, default="")
    brand_name = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")
    call_to_action = models.TextField(null=True, blank=True, default="")

    tags = tagulous.models.TagField(to="CreativeTag", blank=True)

    batch = models.ForeignKey("CreativeBatch", on_delete=models.PROTECT)

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

    image_id = models.CharField(max_length=256, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)
    image_file_size = models.PositiveIntegerField(null=True)

    icon_id = models.CharField(max_length=256, null=True)
    icon_width = models.PositiveIntegerField(null=True)
    icon_height = models.PositiveIntegerField(null=True)
    icon_hash = models.CharField(max_length=128, null=True)
    icon_file_size = models.PositiveIntegerField(null=True)

    original_creative = models.ForeignKey("Creative", null=True, on_delete=models.CASCADE)

    additional_data = JSONField(null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
