from django.db import models

from . import queryset

import core.common
import core.features.multicurrency


class BudgetDailyStatementManager(core.common.BaseManager):
    def create(self, *, date, budget, media_spend_nano, data_spend_nano, license_fee_nano, margin_nano, **kwargs):
        assert not any(arg_name.startswith("local_") for arg_name in kwargs.keys()), "Provide values in USD"

        currency_exchange_rate = core.features.multicurrency.get_exchange_rate(date, budget.credit.currency)

        local_media_spend_nano = media_spend_nano * currency_exchange_rate
        local_data_spend_nano = data_spend_nano * currency_exchange_rate
        local_license_fee_nano = license_fee_nano * currency_exchange_rate
        local_margin_nano = margin_nano * currency_exchange_rate

        return super().create(
            budget=budget,
            date=date,
            media_spend_nano=media_spend_nano,
            data_spend_nano=data_spend_nano,
            license_fee_nano=license_fee_nano,
            margin_nano=margin_nano,
            local_media_spend_nano=local_media_spend_nano,
            local_data_spend_nano=local_data_spend_nano,
            local_license_fee_nano=local_license_fee_nano,
            local_margin_nano=local_margin_nano,
            **kwargs,
        )


class BudgetDailyStatement(models.Model):
    budget = models.ForeignKey("BudgetLineItem", related_name="statements", on_delete=models.CASCADE)
    date = models.DateField()
    media_spend_nano = models.BigIntegerField()
    data_spend_nano = models.BigIntegerField()
    license_fee_nano = models.BigIntegerField()
    margin_nano = models.BigIntegerField()

    local_media_spend_nano = models.BigIntegerField()
    local_data_spend_nano = models.BigIntegerField()
    local_license_fee_nano = models.BigIntegerField()
    local_margin_nano = models.BigIntegerField()

    objects = BudgetDailyStatementManager.from_queryset(queryset.BudgetDailyStatementQuerySet)()

    def update_amounts(self, media_spend_nano, data_spend_nano, license_fee_nano, margin_nano):
        currency_exchange_rate = core.features.multicurrency.get_exchange_rate(self.date, self.budget.credit.currency)

        self.media_spend_nano = media_spend_nano
        self.data_spend_nano = data_spend_nano
        self.license_fee_nano = license_fee_nano
        self.margin_nano = margin_nano

        self.local_media_spend_nano = media_spend_nano * currency_exchange_rate
        self.local_data_spend_nano = data_spend_nano * currency_exchange_rate
        self.local_license_fee_nano = license_fee_nano * currency_exchange_rate
        self.local_margin_nano = margin_nano * currency_exchange_rate

        self.save()

    class Meta:
        get_latest_by = "date"
        unique_together = ("budget", "date")
        app_label = "dash"
