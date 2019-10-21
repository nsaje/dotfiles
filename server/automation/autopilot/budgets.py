import operator
from decimal import ROUND_CEILING
from decimal import ROUND_DOWN
from decimal import Decimal
from random import betavariate
from random import random

import structlog

import core.features.bcm
import dash
import dash.constants
import dash.views.helpers

from . import constants
from . import helpers
from . import settings

logger = structlog.get_logger(__name__)


def get_autopilot_daily_budget_recommendations(
    entity,
    daily_budget,
    data,
    bcm_modifiers,
    campaign_goal=None,
    uses_bcm_v2=False,
    ignore_daily_budget_too_small=False,
):
    daily_budget = daily_budget.quantize(Decimal("1."), rounding=ROUND_DOWN)
    active_sources = list(data.keys())
    max_budgets, new_budgets, old_budgets = _get_autopilot_budget_constraints(
        data, daily_budget, uses_bcm_v2, bcm_modifiers
    )
    comments = []
    min_budgets_sum = sum(new_budgets.values())
    budget_left = daily_budget - min_budgets_sum

    # Don't add any budget to sources with insufficient spend
    active_sources_with_spend = _get_active_sources_with_spend(active_sources, data, new_budgets)
    if len(active_sources_with_spend) < 1:
        logger.info(
            str(entity) + " does not have any active sources with enough spend. Uniformly redistributed budget."
        )
        comments.append(constants.DailyBudgetChangeComment.NO_ACTIVE_SOURCES_WITH_SPEND)

        # recalculate min budgets without MIN_BUDGET_LOSS when no sources with spend
        max_budgets, new_budgets = _get_minimum_autopilot_budget_constraints(data, uses_bcm_v2, bcm_modifiers)
        min_budgets_sum = sum(new_budgets.values())
        budget_left = daily_budget - min_budgets_sum

        new_budgets = _uniformly_redistribute_remaining_budget(active_sources, budget_left, new_budgets, bcm_modifiers)
    else:
        bandit = BetaBandit(active_sources_with_spend, backup_sources=active_sources)
        min_value_of_optimization_goal, max_value_of_optimization_goal = _get_min_max_values_of_optimization_goal(
            list(data.values()), campaign_goal, uses_bcm_v2
        )
        # Train bandit
        for s in active_sources_with_spend:
            for i in range(5):
                bandit.add_result(
                    s,
                    predict_outcome_success(
                        s,
                        data[s],
                        campaign_goal,
                        min_value_of_optimization_goal,
                        max_value_of_optimization_goal,
                        bcm_modifiers,
                        uses_bcm_v2=uses_bcm_v2,
                    ),
                )

        # Redistribute budgets
        while budget_left >= 1:
            if len(_get_active_sources_with_spend(active_sources, data, new_budgets)) < 1:
                new_budgets = _uniformly_redistribute_remaining_budget(
                    active_sources, budget_left, new_budgets, bcm_modifiers
                )
                logger.info(
                    str(entity)
                    + " used up all smart budget, now uniformly redistributed remaining $"
                    + str(budget_left)
                    + "."
                )
                comments.append(constants.DailyBudgetChangeComment.USED_UP_BUDGET_THEN_UNIFORMLY_REDISTRIBUTED)
                break
            budget_left -= Decimal(1.0)
            s = bandit.get_recommendation()
            if not s:
                break
            new_budgets[s] += Decimal(1)
            bandit.add_result(
                s,
                predict_outcome_success(
                    s,
                    data[s],
                    campaign_goal,
                    min_value_of_optimization_goal,
                    max_value_of_optimization_goal,
                    bcm_modifiers,
                    new_budget=new_budgets[s],
                    uses_bcm_v2=uses_bcm_v2,
                ),
            )
            max_budget = s.source.source_type.get_etfm_max_daily_budget(bcm_modifiers)
            if new_budgets[s] >= max_budget:
                bandit.remove_source(s)

    if daily_budget < min_budgets_sum:
        if not ignore_daily_budget_too_small:
            logger.warning(
                "Budget Autopilot got too small daily budget",
                daily_budget=daily_budget,
                minimum=min_budgets_sum,
                entity=entity,
                entity_id=entity.id,
            )
    elif sum(new_budgets.values()) != daily_budget:
        logger.error(
            "Budget Autopilot tried assigning wrong ammount of total daily spend caps",
            expected=str(daily_budget),
            proposed=str(sum(new_budgets.values())),
            entity=str(entity),
            entity_id=str(entity.id),
        )
        comments = [constants.DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET]
        new_budgets = old_budgets

    return {
        s: {"old_budget": old_budgets[s], "new_budget": new_budgets[s], "budget_comments": comments}
        for s in active_sources
    }


def _get_min_max_values_of_optimization_goal(data, campaign_goal, uses_bcm_v2):
    max_value = 0.0
    min_value = float("inf")
    if campaign_goal:
        col = helpers.get_campaign_goal_column(campaign_goal, uses_bcm_v2=uses_bcm_v2)
        for row in data:
            current = row[col]
            if current:
                max_value = max(current, max_value)
                min_value = min(current, min_value)
    return min_value, max_value


def _uniformly_redistribute_remaining_budget(sources, budget_left, min_budgets, bcm_modifiers):
    while budget_left >= 1:
        for s in sources:
            if (
                any(b < min_budgets[s] for b in list(min_budgets.values()))
                and s.source != dash.models.AllRTBSource
                and min_budgets[s] == s.source.source_type.get_etfm_min_daily_budget(bcm_modifiers)
            ):
                continue
            budget_left -= Decimal(1.0)
            min_budgets[s] += Decimal(1)
            if budget_left <= 0:
                break
    return min_budgets


def _get_active_sources_with_spend(active_sources, data, current_budgets):
    active_sources_with_spend = []
    for s in active_sources:
        if data[s].get("yesterdays_spend_cc") / current_budgets.get(s) >= settings.AUTOPILOT_MIN_SPEND_PERC:
            active_sources_with_spend.append(s)
    return active_sources_with_spend


def _get_autopilot_budget_constraints(data, daily_budget, uses_bcm_v2, bcm_modifiers):
    max_budgets, min_budgets, old_budgets = _get_optimistic_autopilot_budget_constraints(
        data, uses_bcm_v2, bcm_modifiers
    )
    if sum(min_budgets.values()) > daily_budget:
        max_budgets, min_budgets = _get_minimum_autopilot_budget_constraints(data, uses_bcm_v2, bcm_modifiers)
    return max_budgets, min_budgets, old_budgets


def _get_optimistic_autopilot_budget_constraints(data, uses_bcm_v2, bcm_modifiers):
    max_budgets = {}
    min_budgets = {}
    old_budgets = {}
    active_sources = list(data.keys())
    for ad_group_source in active_sources:
        max_budgets, min_budgets, old_budgets = _populate_optimistic_budget_constraints_row(
            data[ad_group_source]["old_budget"],
            max_budgets,
            min_budgets,
            old_budgets,
            ad_group_source,
            ad_group_source.source.source_type.get_etfm_min_daily_budget(bcm_modifiers),
            uses_bcm_v2,
            bcm_modifiers,
        )

    return max_budgets, min_budgets, old_budgets


def _populate_optimistic_budget_constraints_row(
    current_budget, max_budgets, min_budgets, old_budgets, ags, source_type_min_budget, uses_bcm_v2, bcm_modifiers
):
    ap_settings_min_budget = settings.BUDGET_AP_MIN_SOURCE_BUDGET
    if uses_bcm_v2:
        ap_settings_min_budget = core.features.bcm.calculations.calculate_min_daily_budget(
            ap_settings_min_budget, bcm_modifiers
        )
    if not current_budget:
        current_budget = ap_settings_min_budget
    max_budgets[ags] = Decimal((current_budget * settings.MAX_BUDGET_GAIN).to_integral_exact(rounding=ROUND_CEILING))
    min_budgets[ags] = max(
        Decimal((current_budget * settings.MAX_BUDGET_LOSS).to_integral_exact(rounding=ROUND_CEILING)),
        ap_settings_min_budget,
        source_type_min_budget,
    )
    old_budgets[ags] = current_budget
    return max_budgets, min_budgets, old_budgets


def _get_minimum_autopilot_budget_constraints(data, uses_bcm_v2, bcm_modifiers):
    max_budgets = {}
    min_budgets = {}
    active_sources = list(data.keys())
    for source in active_sources:
        min_budgets[source] = helpers.get_ad_group_sources_minimum_daily_budget(source, uses_bcm_v2, bcm_modifiers)
        max_budgets[source] = (min_budgets[source] * settings.MAX_BUDGET_GAIN).to_integral_exact(rounding=ROUND_CEILING)
    return max_budgets, min_budgets


def predict_outcome_success(
    source,
    data,
    campaign_goal,
    min_value_of_campaign_goal,
    max_value_of_campaign_goal,
    bcm_modifiers,
    new_budget=None,
    uses_bcm_v2=False,
):
    ap_settings_min_budget = core.features.bcm.calculations.calculate_min_daily_budget(
        settings.BUDGET_AP_MIN_SOURCE_BUDGET, bcm_modifiers
    )
    spend_perc = (
        data.get("spend_perc")
        if not new_budget
        else data.get("yesterdays_spend_cc") / max(new_budget, ap_settings_min_budget)
    )

    if not campaign_goal:
        return spend_perc > random()

    data_value = data.get(helpers.get_campaign_goal_column(campaign_goal, uses_bcm_v2))
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


def get_adgroup_minimum_daily_budget(ad_group, ad_group_settings):
    enabled_sources_settings = helpers.get_autopilot_active_sources_settings({ad_group: ad_group_settings})
    if ad_group_settings.b1_sources_group_enabled:
        enabled_sources_settings = [
            a
            for a in enabled_sources_settings
            if a.ad_group_source.source.source_type.type != dash.constants.SourceType.B1
        ]
        if ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            enabled_sources_settings.append(dash.models.AllRTBSource)
    return len(enabled_sources_settings) * settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC


def get_account_default_minimum_daily_budget(account):
    """ Minimum daily budget when using all default settings (Autopilot, All RTB, etc.) """
    allowed_sources = account.allowed_sources.all()
    non_b1_sources = [source for source in allowed_sources if source.source_type.type != dash.constants.SourceType.B1]
    all_rtb_source = [dash.models.AllRTBSource]
    return (len(non_b1_sources) + len(all_rtb_source)) * settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC


class BetaBandit(object):
    # Bayesian Multi-Arm Bandit / Thompsons Sampling
    # Machine Learning method used for re-assigning budgets in Autopilot
    def __init__(self, sources, backup_sources=[], prior=(1.0, 1.0)):
        self.sources = sources[:]
        self.backup_sources = backup_sources[:]
        all_sources = list(set(sources) | set(backup_sources))
        self.trials = {s: 0 for s in all_sources}
        self.successes = {s: 0 for s in all_sources}
        self.prior = prior
        self.banned_sources = []

    def add_result(self, source, success):
        self.trials[source] = self.trials[source] + 1
        if success:
            self.successes[source] = self.successes[source] + 1

    def temporarily_ban_source(self, source):
        self.banned_sources.append(source)

    def remove_source(self, source):
        try:
            self.backup_sources.remove(source)
            self.sources.remove(source)
        except ValueError:
            logger.warning("BetaBandit source could not be removed as it is not present" + str(source))
        if not self.sources:
            self.sources = self.backup_sources

    def get_recommendation(self):
        sampled_probs = {}
        for source in self.sources:
            # Construct beta distribution for posterior probs and draw samples from it
            sampled_probs[source] = betavariate(
                self.prior[0] + self.successes[source], self.prior[1] + self.trials[source] - self.successes[source]
            )

        # Return non-banned source with the largest success probability
        sorted_probs = sorted(list(sampled_probs.items()), key=operator.itemgetter(1), reverse=True)
        for prob in sorted_probs:
            if prob[0] not in self.banned_sources:
                return prob[0]

        # All max budgets were reached but we still have budget left, un-ban all and continue redistributing
        self.banned_sources = []
        return sorted_probs[0][0] if sorted_probs else None
