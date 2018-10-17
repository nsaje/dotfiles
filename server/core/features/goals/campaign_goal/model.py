# -*- coding: utf-8 -*-

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import transaction

from dash import constants
import core.common
import core.features.multicurrency
import utils.lc_helper

from ..campaign_goal_value import CampaignGoalValue
from . import bcm_mixin
from . import exceptions


# FIXME: the same dict is in dash/campaign_goals
CAMPAIGN_GOAL_NAME_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE: "{} Time on Site - Seconds",
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: "{} Max Bounce Rate",
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: "{} New Users",
    constants.CampaignGoalKPI.PAGES_PER_SESSION: "{} Pageviews per Visit",
    constants.CampaignGoalKPI.CPA: "{} CPA",
    constants.CampaignGoalKPI.CPC: "{} CPC",
    constants.CampaignGoalKPI.CPV: "{} Cost Per Visit",
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: "{} Cost Per Non-Bounced Visit",
    constants.CampaignGoalKPI.CP_NEW_VISITOR: "{} Cost Per New Visitor",
    constants.CampaignGoalKPI.CP_PAGE_VIEW: "{} Cost Per Pageview",
    constants.CampaignGoalKPI.CPCV: "{} Cost Per Completed Video View",
}


class CampaignGoalManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, campaign, goal_type, value, conversion_goal=None, primary=False):
        core.common.entity_limits.enforce(CampaignGoal.objects.filter(campaign=campaign), campaign.account_id)
        self._validate_goal_count(campaign, goal_type)
        self._validate_cpa_goal(goal_type, conversion_goal)

        if conversion_goal is not None:
            goal_type = constants.CampaignGoalKPI.CPA

        goal = super(CampaignGoalManager, self).create(
            type=goal_type, campaign=campaign, conversion_goal=conversion_goal
        )

        history_value = goal.add_local_value(request, value, skip_history=True)
        currency_symbol = core.features.multicurrency.get_currency_symbol(goal.campaign.account.currency)

        if primary:
            goal.set_primary(request)

        import dash.campaign_goals

        if goal.type in dash.campaign_goals.COST_DEPENDANT_GOALS:
            history_value = utils.lc_helper.format_currency(history_value, places=3, curr=currency_symbol)

        campaign.write_history(
            'Added campaign goal "{}{}"'.format(
                (str(history_value) + " ") if history_value else "", constants.CampaignGoalKPI.get_text(goal.type)
            ),
            action_type=constants.HistoryActionType.GOAL_CHANGE,
            user=request.user,
        )

        return goal

    def _validate_goal_count(self, campaign, goal_type):
        goals = CampaignGoal.objects.filter(campaign=campaign, type=goal_type)
        if goal_type == constants.CampaignGoalKPI.CPA:
            if goals.count() >= constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
                raise exceptions.ConversionGoalLimitExceeded("Max conversion goals per campaign exceeded")
        elif goals.exists():
            raise exceptions.MultipleSameTypeGoals("Multiple goals of the same type not allowed")

    def _validate_cpa_goal(self, goal_type, conversion_goal):
        if goal_type == constants.CampaignGoalKPI.CPA and conversion_goal is None:
            raise exceptions.ConversionGoalRequired("Conversion goal required when creating a CPA goal")


class CampaignGoal(models.Model, bcm_mixin.CampaignGoalBCMMixin):
    class Meta:
        app_label = "dash"
        unique_together = ("campaign", "type", "conversion_goal")

    campaign = models.ForeignKey("Campaign", on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(
        default=constants.CampaignGoalKPI.TIME_ON_SITE, choices=constants.CampaignGoalKPI.get_choices()
    )
    primary = models.BooleanField(default=False)
    conversion_goal = models.ForeignKey("ConversionGoal", null=True, blank=True, on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Created by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    objects = CampaignGoalManager()

    def to_dict(self, with_values=False, local_values=False):
        campaign_goal = {
            "campaign_id": self.campaign_id,
            "type": self.type,
            "primary": self.primary,
            "id": self.pk,
            "conversion_goal": None,
        }

        if self.conversion_goal:
            campaign_goal["conversion_goal"] = {
                "id": self.conversion_goal.pk,
                "type": self.conversion_goal.type,
                "name": self.conversion_goal.name,
                "conversion_window": self.conversion_goal.conversion_window,
                "goal_id": self.conversion_goal.goal_id,
                "pixel_url": None,
            }
            if self.conversion_goal.pixel_id is not None:
                campaign_goal["conversion_goal"]["goal_id"] = self.conversion_goal.pixel_id

        if with_values:
            default_rounding_format = "1.00"
            rounding_format = {constants.CampaignGoalKPI.CPC: "1.000"}

            campaign_goal["values"] = []
            for campaign_goal_value in self.values.all():
                if local_values:
                    value = campaign_goal_value.local_value
                else:
                    value = campaign_goal_value.value

                campaign_goal["values"].append(
                    {
                        "datetime": str(campaign_goal_value.created_dt),
                        "value": Decimal(value).quantize(
                            Decimal(rounding_format.get(self.type, default_rounding_format))
                        ),
                    }
                )

        return campaign_goal

    @transaction.atomic
    def update(self, request, **updates):
        value = updates.get("value")
        if value:
            self.add_local_value(request, value)
        primary = updates.get("primary")
        if primary:
            self.set_primary(request)

    def get_view_key(self):
        return "campaign_goal_" + str(self.id)

    def add_value(self, request, value, skip_history=False):
        value = Decimal(value)
        local_value = value

        import dash.campaign_goals

        if self.type in dash.campaign_goals.COST_DEPENDANT_GOALS:
            local_value = value * self._get_exchange_rate()

        self._add_value(request, value, local_value, skip_history)
        return value

    def add_local_value(self, request, local_value, skip_history=False):
        local_value = Decimal(local_value)
        value = local_value

        import dash.campaign_goals

        if self.type in dash.campaign_goals.COST_DEPENDANT_GOALS:
            value = local_value / self._get_exchange_rate()

        self._add_value(request, value, local_value, skip_history)
        return local_value

    def _add_value(self, request, value, local_value, skip_history=False):
        goal_value = CampaignGoalValue(campaign_goal=self, value=value, local_value=local_value)
        goal_value.save()

        if not skip_history:
            history_value = local_value
            currency_symbol = core.features.multicurrency.get_currency_symbol(self.campaign.account.currency)

            import dash.campaign_goals

            if self.type in dash.campaign_goals.COST_DEPENDANT_GOALS:
                history_value = utils.lc_helper.format_currency(history_value, places=3, curr=currency_symbol)

            self.campaign.write_history(
                'Changed campaign goal value: "{}"'.format(CAMPAIGN_GOAL_NAME_FORMAT[self.type].format(history_value)),
                action_type=constants.HistoryActionType.GOAL_CHANGE,
                user=request.user,
            )

    def get_current_value(self):
        try:
            return self.values.latest("created_dt")
        except CampaignGoalValue.DoesNotExist:
            return None

    @transaction.atomic
    def set_primary(self, request):
        CampaignGoal.objects.filter(campaign=self.campaign).update(primary=False)
        self.primary = True
        self.save()

        self.campaign.write_history(
            'Campaign goal "{}" set as primary'.format(constants.CampaignGoalKPI.get_text(self.type)),
            action_type=constants.HistoryActionType.GOAL_CHANGE,
            user=request.user,
        )

    def _get_exchange_rate(self):
        currency = self.campaign.account.currency
        return core.features.multicurrency.get_current_exchange_rate(currency)
