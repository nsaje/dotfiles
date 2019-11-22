import json

from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.forms import Textarea
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.html import XmlLexer

import dash.constants
from dash.features.contentupload import upload

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
        style = "<style>{}</style><br>".format(formatter.get_style_defs())
        return mark_safe(style + response)

    def items_to_upload_prettified(self, instance):
        response = json.dumps(instance.items_to_upload, indent=1)
        formatter = HtmlFormatter(style="colorful")
        response = highlight(response, XmlLexer(), formatter)
        style = "<style>{} <br></style>".format(formatter.get_style_defs())
        return mark_safe(style + response)

    def content_ads_candidates_errors(self, instance):
        errors = dict()
        if instance.batches.all():
            for batch in instance.batches.all():
                if batch.status == dash.constants.UploadBatchStatus.FAILED:
                    _, errs = upload.get_clean_candidates_and_errors(batch.contentadcandidate_set.all())
                    errors.update(errs)

        return "\n".join([str(err) for err in errors.items()])

    def global_upload_status(self, instance):
        successes = []
        if instance.batches.all():
            for batch in instance.batches.all():
                if batch.status == dash.constants.UploadBatchStatus.FAILED:
                    successes.append(False)
        return all(successes)

    def ad_groups_links(self, instance):
        links = []
        for ad_group in instance.product_feed.ad_groups.all():
            links.append(
                "<a href=https://one.zemanta.com/v2/analytics/adgroup/{}>{} ({}) </a>".format(
                    ad_group.id, ad_group.name, ad_group.settings.state
                )
            )
        return format_html(", ".join(links))

    content_ads_candidates_errors.short_description = "Content ads candidates errors"
    ads_skipped_prettified.short_description = "Feed items not uploaded (skipped because of validation)"
    items_to_upload_prettified.short_description = "items uploaded"
    global_upload_status.short_description = "global upload success"
    global_upload_status.boolean = True

    fields = (
        "timestamp",
        "product_feed",
        "batches",
        "ad_groups_links",
        "global_upload_status",
        "dry_run",
        "exception",
        "ads_skipped_prettified",
        "items_to_upload_prettified",
        "content_ads_candidates_errors",
        "ads_paused_and_archived",
    )
    readonly_fields = (
        "product_feed",
        "timestamp",
        "batches",
        "ad_groups_links",
        "global_upload_status",
        "dry_run",
        "exception",
        "ads_skipped_prettified",
        "items_to_upload_prettified",
        "content_ads_candidates_errors",
        "ads_paused_and_archived",
    )
    ordering = ("-timestamp", "product_feed")
    search_fields = ("batches__adgroup", "product_feed")
    list_filter = ("product_feed", "timestamp", "dry_run")
    list_display = ("timestamp", "dry_run", "global_upload_status", "product_feed", "exception")


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
