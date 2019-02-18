from django.contrib.postgres.fields import JSONField
from django.db import models

import core.common
import dash.constants

from . import instance


class ContentAdCandidate(instance.ContentAdCandidateMixin, core.common.FootprintModel):
    class Meta:
        app_label = "dash"

    label = models.TextField(null=True, blank=True, default="")
    url = models.TextField(null=True, blank=True, default="")
    title = models.TextField(null=True, blank=True, default="")
    image_url = models.TextField(null=True, blank=True, default=None)
    image_crop = models.TextField(null=True, blank=True, default=dash.constants.ImageCrop.CENTER)
    type = models.IntegerField(choices=dash.constants.AdType.get_choices(), default=dash.constants.AdType.CONTENT)

    video_asset = models.ForeignKey("VideoAsset", blank=True, null=True, on_delete=models.PROTECT)
    ad_tag = models.TextField(null=True, blank=True)

    display_url = models.TextField(null=True, blank=True, default="")
    brand_name = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")
    call_to_action = models.TextField(null=True, blank=True, default=dash.constants.DEFAULT_CALL_TO_ACTION)

    primary_tracker_url = models.TextField(null=True, blank=True, default=None)
    secondary_tracker_url = models.TextField(null=True, blank=True, default=None)

    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT, null=True, blank=True)
    batch = models.ForeignKey("UploadBatch", on_delete=models.PROTECT)

    image_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )
    url_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )
    primary_tracker_url_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )
    secondary_tracker_url_status = models.IntegerField(
        choices=dash.constants.AsyncUploadJobStatus.get_choices(),
        default=dash.constants.AsyncUploadJobStatus.PENDING_START,
    )
    can_append_tracking_codes = models.BooleanField(default=False)

    image_id = models.CharField(max_length=256, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)
    image_file_size = models.PositiveIntegerField(null=True)

    original_content_ad = models.ForeignKey("ContentAd", null=True, on_delete=models.CASCADE)

    additional_data = JSONField(null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
