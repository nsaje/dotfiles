import logging
import operator
import exceptions
from decimal import Decimal, ROUND_CEILING
from random import betavariate, random

import dash
import dash.views.helpers
from automation import autopilot_settings
from automation.constants import DailyBudgetChangeComment

logger = logging.getLogger(__name__)


def get_autopilot_daily_budget_recommendations(ad_group, daily_budget, data, goal='bounce_and_spend'):
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

        # Train bandit
        for s in active_sources_with_spend:
            for i in range(50):
                bandit.add_result(s, predict_outcome_success(s, data[s], goal))

        # Redistribute budgets
        while budget_left >= 1:
            budget_left -= Decimal(1.0)
            s = bandit.get_recommendation()
            if not s:
                break
            new_budgets[s] += Decimal(1)
            if new_budgets[s] >= s.source.source_type.max_daily_budget:
                bandit.remove_source(s)
            elif new_budgets[s] >= max_budgets[s]:
                bandit.temporarily_ban_source(s)

    if sum(new_budgets.values()) != daily_budget:
        logger.warning('Budget Auto-Pilot tried assigning wrong ammount of total daily budgets - Expected: ' +
                       str(daily_budget) + ' Proposed: ' + str(sum(new_budgets.values())) + ' on AdGroup: ' +
                       str(ad_group) + ' ( ' + str(ad_group.id) + ' )')
        comments = [DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET]
        new_budgets = old_budgets
    return {s: {'old_budget': old_budgets[s], 'new_budget': new_budgets[s], 'budget_comments': comments}
            for s in active_sources}


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
            current_budget = autopilot_settings.MIN_SOURCE_BUDGET
        max_budgets[source] = Decimal((current_budget * autopilot_settings.MAX_BUDGET_GAIN).
                                      to_integral_exact(rounding=ROUND_CEILING))
        min_budgets[source] = max(Decimal((current_budget * autopilot_settings.MAX_BUDGET_LOSS).
                                  to_integral_exact(rounding=ROUND_CEILING)), autopilot_settings.MIN_SOURCE_BUDGET,
                                  source.source.source_type.min_daily_budget)
        old_budgets[source] = current_budget
    return max_budgets, min_budgets, old_budgets


def _get_minimum_autopilot_budget_constraints(active_sources):
    max_budgets = {}
    min_budgets = {}
    for source in active_sources:
        min_budgets[source] = max(autopilot_settings.MIN_SOURCE_BUDGET, source.source.source_type.min_daily_budget)
        max_budgets[source] = (min_budgets[source] * autopilot_settings.MAX_BUDGET_GAIN).\
            to_integral_exact(rounding=ROUND_CEILING)
    return max_budgets, min_budgets


def predict_outcome_success(source, data, goal):
    # Only 'Volume (% spend) and Bounce Rate' is supported atm, other goals will be supported eventually
    if goal == 'bounce_and_spend':
        spend_perc = data.get('spend_perc')
        bounce_rate = data.get('bounce_rate')
        pos_bounce_rate = (100 - bounce_rate) / 100
        prob_success = min(float(spend_perc * autopilot_settings.GOALS_COLUMNS.get(goal).get('spend_perc')),
                           float(autopilot_settings.GOALS_COLUMNS.get(goal).get('spend_perc'))) +\
            pos_bounce_rate * autopilot_settings.GOALS_COLUMNS.get(goal).get('bounce_rate')
        return prob_success > random()
    raise exceptions.NotImplementedError('Budget Auto-Pilot Goal is not implemented: ', goal)


def get_adgroup_minimum_daily_budget(adgroup=None):
    return autopilot_settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET


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
