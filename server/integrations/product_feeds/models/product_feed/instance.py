import datetime
import hashlib
import html
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.utils.html import strip_tags

import core.models
import dash.constants
from core.common.entity_limits import EntityLimitExceeded
from dash.features import contentupload
from integrations.product_feeds import constants
from integrations.product_feeds import exceptions
from integrations.product_feeds import models
from utils import dates_helper
from utils import slack


class ProductFeedInstanceMixin:
    def __str__(self):
        return self.name

    def pause_and_archive_ads(self, dry_run=False):
        if self.content_ads_ttl <= 0:
            return
        ads_to_pause_and_archive = (
            core.models.ContentAd.objects.filter_active()
            .filter(
                ad_group__in=self.ad_groups.exclude_archived(),
                created_dt__lte=dates_helper.local_today() - datetime.timedelta(self.content_ads_ttl),
            )
            .exclude_archived()
        )
        if not dry_run:
            for ad in ads_to_pause_and_archive:
                ad.update(None, state=dash.constants.ContentAdSourceState.INACTIVE, archived=True)
        self._write_log(
            dry_run=dry_run, ads_paused_and_archived=list(ads_to_pause_and_archive), exception="Pause and archive Ads."
        )

    def ingest_and_create_ads(self, dry_run=False):
        try:
            all_items = self._get_all_feed_items()
            batch_name = "{}_{}".format(self.name, dates_helper.local_now().strftime("%Y-%m-%d-%H%M"))
            all_parsed_items = []
            skipped_items = []
            batches = []
            items_to_upload = []

            for item in all_items:
                if item.is_empty_element:
                    continue
                parsed_item = self._get_parsed_item(item)
                if self.truncate_title:
                    parsed_item["title"] = self._truncate(parsed_item["title"], constants.MAX_TITLE_LENGTH)
                if self.truncate_description:
                    parsed_item["description"] = self._truncate(
                        parsed_item["description"], constants.MAX_DESCRIPTION_LENGTH
                    )
                try:
                    self._validate_item(parsed_item)
                    parsed_item["label"] = self._hash_label(
                        parsed_item["title"], parsed_item["url"], parsed_item["image_url"]
                    )
                    all_parsed_items.append(parsed_item)
                except exceptions.ValidationError as e:
                    skipped_items.append({"item": "{}".format(item), "reason": "{}".format(e)})
                    continue

            ad_groups = self.ad_groups.filter_active().exclude_archived()
            for ad_group in ad_groups:
                for item in all_parsed_items:
                    if ad_group.custom_flags and ad_group.custom_flags.get(constants.CUSTOM_FLAG_BRAND):
                        if not self._map_ads_to_ad_group_brand(ad_group, item["brand_name"]):
                            continue
                        item["brand_name"] = item["dealer_name"]
                    if self._is_ad_already_uploaded(item, ad_group):
                        skipped_items.append(
                            {
                                "item": "{}".format(item),
                                "ad_group": "{}".format(ad_group),
                                "reason": "Item already uploaded.",
                            }
                        )
                        continue
                    items_to_upload.append(item)
                    if not dry_run:
                        batch, candidates = contentupload.upload.insert_candidates(
                            None,
                            ad_group.campaign.account,
                            [item],
                            ad_group,
                            batch_name,
                            filename="no-verify",
                            auto_save=True,
                        )
                        batches.append(batch)
            self._write_log(
                dry_run=dry_run,
                batches=batches,
                ads_skipped=skipped_items[:100],
                exception="No active ad_groups" if not ad_groups else "",
                items_to_upload="{}".format("".join([str(i) for i in items_to_upload[:100]])),
            )
        except (Exception, EntityLimitExceeded) as e:
            self._write_log(dry_run=dry_run, exception="{}".format(e))
            slack.publish(
                "Something append with feed '{}', exception: {}".format(self.name, e),
                msg_type=slack.MESSAGE_TYPE_WARNING,
                username="Product Feeds",
            )
            raise e

    def _get_feed_data(self):
        response = requests.get(self.feed_url)
        if not response.ok:
            raise exceptions.FeedConnectionError("Unable to get the feed. Error: {}".format(response.reason))
        return response.text

    def _get_all_feed_items(self):
        feed_data = self._get_feed_data()
        product_feed = BeautifulSoup(feed_data, features="xml")
        els_name = constants.FEEDS_TAG_MAPPING[self.feed_type]["elements_name"]
        all_items = product_feed.find_all(els_name)
        if not all_items:
            raise exceptions.NofeedItems("Not elements found with element names: '{}'".format(els_name))
        return all_items

    def _get_parsed_item(self, item):
        item_values = dict()
        for k, v in constants.FEEDS_TAG_MAPPING[self.feed_type]["elements_mapping"].items():
            tag = item.find(v)
            if not tag:
                item_values[k] = None
                continue
            if k == "image_url":
                item_values[k] = self._get_image_link(tag)
                continue
            item_values[k] = tag.text

        if "brand_name" not in item_values:
            item_values["brand_name"] = self.default_brand_name
        if "display_url" not in item_values:
            item_values["display_url"] = self.default_display_url
        if "call_to_action" not in item_values:
            item_values["call_to_action"] = self.default_call_to_action
        return self._clean_strings(**item_values)

    def _validate_item(self, parsed_item):
        if set(constants.FEEDS_TAG_MAPPING[self.feed_type]["elements_mapping"].keys()).difference(parsed_item.keys()):
            raise exceptions.ValidationError("Item has missing key(s)")
        if not all(parsed_item.values()):
            raise exceptions.ValidationError("Item has empty values.")
        if self._contains_blacklisted_words(parsed_item["title"]):
            raise exceptions.ValidationError("Title contains blacklisted keywords.")
        if self._contains_blacklisted_words(parsed_item["description"]):
            raise exceptions.ValidationError("Description contains blacklisted keywords.")
        if len(parsed_item["title"]) > constants.MAX_TITLE_LENGTH and not self.truncate_title:
            raise exceptions.ValidationError("Title too long.")
        if len(parsed_item["description"]) > constants.MAX_DESCRIPTION_LENGTH and not self.truncate_description:
            raise exceptions.ValidationError("Description is too long.")
        if len(parsed_item["display_url"]) > constants.MAX_DISPLAY_URL_LENGTH:
            raise exceptions.ValidationError("Display url is too long.")
        if len(parsed_item["brand_name"]) > constants.MAX_BRAND_NAME_LENGTH:
            raise exceptions.ValidationError("Brand name is too long.")
        return True

    def _is_ad_already_uploaded(self, item, ad_group):
        return ad_group.contentad_set.filter(label=item["label"]).exclude_archived().exists()

    def _write_log(self, **kwargs):
        product_feed = self
        models.SyncAttempt.objects.create(product_feed, **kwargs)

    def _contains_blacklisted_words(self, string):
        splitted_string = re.sub(r"[^\w]", " ", string.casefold()).split()
        if len(set(splitted_string).intersection((bw.casefold() for bw in self.blacklisted_keywords))):
            return True
        return False

    def _clean_strings(self, **kwargs):
        cleaned_strings = dict()
        for k, v in kwargs.items():
            if k == "display_url" and v != self.default_display_url:
                cleaned_strings[k] = urlparse(v).netloc
                continue
            cleaned_strings[k] = html.unescape(re.compile(r"\s").sub(" ", strip_tags(v).strip())) if v else None
        return cleaned_strings

    @staticmethod
    def _get_image_link(tag):
        if tag.name == "content":
            url = tag.get("url", "")
            if "-/" in url:
                # Yahoo new : The url is a link to an image resizer service and the image link is provided after
                # the -/ delimiter. Their resized image is too small so we must use the original one.
                return url.rpartition("-/")[2]
        elif tag.name == "encoded":
            tag_content_as_html = BeautifulSoup(tag.next, features="lxml")
            if tag_content_as_html.find("img"):
                return tag_content_as_html.find("img").get("src", "")
            return ""
        else:
            return tag.text

    @staticmethod
    def _truncate(string, max_length):
        if len(string) <= max_length:
            return string
        new_string = ""
        split_by_words = string.split(" ")
        for word in split_by_words:
            if word != split_by_words[-1]:
                preview = new_string + word + "..."
                if len(preview) <= max_length:
                    new_string = "{} {}".format(new_string, word)
                else:
                    new_string = "{}...".format(new_string.strip())
                    break
        return new_string

    @staticmethod
    def _hash_label(title, url, image_url):
        to_hash = "{}{}{}".format(title, url, image_url)
        return hashlib.md5(to_hash.encode("utf-8")).hexdigest()

    @staticmethod
    def _map_ads_to_ad_group_brand(ad_group, brand_name):
        return bool(re.match(ad_group.custom_flags.get(constants.CUSTOM_FLAG_BRAND, ""), brand_name, re.IGNORECASE))
