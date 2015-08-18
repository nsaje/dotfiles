from django.db import models
from django.conf import settings
import dash.models

class CampaignBudgetDepletionSettings(models.Model):
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name="+",
        on_delete=models.PROTECT
    )
    campaign = models.ForeignKey(
        dash.models.Campaign,
        related_name='+',
        on_delete=models.PROTECT
    )
    created_dt = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Created at',
        db_index=True
    )
    available_budget = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        blank=True,
        null=True,
        default=0,
        verbose_name='Budget available at creation'
    )
    yesterdays_spendt = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        blank=True,
        null=True,
        default=0,
        verbose_name='Campaign\'s yesterday\'s spend'
    )

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')
