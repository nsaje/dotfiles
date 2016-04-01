import logging
import operator
import exceptions
from decimal import Decimal, ROUND_CEILING
from random import betavariate, random

import dash
import dash.views.helpers
from dash.constants import CampaignGoalKPI
from automation import autopilot_settings, autopilot_helpers
from automation.constants import DailyBudgetChangeComment

logger = logging.getLogger(__name__)


def get_autopilot_daily_budget_recommendations(ad_group, daily_budget, data, campaign_goal=None):
    active_sources = data.keys()

    max_budgets, new_budgets, old_budgets = _get_autopilot_budget_constraints(active_sources, daily_budget)
    comments = []
    budget_left = daily_budget - sum(new_budgets.values())

    # Don't add any budget to sources with insufficient spend
    active_sources_with_spend = _get_active_sources_with_spend(active_sources, data)
    if len(active_sources_with_spend) < 1:
        msg = str(ad_group) + ' does not have any active sources with enough spend. Uniformly redistributed budget.'
        logger.info(msg)
        comments.append(DailyBudgetChangeComment.NO_ACTIVE_SOURCES_WITH_SPEND)
        new_budgets = _uniformly_redistribute_remaining_budget(active_sources, budget_left, new_budgets)
    else:
        bandit = BetaBandit(active_sources_with_spend, backup_sources=active_sources)
        min_value_of_campaign_goal, max_value_of_campaign_goal = _get_min_max_values_of_campaign_goal(
            data.values(), campaign_goal)
        # Train bandit
        for s in active_sources_with_spend:
            for i in range(5):
                bandit.add_result(s, predict_outcome_success(
                    s, data[s], campaign_goal, min_value_of_campaign_goal, max_value_of_campaign_goal))

        # Redistribute budgets
        while budget_left >= 1:
            budget_left -= Decimal(1.0)
            s = bandit.get_recommendation()
            if not s:
                break
            new_budgets[s] += Decimal(1)
            bandit.add_result(s, predict_outcome_success(s, data[s], campaign_goal, min_value_of_campaign_goal,
                                                         max_value_of_campaign_goal, new_budget=new_budgets[s]))
            if new_budgets[s] >= s.source.source_type.max_daily_budget:
                bandit.remove_source(s)

    if sum(new_budgets.values()) != daily_budget:
        logger.warning('Budget Auto-Pilot tried assigning wrong ammount of total daily budgets - Expected: ' +
                       str(daily_budget) + ' Proposed: ' + str(sum(new_budgets.values())) + ' on AdGroup: ' +
                       str(ad_group) + ' ( ' + str(ad_group.id) + ' )')
        comments = [DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET]
        new_budgets = old_budgets
    return {s: {'old_budget': old_budgets[s], 'new_budget': new_budgets[s], 'budget_comments': comments}
            for s in active_sources}


def _get_min_max_values_of_campaign_goal(data, campaign_goal):
    max_value = 0.0
    min_value = float("inf")
    if campaign_goal:
        col = autopilot_helpers.get_campaign_goal_column(campaign_goal)
        for row in data:
            current = row[col]
            max_value = max(current, max_value)
            min_value = min(current, min_value) if current else min_value
    return min_value, max_value


def _uniformly_redistribute_remaining_budget(sources, budget_left, min_budgets):
    while budget_left >= 1:
        for s in sources:
            budget_left -= Decimal(1.0)
            min_budgets[s] += Decimal(1)
            if budget_left <= 0:
                break
    return min_budgets


def _get_active_sources_with_spend(active_sources, data):
    active_sources_with_spend = []
    for s in active_sources:
        if data[s].get('spend_perc') >= autopilot_settings.AUTOPILOT_MIN_SPEND_PERC:
            active_sources_with_spend.append(s)
    return active_sources_with_spend


def _get_autopilot_budget_constraints(active_sources, daily_budget):
    max_budgets, min_budgets, old_budgets = _get_optimistic_autopilot_budget_constraints(active_sources)
    if sum(min_budgets.values()) > daily_budget:
        max_budgets, min_budgets = _get_minimum_autopilot_budget_constraints(active_sources)
    return max_budgets, min_budgets, old_budgets


def _get_optimistic_autopilot_budget_constraints(active_sources):
    max_budgets = {}
    min_budgets = {}
    old_budgets = {}
    ags_settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__in=active_sources)\
                                                    .group_current_settings().select_related('ad_group_source')
    for source_settings in ags_settings:
        current_budget = source_settings.daily_budget_cc
        source = source_settings.ad_group_source
        if not current_budget:
            current_budget = autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET
        max_budgets[source] = Decimal((current_budget * autopilot_settings.MAX_BUDGET_GAIN).
                                      to_integral_exact(rounding=ROUND_CEILING))
        min_budgets[source] = max(Decimal((current_budget * autopilot_settings.MAX_BUDGET_LOSS).
                                  to_integral_exact(rounding=ROUND_CEILING)),
                                  autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET,
                                  source.source.source_type.min_daily_budget)
        old_budgets[source] = current_budget
    return max_budgets, min_budgets, old_budgets


def _get_minimum_autopilot_budget_constraints(active_sources):
    max_budgets = {}
    min_budgets = {}
    for source in active_sources:
        min_budgets[source] = autopilot_helpers.get_ad_group_sources_minimum_daily_budget(source)
        max_budgets[source] = (min_budgets[source] * autopilot_settings.MAX_BUDGET_GAIN).\
            to_integral_exact(rounding=ROUND_CEILING)
    return max_budgets, min_budgets


def predict_outcome_success(source, data, campaign_goal, min_value_of_campaign_goal,
                            max_value_of_campaign_goal, new_budget=None):
    spend_perc = data.get('spend_perc') if not new_budget else\
        data.get('yesterdays_spend_cc') / max(new_budget, autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET)

    if not campaign_goal:
        return spend_perc > random()

    data_value = data.get(autopilot_helpers.get_campaign_goal_column(campaign_goal))
    goal_value = 0.0
    if data_value:
        goal_value = _get_campaign_goal_value(campaign_goal.type, data_value,
                                              max_value_of_campaign_goal, min_value_of_campaign_goal)

    spend_weight = min(float(spend_perc * autopilot_settings.GOALS_COLUMNS.get(campaign_goal.type).get('spend_perc')),
                       float(autopilot_settings.GOALS_COLUMNS.get(campaign_goal.type).get('spend_perc')))
    prob_success = spend_weight + goal_value * autopilot_helpers.get_campaign_goal_column_importance(campaign_goal)
    if spend_perc <= autopilot_settings.SPEND_PERC_LOWERING_THRESHOLD:
        prob_success = prob_success * autopilot_settings.LOW_SPEND_PROB_LOWERING_FACTOR
    return prob_success > random()


def _get_campaign_goal_value(campaign_goal_type, data_value, max_value_of_campaign_goal, min_value_of_campaign_goal):
    if campaign_goal_type == CampaignGoalKPI.MAX_BOUNCE_RATE:
        return (100 - data_value) / 100
    if campaign_goal_type == CampaignGoalKPI.NEW_UNIQUE_VISITORS:
        return data_value / 100
    if campaign_goal_type in [CampaignGoalKPI.TIME_ON_SITE, CampaignGoalKPI.PAGES_PER_SESSION]:
        return data_value / max_value_of_campaign_goal
    if campaign_goal_type == CampaignGoalKPI.CPC:
        return float(min_value_of_campaign_goal / data_value)
    raise exceptions.NotImplementedError('Budget Auto-Pilot campaign goal is not implemented: ', campaign_goal_type)


def get_adgroup_minimum_daily_budget(adgroup=None):
    return len(autopilot_helpers.get_autopilot_active_sources_settings([adgroup])) *\
        autopilot_settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC


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
        if (success):
            self.successes[source] = self.successes[source] + 1

    def temporarily_ban_source(self, source):
        self.banned_sources.append(source)

    def remove_source(self, source):
        try:
            self.backup_sources.remove(source)
            self.sources.remove(source)
        except ValueError:
            logger.warning('BetaBandit source could not be removed as it is not present' + str(source))
        if not self.sources:
            self.sources = self.backup_sources

    def get_recommendation(self):
        sampled_probs = {}
        for source in self.sources:
            # Construct beta distribution for posterior probs and draw samples from it
            sampled_probs[source] = betavariate(self.prior[0] + self.successes[source],
                                                self.prior[1] + self.trials[source] - self.successes[source])

        # Return non-banned source with the largest success probability
        sorted_probs = sorted(sampled_probs.items(), key=operator.itemgetter(1), reverse=True)
        for prob in sorted_probs:
            if prob[0] not in self.banned_sources:
                return prob[0]

        # All max budgets were reached but we still have budget left, un-ban all and continue redistributing
        self.banned_sources = []
        return sorted_probs[0][0] if sorted_probs else None
