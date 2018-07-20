# -*- coding: utf-8 -*-
from django.contrib.postgres.fields import JSONField
from django.db import models

from dash import constants
from dash import image_helper

import core.common


class ContentAdCandidate(core.common.FootprintModel):
    class Meta:
        app_label = "dash"

    label = models.TextField(null=True, blank=True, default="")
    url = models.TextField(null=True, blank=True, default="")
    title = models.TextField(null=True, blank=True, default="")
    image_url = models.TextField(null=True, blank=True, default=None)
    image_crop = models.TextField(null=True, blank=True, default=constants.ImageCrop.CENTER)

    video_asset = models.ForeignKey("VideoAsset", blank=True, null=True, on_delete=models.PROTECT)

    display_url = models.TextField(null=True, blank=True, default="")
    brand_name = models.TextField(null=True, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="")
    call_to_action = models.TextField(null=True, blank=True, default=constants.DEFAULT_CALL_TO_ACTION)

    primary_tracker_url = models.TextField(null=True, blank=True, default=None)
    secondary_tracker_url = models.TextField(null=True, blank=True, default=None)

    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT, null=True, blank=True)
    batch = models.ForeignKey("UploadBatch", on_delete=models.PROTECT)

    image_status = models.IntegerField(
        choices=constants.AsyncUploadJobStatus.get_choices(), default=constants.AsyncUploadJobStatus.PENDING_START
    )
    url_status = models.IntegerField(
        choices=constants.AsyncUploadJobStatus.get_choices(), default=constants.AsyncUploadJobStatus.PENDING_START
    )

    image_id = models.CharField(max_length=256, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)

    original_content_ad = models.ForeignKey("ContentAd", null=True)

    additional_data = JSONField(null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "url": self.url,
            "title": self.title,
            "image_url": self.image_url,
            "image_id": self.image_id,
            "image_hash": self.image_hash,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "image_crop": self.image_crop,
            "video_asset_id": str(self.video_asset.id) if self.video_asset else None,
            "display_url": self.display_url,
            "description": self.description,
            "brand_name": self.brand_name,
            "call_to_action": self.call_to_action,
            "image_status": self.image_status,
            "url_status": self.url_status,
            "hosted_image_url": self.get_image_url(360, 360),
            "primary_tracker_url": self.primary_tracker_url,
            "secondary_tracker_url": self.secondary_tracker_url,
            "additional_data": self.additional_data,
        }

    def get_image_url(self, width=None, height=None):
        if width is None:
            width = self.image_width

        if height is None:
            height = self.image_height

        return image_helper.get_image_url(self.image_id, width, height, self.image_crop)
