import operator
from decimal import ROUND_CEILING
from decimal import ROUND_DOWN
from decimal import Decimal
from random import betavariate
from random import random

import core.features.bcm
import core.models.all_rtb
import dash
import dash.constants
import dash.views.helpers
from utils import zlogging

from .. import constants
from .. import settings
from . import helpers

logger = zlogging.getLogger(__name__)


def get_autopilot_daily_budget_recommendations(
    campaign, daily_budget, ad_groups_data, bcm_modifiers, campaign_goal=None, ignore_daily_budget_too_small=False
):
    daily_budget = daily_budget.quantize(Decimal("1."), rounding=ROUND_DOWN)
    new_budgets, old_budgets = _get_autopilot_budget_constraints(ad_groups_data, daily_budget, bcm_modifiers)
    min_new_budgets_sum = sum(new_budgets.values())
    budget_left = daily_budget - min_new_budgets_sum
    comments = []

    # Don't add any budget to ad groups with insufficient spend
    active_ad_groups_with_spend = _get_active_ad_groups_with_spend(ad_groups_data, new_budgets)
    if len(active_ad_groups_with_spend) < 1:
        logger.info(
            str(campaign) + " does not have any active ad groups with enough spend. Uniformly redistributed budget."
        )
        comments.append(constants.DailyBudgetChangeComment.NO_ACTIVE_AD_GROUPS_WITH_SPEND)

        # recalculate min budgets without MAX_BUDGET_LOSS when no ad groups with spend
        new_budgets = _get_minimum_autopilot_budget_constraints(ad_groups_data, bcm_modifiers)
        min_new_budgets_sum = sum(new_budgets.values())
        budget_left = daily_budget - min_new_budgets_sum

        _uniformly_redistribute_remaining_budget(new_budgets, budget_left)

    else:
        bandit = BetaBandit(active_ad_groups_with_spend, backup_ad_groups=ad_groups_data.keys())
        min_value_of_optimization_goal, max_value_of_optimization_goal = _get_min_max_values_of_optimization_goal(
            list(ad_groups_data.values()), campaign_goal
        )

        # Train bandit
        for ad_group in active_ad_groups_with_spend:
            for i in range(5):
                bandit.add_result(
                    ad_group,
                    _predict_outcome_success(
                        ad_groups_data[ad_group],
                        campaign_goal,
                        min_value_of_optimization_goal,
                        max_value_of_optimization_goal,
                        bcm_modifiers,
                    ),
                )

        # Redistribute budgets
        while budget_left >= 1:
            if len(_get_active_ad_groups_with_spend(ad_groups_data, new_budgets)) < 1:
                _uniformly_redistribute_remaining_budget(new_budgets, budget_left)
                logger.info(
                    str(campaign)
                    + " used up all smart budget, now uniformly redistributed remaining $"
                    + str(budget_left)
                    + "."
                )
                comments.append(constants.DailyBudgetChangeComment.USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED)
                break

            budget_left -= Decimal(1.0)
            recommended_ag = bandit.get_recommendation()

            if not recommended_ag:
                break

            new_budgets[recommended_ag] += Decimal(1)
            bandit.add_result(
                recommended_ag,
                _predict_outcome_success(
                    ad_groups_data[recommended_ag],
                    campaign_goal,
                    min_value_of_optimization_goal,
                    max_value_of_optimization_goal,
                    bcm_modifiers,
                    new_budget=new_budgets[recommended_ag],
                ),
            )
            ad_group_max_daily_budget = core.models.all_rtb.AllRTBSourceType.get_etfm_max_daily_budget(bcm_modifiers)

            if new_budgets[recommended_ag] >= ad_group_max_daily_budget:
                bandit.remove_ad_group(recommended_ag)

    if daily_budget < min_new_budgets_sum:
        if not ignore_daily_budget_too_small:
            logger.warning(
                "Budget Autopilot got too small daily budget",
                daily_budget=daily_budget,
                minimum=min_new_budgets_sum,
                campaign_id=campaign.id,
            )

    elif sum(new_budgets.values()) != daily_budget:
        logger.error(
            "Budget Autopilot tried assigning wrong ammount of total daily spend caps",
            expected=str(daily_budget),
            proposed=str(sum(new_budgets.values())),
            campaign_id=str(campaign.id),
        )
        comments = [constants.DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET]
        new_budgets = old_budgets

    return {
        ad_group: {
            "old_budget": old_budgets[ad_group],
            "new_budget": new_budgets[ad_group],
            "budget_comments": comments,
        }
        for ad_group in ad_groups_data.keys()
    }


def _get_min_max_values_of_optimization_goal(data, campaign_goal):
    max_value = 0.0
    min_value = float("inf")

    if campaign_goal:
        col = helpers.get_campaign_goal_column(campaign_goal)

        for entry in data:
            current = entry[col]

            if current:
                max_value = max(current, max_value)
                min_value = min(current, min_value)

    return min_value, max_value


def _uniformly_redistribute_remaining_budget(new_budgets, budget_left):
    budget_count = len(new_budgets)
    new_budget_chunk = budget_left // budget_count
    budget_left %= budget_count

    for ad_group in new_budgets.keys():
        new_budgets[ad_group] += new_budget_chunk

    while budget_left >= 1:
        for ad_group in new_budgets.keys():
            budget_left -= Decimal(1.0)
            new_budgets[ad_group] += Decimal(1)

            if budget_left <= 0:
                break

    return new_budgets


def _get_active_ad_groups_with_spend(ad_groups_data, current_budgets):
    active_ad_groups_with_spend = []

    for ad_group, data in ad_groups_data.items():
        if data.get("yesterdays_spend") / current_budgets.get(ad_group) >= settings.AUTOPILOT_MIN_SPEND_PERC:
            active_ad_groups_with_spend.append(ad_group)

    return active_ad_groups_with_spend


def _get_autopilot_budget_constraints(ad_groups_data, daily_budget, bcm_modifiers):
    autopilot_min_daily_budget = core.features.bcm.calculations.calculate_min_daily_budget(
        settings.BUDGET_AP_MIN_BUDGET, bcm_modifiers
    )

    min_new_budgets, old_budgets = _get_optimistic_autopilot_budget_constraints(
        ad_groups_data, autopilot_min_daily_budget
    )
    if sum(min_new_budgets.values()) > daily_budget:
        min_new_budgets = _get_minimum_autopilot_budget_constraints(
            ad_groups_data, bcm_modifiers, autopilot_min_daily_budget
        )

    return min_new_budgets, old_budgets


def _get_optimistic_autopilot_budget_constraints(ad_groups_data, autopilot_min_daily_budget):
    min_new_budgets = {}
    old_budgets = {}

    for ad_group, data in ad_groups_data.items():
        current_budget = data["old_budget"] or autopilot_min_daily_budget

        min_new_budgets[ad_group] = max(
            Decimal((current_budget * settings.MAX_BUDGET_LOSS).to_integral_exact(rounding=ROUND_CEILING)),
            autopilot_min_daily_budget,
        )
        old_budgets[ad_group] = current_budget

    return min_new_budgets, old_budgets


def _get_minimum_autopilot_budget_constraints(ad_groups_data, bcm_modifiers, autopilot_min_daily_budget=None):
    if autopilot_min_daily_budget is None:
        autopilot_min_daily_budget = core.features.bcm.calculations.calculate_min_daily_budget(
            settings.BUDGET_AP_MIN_BUDGET, bcm_modifiers
        )

    min_new_budgets = {ad_group: autopilot_min_daily_budget for ad_group in ad_groups_data.keys()}

    return min_new_budgets


def _predict_outcome_success(
    data, campaign_goal, min_value_of_campaign_goal, max_value_of_campaign_goal, bcm_modifiers, new_budget=None
):
    ap_settings_min_budget = core.features.bcm.calculations.calculate_min_daily_budget(
        settings.BUDGET_AP_MIN_BUDGET, bcm_modifiers
    )
    spend_perc = (
        data.get("spend_perc")
        if not new_budget
        else data.get("yesterdays_spend") / max(new_budget, ap_settings_min_budget)
    )

    if not campaign_goal:
        return spend_perc > random()

    data_value = data.get(helpers.get_campaign_goal_column(campaign_goal))
    goal_value = 0.0
    if data_value:
        goal_value = _get_campaign_goal_value(
            campaign_goal.type, data_value, max_value_of_campaign_goal, min_value_of_campaign_goal
        )

    spend_weight = min(
        float(spend_perc * settings.GOALS_COLUMNS.get(campaign_goal.type).get("spend_perc")),
        float(settings.GOALS_COLUMNS.get(campaign_goal.type).get("spend_perc")),
    )
    prob_success = spend_weight + goal_value * helpers.get_campaign_goal_column_importance(campaign_goal)
    if spend_perc <= settings.SPEND_PERC_LOWERING_THRESHOLD:
        prob_success = prob_success * settings.LOW_SPEND_PROB_LOWERING_FACTOR

    return prob_success > random()


def _get_campaign_goal_value(campaign_goal_type, data_value, max_value_of_campaign_goal, min_value_of_campaign_goal):
    cg_kpi = dash.constants.CampaignGoalKPI
    if campaign_goal_type == cg_kpi.MAX_BOUNCE_RATE:
        return (100 - data_value) / 100
    if campaign_goal_type == cg_kpi.NEW_UNIQUE_VISITORS:
        return data_value / 100
    if campaign_goal_type in (cg_kpi.TIME_ON_SITE, cg_kpi.PAGES_PER_SESSION, cg_kpi.CPA):
        return data_value / max_value_of_campaign_goal if max_value_of_campaign_goal > 0 else 0.0
    if campaign_goal_type in (
        cg_kpi.CPC,
        cg_kpi.CPV,
        cg_kpi.CP_NON_BOUNCED_VISIT,
        cg_kpi.CP_NEW_VISITOR,
        cg_kpi.CP_PAGE_VIEW,
        cg_kpi.CPCV,
    ):
        return (
            float(min_value_of_campaign_goal / data_value)
            if (data_value > 0.0 and min_value_of_campaign_goal < float("inf"))
            else 0.0
        )
    raise NotImplementedError("Budget Autopilot campaign goal is not implemented: ", campaign_goal_type)


class BetaBandit(object):
    # Bayesian Multi-Arm Bandit / Thompsons Sampling
    # Machine Learning method used for re-assigning budgets in Autopilot
    def __init__(self, ad_groups, backup_ad_groups=[], prior=(1.0, 1.0)):
        self.ad_groups = ad_groups[:]
        self.backup_ad_groups = backup_ad_groups[:]
        all_ad_groups = list(set(ad_groups) | set(backup_ad_groups))
        self.trials = {ag: 0 for ag in all_ad_groups}
        self.successes = {ag: 0 for ag in all_ad_groups}
        self.prior = prior
        self.banned_ad_groups = []

    def add_result(self, ad_group, success):
        self.trials[ad_group] = self.trials[ad_group] + 1
        if success:
            self.successes[ad_group] = self.successes[ad_group] + 1

    def temporarily_ban_ad_group(self, ad_group):
        self.banned_ad_groups.append(ad_group)

    def remove_ad_group(self, ad_group):
        try:
            self.backup_ad_groups.remove(ad_group)
            self.ad_groups.remove(ad_group)
        except ValueError:
            logger.warning("BetaBandit ad group could not be removed as it is not present" + str(ad_group))
        if not self.ad_groups:
            self.ad_groups = self.backup_ad_groups

    def get_recommendation(self):
        sampled_probs = {}
        for ad_group in self.ad_groups:
            # Construct beta distribution for posterior probs and draw samples from it
            sampled_probs[ad_group] = betavariate(
                self.prior[0] + self.successes[ad_group],
                self.prior[1] + self.trials[ad_group] - self.successes[ad_group],
            )

        # Return non-banned ad group with the largest success probability
        sorted_probs = sorted(list(sampled_probs.items()), key=operator.itemgetter(1), reverse=True)
        for prob in sorted_probs:
            if prob[0] not in self.banned_ad_groups:
                return prob[0]

        # All max budgets were reached but we still have budget left, un-ban all and continue redistributing
        self.banned_ad_groups = []
        return sorted_probs[0][0] if sorted_probs else None
