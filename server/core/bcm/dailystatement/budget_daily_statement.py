from django.db import models

from . import queryset


class BudgetDailyStatement(models.Model):
    budget = models.ForeignKey('BudgetLineItem', related_name='statements')
    date = models.DateField()
    media_spend_nano = models.BigIntegerField()
    data_spend_nano = models.BigIntegerField()
    license_fee_nano = models.BigIntegerField()
    margin_nano = models.BigIntegerField()

    objects = queryset.BudgetDailyStatementQuerySet.as_manager()

    @property
    def total_spend_nano(self):
        return self.media_spend_nano + self.data_spend_nano + self.license_fee_nano

    class Meta:
        get_latest_by = 'date'
        unique_together = ('budget', 'date')
        app_label = 'dash'
