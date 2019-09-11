# -*- coding: utf-8 -*-
import urllib.parse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db import transaction

import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from dash import image_helper

from . import instance
from . import manager
from . import prodops_mixin
from . import queryset
from . import validation


class ContentAd(
    validation.ContentAdValidatorMixin, instance.ContentAdInstanceMixin, models.Model, prodops_mixin.ProdopsMixin
):
    class Meta:
        get_latest_by = "created_dt"
        app_label = "dash"

    _demo_fields = {
        "url": utils.demo_anonymizer.fake_content_ad_url,
        "display_url": utils.demo_anonymizer.fake_display_url,
        "brand_name": utils.demo_anonymizer.fake_brand,
        "redirect_id": lambda: "u1jvpq0wthxc",
        "tracker_urls": lambda: [],
    }

    label = models.CharField(max_length=256, default="")
    url = models.CharField(max_length=2048, editable=False)
    title = models.CharField(max_length=256, editable=False)
    display_url = models.CharField(max_length=35, blank=True, default="")
    brand_name = models.CharField(max_length=25, blank=True, default="")
    description = models.CharField(max_length=150, blank=True, default="")
    call_to_action = models.CharField(max_length=25, blank=True, default="")
    type = models.IntegerField(choices=constants.AdType.get_choices(), default=constants.AdType.CONTENT)

    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT)
    batch = models.ForeignKey("UploadBatch", on_delete=models.PROTECT)
    sources = models.ManyToManyField("Source", through="ContentAdSource")

    image_id = models.CharField(max_length=256, editable=False, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)
    image_file_size = models.PositiveIntegerField(null=True)
    crop_areas = models.CharField(max_length=128, null=True)
    image_crop = models.CharField(max_length=25, default=constants.ImageCrop.CENTER)
    image_present = models.BooleanField(default=True)

    icon_id = models.CharField(max_length=256, editable=False, null=True)
    icon_size = models.PositiveIntegerField(null=True)
    icon_hash = models.CharField(max_length=128, null=True)
    icon_file_size = models.PositiveIntegerField(null=True)

    video_asset = models.ForeignKey("VideoAsset", blank=True, null=True, on_delete=models.PROTECT)
    ad_tag = models.TextField(null=True, blank=True)

    document_id = models.BigIntegerField(null=True, blank=True)
    document_features = JSONField(null=True, blank=True)

    redirect_id = models.CharField(max_length=128, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    state = models.IntegerField(
        null=True, default=constants.ContentAdSourceState.ACTIVE, choices=constants.ContentAdSourceState.get_choices()
    )

    archived = models.BooleanField(default=False)
    tracker_urls = ArrayField(models.CharField(max_length=2048), null=True)

    additional_data = JSONField(null=True, blank=True)
    amplify_review = models.NullBooleanField(default=None)

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_original_image_url(self, width=None, height=None):
        if self.image_id is None:
            return None

        return urllib.parse.urljoin(settings.IMAGE_THUMBNAIL_URL, "{image_id}.jpg".format(image_id=self.image_id))

    def get_image_url(self, width=None, height=None):
        if width is None:
            width = self.image_width

        if height is None:
            height = self.image_height

        return image_helper.get_image_url(self.image_id, width, height, self.image_crop)

    def get_original_icon_url(self, size=None):
        if self.icon_id is None:
            return None

        return urllib.parse.urljoin(settings.IMAGE_THUMBNAIL_URL, "{icon_id}.jpg".format(icon_id=self.icon_id))

    def get_icon_url(self, size=None):
        if size is None:
            size = self.icon_size

        return image_helper.get_image_url(self.icon_id, size, size, constants.ImageCrop.CENTER)

    def url_with_tracking_codes(self, tracking_codes):
        if not tracking_codes:
            return self.url

        parsed = list(urllib.parse.urlparse(self.url))

        parts = []
        if parsed[4]:
            parts.append(parsed[4])
        parts.append(tracking_codes)

        parsed[4] = "&".join(parts)

        return urllib.parse.urlunparse(parsed)

    def get_url(self, ad_group):
        return self.url

    def get_redirector_url(self):
        return settings.R1_BLANK_REDIRECT_URL.format(redirect_id=self.redirect_id, content_ad_id=self.id)

    def get_sspd_url(self):
        if self.id:
            return settings.SSPD_CONTENT_AD_REDIRECT_URL.format(id=self.id)
        else:
            return "N/A"

    def get_creative_size(self):
        if self.image_width and self.image_height:
            return str(self.image_width) + "x" + str(self.image_height)
        else:
            return "N/A"

    def __str__(self):
        return "{cn}(id={id}, ad_group={ad_group}, image_id={image_id}, state={state})".format(
            cn=self.__class__.__name__, id=self.id, ad_group=self.ad_group, image_id=self.image_id, state=self.state
        )

    def to_candidate_dict(self):
        return {
            "label": self.label,
            "url": self.url,
            "title": self.title,
            "type": self.type,
            "image_url": self.get_image_url(),
            "image_id": self.image_id,
            "image_hash": self.image_hash,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "image_crop": self.image_crop,
            "icon_url": self.get_icon_url(),
            "icon_id": self.icon_id,
            "icon_hash": self.icon_hash,
            "icon_width": self.icon_size,
            "icon_height": self.icon_size,
            "video_asset_id": str(self.video_asset.id) if self.video_asset else None,
            "ad_tag": self.ad_tag,
            "display_url": self.display_url,
            "description": self.description,
            "brand_name": self.brand_name,
            "call_to_action": self.call_to_action,
            "primary_tracker_url": self.tracker_urls[0] if self.tracker_urls else None,
            "secondary_tracker_url": self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
        }

    def to_cloned_candidate_dict(self):
        fields = (
            "label",
            "url",
            "title",
            "type",
            "display_url",
            "brand_name",
            "description",
            "call_to_action",
            "image_id",
            "image_width",
            "image_height",
            "image_hash",
            "crop_areas",
            "image_crop",
            "image_present",
            "icon_id",
            "icon_hash",
            "state",
            "tracker_urls",
            "video_asset_id",
            "ad_tag",
        )
        candidate = {
            "primary_tracker_url": self.tracker_urls[0] if self.tracker_urls else None,
            "secondary_tracker_url": self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
        }

        for field in fields:
            candidate[field] = getattr(self, field)

        for field in ["icon_width", "icon_height"]:
            candidate[field] = getattr(self, "icon_size")

        return candidate

    objects = manager.ContentAdManager.from_queryset(queryset.ContentAdQuerySet)()
