# -*- coding: utf-8 -*-
import urllib.parse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db import transaction

import core.models.helpers
import utils.demo_anonymizer
import utils.redirector
import utils.string_helper
from core.models.image_asset import ImageAsset
from dash import constants
from dash import image_helper

from . import entity_permission
from . import instance
from . import manager
from . import prodops_mixin
from . import queryset
from . import validation


class ContentAd(
    entity_permission.EntityPermissionMixin,
    validation.ContentAdValidatorMixin,
    instance.ContentAdInstanceMixin,
    models.Model,
    prodops_mixin.ProdopsMixin,
):
    class Meta:
        get_latest_by = "created_dt"
        app_label = "dash"

    _demo_fields = {
        "url": utils.demo_anonymizer.fake_content_ad_url,
        "display_url": utils.demo_anonymizer.fake_display_url,
        "brand_name": utils.demo_anonymizer.fake_brand,
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

    icon = models.ForeignKey(ImageAsset, null=True, on_delete=models.PROTECT)

    video_asset = models.ForeignKey("VideoAsset", blank=True, null=True, on_delete=models.PROTECT)
    ad_tag = models.TextField(null=True, blank=True)

    document_id = models.BigIntegerField(null=True, blank=True)
    document_features = JSONField(null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    state = models.IntegerField(
        null=True, default=constants.ContentAdSourceState.ACTIVE, choices=constants.ContentAdSourceState.get_choices()
    )

    archived = models.BooleanField(default=False)
    tracker_urls = ArrayField(models.CharField(max_length=2048), null=True)
    trackers = JSONField(null=True, blank=True)

    additional_data = JSONField(null=True, blank=True)
    amplify_review = models.NullBooleanField(default=None)

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_base_image_url(self, width=None, height=None):
        if self.image_id is None:
            return None

        return urllib.parse.urljoin(settings.IMAGE_THUMBNAIL_URL, "{image_id}.jpg".format(image_id=self.image_id))

    def get_image_url(self, width=None, height=None):
        if width is None:
            width = self.image_width

        if height is None:
            height = self.image_height

        return image_helper.get_image_url(self.image_id, width, height, self.image_crop)

    def get_base_icon_url(self):
        if self.icon is None:
            return None

        return self.icon.get_base_url()

    def get_icon_url(self, size=None):
        if not self.icon:
            return None

        if size is None:
            size = self.icon.width

        return self.icon.get_url(width=size, height=size)

    def get_hosted_icon_url(self, size=None):
        icon_url = self.get_icon_url(size) or self.ad_group.campaign.account.settings.get_default_icon_url(size)
        if icon_url:
            return icon_url

        return core.models.helpers.get_hosted_default_icon_url(self, size)

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
        return utils.redirector.construct_redirector_url(
            self.ad_group_id,
            self.id,
            self.ad_group.campaign_id,
            self.ad_group.campaign.account_id,
            landing_page_url=self.url,
            use_https=True,
            ga_tracking_enabled=self.ad_group.campaign.settings.enable_ga_tracking,
            adobe_tracking_enabled=self.ad_group.campaign.settings.enable_adobe_tracking,
            tracking_codes=self.ad_group.settings.get_tracking_codes(),
            adobe_tracking_param=self.ad_group.campaign.settings.adobe_tracking_param,
            bid_id="68f81ef4-6bb2-11eb-a67c-6edbe9a2cbeb",  # dummy bid id to fill {postclick} macro correctly
        )

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
            "icon_id": self.icon.image_id if self.icon else None,
            "icon_hash": self.icon.image_hash if self.icon else None,
            "icon_width": self.icon.width if self.icon else None,
            "icon_height": self.icon.height if self.icon else None,
            "icon_file_size": self.icon.file_size if self.icon else None,
            "video_asset_id": str(self.video_asset.id) if self.video_asset else None,
            "ad_tag": self.ad_tag,
            "display_url": self.display_url,
            "description": self.description,
            "brand_name": self.brand_name,
            "call_to_action": self.call_to_action,
            "primary_tracker_url": self.tracker_urls[0] if self.tracker_urls else None,
            "secondary_tracker_url": self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
            "trackers": self.trackers,
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
            "state",
            "tracker_urls",
            "trackers",
            "video_asset_id",
            "ad_tag",
        )
        candidate = {
            "original_content_ad_id": self.id,
            "primary_tracker_url": self.tracker_urls[0] if self.tracker_urls else None,
            "secondary_tracker_url": self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
        }

        for field in fields:
            candidate[field] = getattr(self, field)

        if self.icon:
            candidate["icon_id"] = self.icon.image_id
            candidate["icon_hash"] = self.icon.image_hash
            candidate["icon_width"] = self.icon.width
            candidate["icon_height"] = self.icon.height
            candidate["icon_file_size"] = self.icon.file_size
            candidate["icon_url"] = self.icon.origin_url

        return candidate

    objects = manager.ContentAdManager.from_queryset(queryset.ContentAdQuerySet)()
