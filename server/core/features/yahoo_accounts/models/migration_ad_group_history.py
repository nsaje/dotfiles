import jsonfield
from django.db import models

from utils.json_helper import JSONFIELD_DUMP_KWARGS


class YahooMigrationAdGroupHistory(models.Model):
    class Meta:
        app_label = "dash"

    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={}, dump_kwargs=JSONFIELD_DUMP_KWARGS)
