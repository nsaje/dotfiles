import json

from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.forms import Textarea
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.html import XmlLexer

from . import constants
from .models import ProductFeed
from .models import SyncAttempt


class SyncAttemptAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def ads_skipped_prettified(self, instance):
        response = json.dumps(instance.ads_skipped, indent=1)
        formatter = HtmlFormatter(style="colorful")
        response = highlight(response, XmlLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"
        return mark_safe(style + response)

    def items_to_upload_prettified(self, instance):
        response = json.dumps(instance.items_to_upload, indent=1)
        formatter = HtmlFormatter(style="colorful")
        response = highlight(response, XmlLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"
        return mark_safe(style + response)

    ads_skipped_prettified.short_description = "items_skipped"
    items_to_upload_prettified.short_description = "items_uploaded"

    fields = (
        "timestamp",
        "product_feed",
        "batches",
        "ads_skipped_prettified",
        "exception",
        "dry_run",
        "items_to_upload_prettified",
    )
    readonly_fields = (
        "product_feed",
        "timestamp",
        "batches",
        "ads_skipped_prettified",
        "exception",
        "dry_run",
        "items_to_upload_prettified",
    )
    ordering = ("-timestamp", "product_feed")
    search_fields = ("batches__adgroup", "product_feed")
    list_filter = ("product_feed", "timestamp", "dry_run")
    list_display = ("product_feed", "timestamp", "dry_run")


class ProductFeedAdmin(admin.ModelAdmin):
    list_filter = ("name", "feed_url", "status")
    list_display = ("name", "feed_url", "feed_type", "status", "content_ads_ttl")
    formfield_overrides = {ArrayField: {"widget": Textarea(attrs={"rows": 20, "cols": 45})}}
    raw_id_fields = ("ad_groups",)

    def ingest_and_create_ads_dry_run(self, request, queryset):
        for product_feed in queryset:
            product_feed.ingest_and_create_ads(dry_run=True)

    def pause_and_archive_dry_run(self, request, queryset):
        for product_feed in queryset:
            product_feed.pause_and_archive_ads(dry_run=True)

    def ingest_and_create_ads(self, request, queryset):
        for product_feed in queryset.filter(status=constants.FeedStatus.ENABLED):
            product_feed.ingest_and_create_ads(dry_run=False)

    def pause_and_archive_ads(self, request, queryset):
        for product_feed in queryset.filter(status=constants.FeedStatus.ENABLED):
            product_feed.ingest_and_create_ads(dry_run=False)

    actions = [ingest_and_create_ads_dry_run, pause_and_archive_dry_run, ingest_and_create_ads, pause_and_archive_ads]


admin.site.register(SyncAttempt, SyncAttemptAdmin)
admin.site.register(ProductFeed, ProductFeedAdmin)
