from django.contrib.postgres.fields import ArrayField
from django.db import models

from integrations.product_feeds import constants

from .instance import ProductFeedInstanceMixin


class ProductFeed(ProductFeedInstanceMixin, models.Model):
    _update_fields = (
        "name",
        "feed_url",
        "status",
        "feed_type",
        "truncate_description",
        "truncate_title",
        "default_brand_name",
        "default_display_url",
        "default_brand_name",
        "default_display_url",
        "default_call_to_action",
        "content_ads_ttl",
        "blacklisted_keywords",
        "ad_groups",
        "max_daily_uploads",
    )

    name = models.CharField(max_length=255, blank=False, null=False)
    feed_url = models.CharField(max_length=255, blank=False, null=False)
    status = models.IntegerField(default=constants.FeedStatus.ENABLED, choices=constants.FeedStatus.get_choices())
    feed_type = models.IntegerField(choices=constants.FeedTypes.get_choices(), null=False)
    truncate_description = models.BooleanField(
        default=False,
        null=False,
        help_text="If True, it will be truncated by words and 3 dots appended. Otherwise ad will be ignored.",
    )
    truncate_title = models.BooleanField(
        default=False,
        null=False,
        help_text="If True, it will be truncated by words and 3 dots will be appended. Otherwise ad will be ignored.",
    )
    default_brand_name = models.CharField(
        max_length=25, blank=False, null=False, help_text="Default to use when brand is not specified in the feed"
    )
    default_display_url = models.CharField(
        max_length=35, blank=False, null=False, help_text="Default to use when display url is not specified in the feed"
    )
    default_call_to_action = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text="Default to use when brand is not specified in the feed",
        default="Read more",
    )
    content_ads_ttl = models.IntegerField(
        default=0,
        null=False,
        blank=False,
        help_text="Time to live of the ad before being paused and archived. If 0, it will never expire.",
    )
    blacklisted_keywords = ArrayField(models.CharField(max_length=255), blank=True, null=True, default=list)
    ad_groups = models.ManyToManyField("dash.AdGroup", blank=False)
    max_daily_uploads = models.IntegerField(
        blank=True, default=0, help_text="Maximum of number of ads that will be uploaded every day."
    )
