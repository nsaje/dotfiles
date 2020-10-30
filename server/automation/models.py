from django.conf import settings
from django.db import models

import core.models.ad_group
import core.models.campaign
import dash.constants

from .campaignstop.campaignstop_state import *  # noqa
from .campaignstop.real_time_campaign_stop_log import *  # noqa
from .campaignstop.real_time_data_history import *  # noqa
from .rules.models import *  # noqa


class CampaignBudgetDepletionNotification(models.Model):
    account_manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name="+", on_delete=models.PROTECT)
    campaign = models.ForeignKey(core.models.campaign.Campaign, related_name="+", on_delete=models.PROTECT)
    created_dt = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="Created at", db_index=True
    )
    available_budget = models.DecimalField(
        max_digits=20, decimal_places=4, blank=True, null=True, default=0, verbose_name="Budget available at creation"
    )
    yesterdays_spend = models.DecimalField(
        max_digits=20, decimal_places=4, blank=True, null=True, default=0, verbose_name="Campaign's yesterday's spend"
    )
    stopped = models.BooleanField(default=False)

    def __str__(self):
        return "{0} {1}".format(self.account_manager_id, self.campaign_id)


class AutopilotLog(models.Model):
    campaign = models.ForeignKey(core.models.campaign.Campaign, related_name="+", on_delete=models.PROTECT, null=True)
    ad_group = models.ForeignKey(core.models.ad_group.AdGroup, related_name="+", on_delete=models.PROTECT)
    campaign_goal = models.IntegerField(
        default=None, blank=True, null=True, choices=dash.constants.CampaignGoalKPI.get_choices()
    )
    campaign_goal_optimal_value = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Goal's optimal value"
    )
    goal_value = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Goal's value"
    )
    created_dt = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="Created at", db_index=True
    )
    yesterdays_spend_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, default=0, verbose_name="Yesterday's spend"
    )
    previous_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Previous daily spend cap"
    )
    new_daily_budget = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="New daily spend cap"
    )
    budget_comments = models.CharField(max_length=1024, null=True, blank=True)
    is_autopilot_job_run = models.NullBooleanField(default=False, null=True, blank=True)

    # TODO: RTAP: remove after real-time autopilot migration complete
    ad_group_source = models.ForeignKey(
        core.models.ad_group_source.AdGroupSource, related_name="+", on_delete=models.PROTECT, null=True
    )
    autopilot_type = models.IntegerField(
        default=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
        choices=dash.constants.AdGroupSettingsAutopilotState.get_choices(),
    )
    yesterdays_clicks = models.IntegerField(null=True)
    previous_cpc_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Previous CPC"
    )
    new_cpc_cc = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="New CPC")
    cpc_comments = models.CharField(max_length=1024, null=True, blank=True)
    is_rtb_as_one = models.NullBooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return "{0} {1}".format(self.ad_group, self.ad_group_source)


class CampaignStopLog(models.Model):
    campaign = models.ForeignKey(core.models.campaign.Campaign, on_delete=models.PROTECT)
    notes = models.TextField()
    created_dt = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="Created at", db_index=True
    )
