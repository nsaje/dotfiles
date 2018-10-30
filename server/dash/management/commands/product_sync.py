# -*- coding: utf-8 -*-
import collections
import re
import time
import urllib.parse

import feedparser

from core import models
from core import pixels
from core.features import audiences
from dash import constants
from dash import forms
from dash.features import contentupload
from utils import dates_helper
from utils.command_helpers import ExceptionCommand

configuration = [
    #  {
    #      'campaign_id': 20472,
    #      'feed_url': 'facebook.rss',
    #      'pixel_id': 1414,
    #  },
]

Request = collections.namedtuple("Request", ["user"])

SHOPIFY_RE = re.compile(r"/products/[^?]+")


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        self.user = None
        self.request = Request(self.user)
        for config in configuration:
            self._sync_campaign(config)

    def _sync_campaign(self, config):
        campaign = models.Campaign.objects.get(pk=config["campaign_id"])
        pixel = pixels.ConversionPixel.objects.get(account_id=campaign.account_id, pk=config["pixel_id"])

        product_data = self._parse_feed(config["feed_url"])
        print(("Syncing %d proudcts to campaign %d" % (len(product_data), campaign.id)))

        existing_ad_groups = self._get_ad_groups(campaign)
        existing_audiences = self._get_audiences(campaign)
        existing_ads = self._get_ads(campaign)

        for product in product_data:
            print(("Processing product %s" % product["id"]))
            audience = existing_audiences.get(product["id"])
            if audience is None:
                audience = self._create_audience(campaign, pixel, product)

            ad_group = existing_ad_groups.pop(product["id"], None)
            if ad_group is None:
                ad_group = self._create_ad_group(campaign, product["id"])

            self._set_ad_group_settings(ad_group, audience)
            self._pause_sources_without_retargeting(ad_group)

            content_ad = existing_ads.get(ad_group.id)
            if content_ad is None:
                content_ad = self._create_content_ad(ad_group, product)

    def _parse_feed(self, url):
        data = feedparser.parse(url)

        entries = [
            {
                "id": entry["g_id"],
                "url": entry["g_link"],
                "title": entry["g_title"],
                "image_url": entry["g_image_link"],
                "brand": entry["g_brand"],
                "description": entry["g_description"],
            }
            for entry in data["entries"]
        ]

        return entries

    def _get_ads(self, campaign):
        content_ads = models.ContentAd.objects.filter(ad_group__campaign=campaign).exclude_archived()
        return {content_ad.ad_group_id: content_ad for content_ad in content_ads}

    def _create_content_ad(self, ad_group, product):
        print("Creating content ad")
        description_max_length = forms.ContentAdForm({}).fields["description"].max_length
        candidate = {
            "label": product["id"],
            "url": product["url"],
            "title": product["title"],
            "image_url": product["image_url"],
            "image_crop": "center",
            "display_url": self._domain_name(product["url"]),
            "brand_name": product["brand"],
            "description": self._length_limit(product["description"], description_max_length),
            "call_to_action": "Buy Now",
        }
        self._upload_candidates(ad_group, [candidate])

    def _get_ad_groups(self, campaign):
        ad_groups = (
            models.AdGroup.objects.filter(campaign=campaign).select_related("campaign__account").exclude_archived()
        )
        return {ad_group.name: ad_group for ad_group in ad_groups}

    def _create_ad_group(self, campaign, name):
        print("Creating ad group")
        return models.AdGroup.objects.create(self.request, campaign, name=name)

    def _set_ad_group_settings(self, ad_group, audience):
        audience_targeting = [audience.id]
        if ad_group.settings.audience_targeting != audience_targeting:
            print("Setting audience targeting")
            ad_group.settings.update(self.request, audience_targeting=audience_targeting)

    def _pause_sources_without_retargeting(self, ad_group):
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group).select_related("source")
        for ad_group_source in ad_group_sources:
            if (
                ad_group_source.source.can_modify_retargeting_automatically()
                or ad_group_source.source.can_modify_retargeting_manually()
            ):
                continue

            if ad_group_source.get_current_settings().state != constants.AdGroupSourceSettingsState.INACTIVE:
                ad_group_source.settings.update(self.request, state=constants.AdGroupSourceSettingsState.INACTIVE)

    def _get_audiences(self, campaign):
        existing_audiences = audiences.Audience.objects.filter(pixel__account_id=campaign.account_id).filter(
            archived=False
        )
        return {audience.name: audience for audience in existing_audiences}

    def _create_audience(self, campaign, pixel, product):
        print("Creating audience")
        return audiences.Audience.objects.create(
            self.request, product["id"], pixel, ttl=90, prefill_days=90, rules=[self._audience_rule(product)]
        )

    def _audience_rule(self, product):
        return {"type": constants.AudienceRuleType.CONTAINS, "value": SHOPIFY_RE.search(product["url"]).group()}

    def _upload_candidates(self, ad_group, candidates_data):
        batch_name = self._generate_batch_name("Product sync")

        filename = None
        batch, candidates = contentupload.upload.insert_candidates(
            self.user, ad_group.campaign.account, candidates_data, ad_group, batch_name, filename, auto_save=True
        )

        while batch.status == constants.UploadBatchStatus.IN_PROGRESS:
            batch.refresh_from_db()
            print((constants.UploadBatchStatus.get_text(batch.status)))
            time.sleep(1)

        if batch.status == constants.UploadBatchStatus.FAILED:
            cleaned_candidates = contentupload.upload.get_candidates_with_errors(batch.entitycandidate_set.all())
            print([candidate["errors"] for candidate in cleaned_candidates])
            raise Exception("Upload failed")

    @staticmethod
    def _generate_batch_name(prefix):
        return "%s %s" % (prefix, dates_helper.local_now().strftime("%m/%d/%Y %H:%M %z"))

    @staticmethod
    def _domain_name(url):
        return urllib.parse.urlparse(url).hostname

    @staticmethod
    def _length_limit(text, max_length):
        if len(text) > max_length:
            return text[:max_length].rsplit(" ", 1)[0] + "…"
        return text
