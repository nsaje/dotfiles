# -*- coding: utf-8 -*-
import urllib.parse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models, transaction

import utils.redirector_helper
import utils.demo_anonymizer
import utils.string_helper

from dash import constants
from dash import image_helper

import core.common
import core.entity
import core.history
import core.source

from . import prodops_mixin
from . import instance


class ContentAdManager(models.Manager):
    def _create(self, batch, sources, **kwargs):
        content_ad = ContentAd(
            ad_group=batch.ad_group,
            batch=batch,
            amplify_review=batch.ad_group.amplify_review and settings.AMPLIFY_REVIEW,
        )

        for field in kwargs:
            if not hasattr(content_ad, field):
                continue
            setattr(content_ad, field, kwargs[field])

        content_ad.save()

        core.entity.ContentAdSource.objects.bulk_create(content_ad, sources)

        return content_ad

    @transaction.atomic
    def create(self, batch, sources, r1_resolve=True, **kwargs):
        content_ad = self._create(batch, sources, **kwargs)
        self.insert_redirects([content_ad], clickthrough_resolve=r1_resolve)
        return content_ad

    @transaction.atomic
    def bulk_create_from_candidates(self, candidate_dicts, batch, r1_resolve=True):
        ad_group_sources = core.entity.AdGroupSource.objects.filter(
            ad_group=batch.ad_group
        ).filter_can_manage_content_ads()
        sources = core.source.Source.objects.filter(id__in=ad_group_sources.values_list("source_id", flat=True))

        content_ads = []
        for candidate in candidate_dicts:
            content_ads.append(self._create(batch, sources, **candidate))

        self.insert_redirects(content_ads, clickthrough_resolve=r1_resolve)

        return content_ads

    def bulk_clone(self, request, source_content_ads, ad_group, batch, overridden_state=None):
        candidates = [x.to_cloned_candidate_dict() for x in source_content_ads]
        if overridden_state is not None:
            for x in candidates:
                x["state"] = overridden_state

        # no need to resolve url in r1, because it was done before it was uploaded
        content_ads = self.bulk_create_from_candidates(candidates, batch, r1_resolve=False)
        ad_group.write_history_content_ads_cloned(
            request, content_ads, batch, source_content_ads[0].ad_group, overridden_state
        )

        return content_ads

    @transaction.atomic
    def insert_redirects(self, content_ads, clickthrough_resolve):
        redirector_batch = utils.redirector_helper.insert_redirects(
            content_ads, clickthrough_resolve=clickthrough_resolve
        )
        for content_ad in content_ads:
            content_ad.url = redirector_batch[str(content_ad.id)]["redirect"]["url"]
            content_ad.redirect_id = redirector_batch[str(content_ad.id)]["redirectid"]
            content_ad.save()


class ContentAd(models.Model, prodops_mixin.ProdopsMixin, instance.ContentAdInstanceMixin):
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

    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT)
    batch = models.ForeignKey("UploadBatch", on_delete=models.PROTECT)
    sources = models.ManyToManyField(core.source.Source, through="ContentAdSource")

    image_id = models.CharField(max_length=256, editable=False, null=True)
    image_width = models.PositiveIntegerField(null=True)
    image_height = models.PositiveIntegerField(null=True)
    image_hash = models.CharField(max_length=128, null=True)
    crop_areas = models.CharField(max_length=128, null=True)
    image_crop = models.CharField(max_length=25, default=constants.ImageCrop.CENTER)

    video_asset = models.ForeignKey("VideoAsset", blank=True, null=True, on_delete=models.PROTECT)

    redirect_id = models.CharField(max_length=128, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    state = models.IntegerField(
        null=True, default=constants.ContentAdSourceState.ACTIVE, choices=constants.ContentAdSourceState.get_choices()
    )

    archived = models.BooleanField(default=False)
    tracker_urls = ArrayField(models.CharField(max_length=2048), null=True)

    additional_data = JSONField(null=True, blank=True)
    amplify_review = models.NullBooleanField(default=None)

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

    def __str__(self):
        return "{cn}(id={id}, ad_group={ad_group}, image_id={image_id}, state={state})".format(
            cn=self.__class__.__name__, id=self.id, ad_group=self.ad_group, image_id=self.image_id, state=self.state
        )

    def to_candidate_dict(self):
        return {
            "label": self.label,
            "url": self.url,
            "title": self.title,
            "image_url": self.get_image_url(),
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
            "primary_tracker_url": self.tracker_urls[0] if self.tracker_urls else None,
            "secondary_tracker_url": self.tracker_urls[1] if self.tracker_urls and len(self.tracker_urls) > 1 else None,
        }

    def to_cloned_candidate_dict(self):
        fields = (
            "label",
            "url",
            "title",
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
            "state",
            "tracker_urls",
            "video_asset_id",
        )
        candidate = {}
        for field in fields:
            candidate[field] = getattr(self, field)
        return candidate

    class QuerySet(models.QuerySet):
        def filter_by_user(self, user):
            if user.has_perm("zemauth.can_see_all_accounts"):
                return self
            return self.filter(
                models.Q(ad_group__campaign__account__users__id=user.id)
                | models.Q(ad_group__campaign__account__agency__users__id=user.id)
            ).distinct()

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            content_ad_ids = (
                core.entity.ContentAdSource.objects.filter(source__in=sources)
                .select_related("content_ad")
                .distinct("content_ad_id")
                .values_list("content_ad_id", flat=True)
            )

            return self.filter(id__in=content_ad_ids)

        def exclude_archived(self, show_archived=False):
            if show_archived:
                return self

            return self.filter(archived=False)

    objects = ContentAdManager.from_queryset(QuerySet)()
