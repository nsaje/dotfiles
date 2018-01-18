# -*- coding: utf-8 -*-

from django.db import models

from dash import constants


class CurrencyExchangeRate(models.Model):
    class Meta:
        app_label = 'dash'

    date = models.DateField()
    currency = models.CharField(
        max_length=3,
        choices=constants.Currency.get_choices()
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4
    )
    is_reference = models.BooleanField(default=False)
