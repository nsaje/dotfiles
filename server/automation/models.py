from django.db import models
from django.conf import settings
import dash.models


class CampaignBudgetDepletionNotification(models.Model):
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
    yesterdays_spend = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        blank=True,
        null=True,
        default=0,
        verbose_name='Campaign\'s yesterday\'s spend'
    )

    def __unicode__(self):
        return '{0} {1}'.format(self.account_manager_id, self.campaign_id)


class AutopilotAdGroupSourceBidCpcLog(models.Model):
    campaign = models.ForeignKey(
        dash.models.Campaign,
        related_name='+',
        on_delete=models.PROTECT
    )
    ad_group = models.ForeignKey(
        dash.models.AdGroup,
        related_name='+',
        on_delete=models.PROTECT
    )
    ad_group_source = models.ForeignKey(
        dash.models.AdGroupSource,
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
    yesterdays_clicks = models.IntegerField(null=True)
    yesterdays_spend_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        default=0,
        verbose_name='Yesterday\'s spend'
    )
    previous_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Previous CPC'
    )
    new_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='New CPC'
    )
    current_daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Daily budget'
    )
    comments = models.CharField(max_length=1024, null=True, blank=True)

    def __unicode__(self):
        return '{0} {1}'.format(
            self.campaign,
            self.ad_group,
            self.ad_group_source)
