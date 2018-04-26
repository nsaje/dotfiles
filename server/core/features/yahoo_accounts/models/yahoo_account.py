from django.db import models


class YahooAccount(models.Model):
    class Meta:
        app_label = 'dash'

    advertiser_id = models.CharField(blank=False, null=False, max_length=255)

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')

    def __str__(self):
        return str(self.advertiser_id)
