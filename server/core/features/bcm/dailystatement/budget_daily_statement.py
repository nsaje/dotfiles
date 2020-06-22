from django.db import models

import core.common
import core.features.multicurrency

from . import queryset


class BudgetDailyStatementManager(core.common.BaseManager):
    def create(
        self,
        *,
        date,
        budget,
        base_media_spend_nano,
        base_data_spend_nano,
        media_spend_nano,
        data_spend_nano,
        service_fee_nano,
        license_fee_nano,
        margin_nano,
        **kwargs,
    ):
        assert not any(arg_name.startswith("local_") for arg_name in kwargs.keys()), "Provide values in USD"

        currency_exchange_rate = core.features.multicurrency.get_exchange_rate(date, budget.credit.currency)

        local_base_media_spend_nano = base_media_spend_nano * currency_exchange_rate
        local_base_data_spend_nano = base_data_spend_nano * currency_exchange_rate
        local_media_spend_nano = media_spend_nano * currency_exchange_rate
        local_data_spend_nano = data_spend_nano * currency_exchange_rate

        local_service_fee_nano = service_fee_nano * currency_exchange_rate
        local_license_fee_nano = license_fee_nano * currency_exchange_rate
        local_margin_nano = margin_nano * currency_exchange_rate

        return super().create(
            budget=budget,
            date=date,
            base_media_spend_nano=base_media_spend_nano,
            base_data_spend_nano=base_data_spend_nano,
            media_spend_nano=media_spend_nano,
            data_spend_nano=data_spend_nano,
            service_fee_nano=service_fee_nano,
            license_fee_nano=license_fee_nano,
            margin_nano=margin_nano,
            local_base_media_spend_nano=local_base_media_spend_nano,
            local_base_data_spend_nano=local_base_data_spend_nano,
            local_media_spend_nano=local_media_spend_nano,
            local_data_spend_nano=local_data_spend_nano,
            local_service_fee_nano=local_service_fee_nano,
            local_license_fee_nano=local_license_fee_nano,
            local_margin_nano=local_margin_nano,
            **kwargs,
        )


class BudgetDailyStatement(models.Model):
    budget = models.ForeignKey("BudgetLineItem", related_name="statements", on_delete=models.CASCADE)
    date = models.DateField()

    base_media_spend_nano = models.BigIntegerField(null=True)
    base_data_spend_nano = models.BigIntegerField(null=True)
    media_spend_nano = models.BigIntegerField()
    data_spend_nano = models.BigIntegerField()
    service_fee_nano = models.BigIntegerField(default=0)
    license_fee_nano = models.BigIntegerField()
    margin_nano = models.BigIntegerField()

    local_base_media_spend_nano = models.BigIntegerField(null=True)
    local_base_data_spend_nano = models.BigIntegerField(null=True)
    local_media_spend_nano = models.BigIntegerField()
    local_data_spend_nano = models.BigIntegerField()

    local_service_fee_nano = models.BigIntegerField(default=0)
    local_license_fee_nano = models.BigIntegerField()
    local_margin_nano = models.BigIntegerField()

    objects = BudgetDailyStatementManager.from_queryset(queryset.BudgetDailyStatementQuerySet)()

    def update_amounts(
        self,
        base_media_spend_nano,
        base_data_spend_nano,
        media_spend_nano,
        data_spend_nano,
        service_fee_nano,
        license_fee_nano,
        margin_nano,
    ):
        currency_exchange_rate = core.features.multicurrency.get_exchange_rate(self.date, self.budget.credit.currency)

        self.base_media_spend_nano = base_media_spend_nano
        self.base_data_spend_nano = base_data_spend_nano
        self.media_spend_nano = media_spend_nano
        self.data_spend_nano = data_spend_nano

        self.service_fee_nano = service_fee_nano
        self.license_fee_nano = license_fee_nano
        self.margin_nano = margin_nano

        self.local_base_media_spend_nano = base_media_spend_nano * currency_exchange_rate
        self.local_base_data_spend_nano = base_data_spend_nano * currency_exchange_rate
        self.local_media_spend_nano = media_spend_nano * currency_exchange_rate
        self.local_data_spend_nano = data_spend_nano * currency_exchange_rate

        self.local_service_fee_nano = service_fee_nano * currency_exchange_rate
        self.local_license_fee_nano = license_fee_nano * currency_exchange_rate
        self.local_margin_nano = margin_nano * currency_exchange_rate

        self.save()

    class Meta:
        get_latest_by = "date"
        unique_together = ("budget", "date")
        app_label = "dash"
