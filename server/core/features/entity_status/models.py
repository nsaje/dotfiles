import decimal

from django.db import models

from dash import constants


class AccountStatusCache(models.Model):
    class Meta:
        app_label = "dash"

    account_id = models.IntegerField(primary_key=True)
    status = models.IntegerField(
        default=constants.AdGroupRunningStatus.INACTIVE, choices=constants.AdGroupSettingsState.get_choices()
    )
    local_daily_budget = models.DecimalField(max_digits=10, decimal_places=4, default=decimal.Decimal(0))
