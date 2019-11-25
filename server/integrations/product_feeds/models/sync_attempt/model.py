import jsonfield
from django.db import models

from utils.json_helper import JSONFIELD_DUMP_KWARGS

from . import manager


class SyncAttempt(models.Model):
    product_feed = models.ForeignKey("ProductFeed", related_name="sync_attempts", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    batches = models.ManyToManyField("dash.UploadBatch")
    ads_skipped = jsonfield.JSONField(null=True, blank=True, default=dict)
    exception = models.CharField(blank=True, default="", max_length=255)
    dry_run = models.BooleanField(null=False, default=False)
    items_to_upload = jsonfield.JSONField(blank=True, null=True, default=dict, dump_kwargs=JSONFIELD_DUMP_KWARGS)
    ads_paused_and_archived = models.ManyToManyField("dash.ContentAd")

    def __str__(self):
        return "{} ({})".format(self.product_feed.name, self.timestamp)

    objects = manager.SyncAttemptManager()
