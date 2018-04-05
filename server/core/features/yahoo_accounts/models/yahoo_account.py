from django.db import models

import core.entity


class YahooAccount(models.Model):
    class Meta:
        app_label = 'dash'

    advertiser_id = models.CharField(blank=False, null=False, max_length=255)
    account = models.OneToOneField(core.entity.Account)

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
