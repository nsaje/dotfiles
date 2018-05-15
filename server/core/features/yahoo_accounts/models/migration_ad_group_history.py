import jsonfield

from django.db import models


class YahooMigrationAdGroupHistory(models.Model):
    class Meta:
        app_label = 'dash'

    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})
