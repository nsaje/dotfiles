import datetime
import hashlib
import re
from urllib.parse import urlparse

import requests
from django.utils.html import strip_tags

import core.models
import dash.constants
from bs4 import BeautifulSoup
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
        if self.content_ads_ttl > 0:
            ads_to_pause_and_archive = (
                core.models.ContentAd.objects.filter_active()
                .filter(
                    ad_group__in=self.ad_groups.exclude_archived(),
                    created_dt__lte=dates_helper.local_today() - datetime.timedelta(self.content_ads_ttl),
                )
                .exclude_archived()
                .exclude(label__exact="")
            )
            if not dry_run:
                for ad in ads_to_pause_and_archive:
                    ad.update(None, state=dash.constants.ContentAdSourceState.INACTIVE, archived=True)
            self._write_log(dry_run=dry_run, ads_paused_and_archived=list(ads_to_pause_and_archive))

    def ingest_and_create_ads(self, dry_run=False):
        try:
            all_items = self._get_all_feed_items()
            batch_name = "{}_{}".format(self.name, dates_helper.local_now().strftime("%Y-%m-%d-%H%M"))
            all_parsed_items = []
            skipped_items = []

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
                    skipped_items.append({"item": item, "reason": e})
                    continue

            for ad_group in self.ad_groups.filter_active().exclude_archived():
                items_to_upload = []
                for item in all_parsed_items:
                    if self._is_ad_already_uploaded(item, ad_group):
                        skipped_items.append({"item": item, "ad_group": ad_group, "reason": "Item already uploaded."})
                        continue
                    items_to_upload.append(item)
                if dry_run:
                    # We just log the 10 firsts, otherwise it might be too big.
                    self._write_log(
                        dry_run=dry_run, items_to_upload=items_to_upload[10:], ads_skipped=items_to_upload[10:]
                    )
                    continue
                batch, candidates = contentupload.upload.insert_candidates(
                    None,
                    ad_group.campaign.account,
                    items_to_upload,
                    ad_group,
                    batch_name,
                    filename="no-verify",
                    auto_save=True,
                )
                self._write_log(dry_run=dry_run, batches=batch, ads_skipped=skipped_items)

        except Exception as e:
            self._write_log(dry_run=dry_run, exception=e)
            slack.publish(
                "Something append with feed '{}', exception: {}".format(self.name, e),
                msg_type=slack.MESSAGE_TYPE_WARNING,
                username="Product Feeds",
            )

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
            raise exceptions.ValidationError("Description too long.")
        return True

    def _is_ad_already_uploaded(self, item, ad_group):
        label = self._hash_label(item["title"], item["url"], item["image_url"])
        return ad_group.contentad_set.filter(label=label).exclude_archived().exists()

    def _write_log(self, **kwargs):
        models.SyncAttempt.objects.create(self, **kwargs)

    def _contains_blacklisted_words(self, string):
        splitted_string = re.sub(r"[^\w]", " ", string.casefold()).split()
        if len(set(splitted_string).intersection((bw.casefold() for bw in self.blacklisted_keywords))):
            return True
        return False

    @staticmethod
    def _clean_strings(**kwargs):
        cleaned_strings = dict()
        for k, v in kwargs.items():
            if k == "display_url" and v:
                cleaned_strings[k] = urlparse(v).netloc
            cleaned_strings[k] = re.compile(r"\s").sub(" ", strip_tags(v).strip()) if v else None
        return cleaned_strings

    @staticmethod
    def _get_image_link(tag):
        if tag.name == "content":
            url = tag.get("url", "")
            if "-/" in url:
                # The url is a link to an image resizer service and the image link is provided after the -/ delimiter.
                # Their resized image is too small so we must use the original one.
                return url.rpartition("-/")[2]
        elif tag.name == "encoded":
            return tag.find("img").get("src", "")
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