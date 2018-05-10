from django.db import models
from timezone_field import TimeZoneField

import dash.constants


class YahooAccount(models.Model):
    class Meta:
        app_label = 'dash'

    advertiser_id = models.CharField(blank=False, null=False, max_length=255, unique=True)
    budgets_tz = TimeZoneField(default='America/Los_Angeles')
    currency = models.CharField(
        max_length=3,
        default=dash.constants.Currency.USD,
        choices=dash.constants.Currency.get_choices(),
    )

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')

    def __str__(self):
        return str(self.advertiser_id)
