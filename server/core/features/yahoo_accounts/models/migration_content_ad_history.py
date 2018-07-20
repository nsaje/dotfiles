from django.db import models


class YahooMigrationContentAdHistory(models.Model):
    class Meta:
        app_label = "dash"

    content_ad = models.ForeignKey("ContentAd", on_delete=models.PROTECT)
    source_content_ad_id = models.CharField(max_length=50, null=True)
