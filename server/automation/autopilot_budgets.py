import logging
import operator
import exceptions
from decimal import Decimal, ROUND_CEILING
from random import betavariate, random

import dash
import dash.views.helpers
from automation import autopilot_settings
import automation.constants

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
        comments.append(automation.constants.DailyBudgetChangeComment.NO_ACTIVE_SOURCES_WITH_SPEND)
        new_budgets = _uniformly_redistribute_remaining_budget(active_sources, budget_left, new_budgets)
    else:
        bandit = BetaBandit(active_sources_with_spend)

        # Train bandit
        for s in active_sources_with_spend:
            for i in range(50):
                bandit.add_result(s, predict_outcome_success(s, data[s], goal))

        # Redistribute budgets
        while budget_left >= 1:
            budget_left -= Decimal(1.0)
            s = bandit.get_recommendation()
            new_budgets[s] += Decimal(1)
            if new_budgets[s] >= max_budgets[s]:
                bandit.ban_source(s)

    if sum(new_budgets.values()) != daily_budget:
        logger.warning('Budget Auto-Pilot tried assigning wrong ammount of total daily budgets - Expected: ' +
                       str(daily_budget) + ' Proposed: ' + str(sum(new_budgets.values())) + ' on AdGroup: ' +
                       str(ad_group) + ' ( ' + str(ad_group.id) + ' )')
        comments = [automation.constants.DailyBudgetChangeComment.NEW_BUDGET_NOT_EQUAL_DAILY_BUDGET]
        new_budgets = old_budgets

    return {s: {'old_budget': old_budgets[s], 'new_budget': new_budgets[s], 'budget_comments': comments}
            for s in active_sources}


'''
@statsd_timer('automation.autopilot_budgets', 'adjust_autopilot_ad_groups_budgets_timer')
def adjust_autopilot_ad_groups_budgets():
    adgroups = get_adgroups_on_autopilot()
    statsd_gauge('automation.autopilot_budgets.autopilot_adgroups_count', len(adgroups))
    ap_statsd_autopilot_sources_count = 0
    ap_statsd_total_daily_budget = Decimal('0.0')
    ap_statsd_unassigned_daily_budget = Decimal('0.0')
    ap_statsd_adgroups_processed = 0

    for adgroup in adgroups:
        logger.info('\nadgroup: ' + str(adgroup) + ' ' + str(adgroup.id) + '\n')
        goal = _get_adgroups_autopilot_goal(adgroup)
        sources = dash.views.helpers.get_active_ad_group_sources(dash.models.AdGroup, [adgroup])
        active_sources = [s for s in sources if
                          s.get_current_settings().state == constants.AdGroupSourceSettingsState.ACTIVE]
        ap_statsd_autopilot_sources_count += len(active_sources)

        data = get_historic_data(adgroup, active_sources, GOALS_COLUMNS.get(goal).keys())
        logger.info('data: ' + str(data) + '\n')
        max_budgets, new_budgets, old_budgets = _get_autopilot_budget_constraints(active_sources)

        total_daily_budget = adgroup.get_current_settings().autopilot_daily_budget
        ap_statsd_total_daily_budget += total_daily_budget
        logger.info('max_budgets: ' + str(max_budgets) + '\n')
        logger.info('new_budgets: ' + str(new_budgets) + '\n')
        logger.info('old_budgets: ' + str(old_budgets) + '\n')
        logger.info('total_daily_budget: ' + str(total_daily_budget) + '\n')

        budget_left = total_daily_budget - sum(new_budgets.values())

        # Don't add any budget to sources with insufficient spend
        active_sources_with_spend = _get_active_sources_with_spend(active_sources, data)

        if len(active_sources_with_spend) < 1:
            msg = str(adgroup) +\
                ' does not have any active sources with enough spend. Uniformly redistributed remaining budget.'
            logger.info(msg)
            new_budgets = _uniformly_redistribute_remaining_budget(active_sources, budget_left, new_budgets)
            set_new_daily_budgets(active_sources, new_budgets)
            send_autopilot_daily_budget_changes_email(adgroup.id, DEBUG_EMAILS, msg)
            continue

        bandit = BetaBandit(active_sources_with_spend)

        # Train bandit
        for s in active_sources_with_spend:
            for i in range(50):
                bandit.add_result(s, predict_outcome_success(s, data[s], goal))

        # Redistribute budgets
        while budget_left >= 1:
            budget_left -= Decimal(1.0)
            s = bandit.get_recommendation()
            new_budgets[s] += 1
            if new_budgets[s] >= max_budgets[s]:
                bandit.ban_source(s)

        set_new_daily_budgets(active_sources, new_budgets)

        # Run CPC Auto-Pilot
        cpc_changes = automation.autopilot.run_cpc_autopilot_on_adgroup(adgroup, {}, True)

        _send_debug_emails(cpc_changes, total_daily_budget, new_budgets,
                           active_sources, old_budgets, max_budgets, bandit, data, adgroup)
        ap_statsd_unassigned_daily_budget += budget_left
        ap_statsd_adgroups_processed += 1

    statsd_gauge('automation.autopilot_budgets.autopilot_sources_count', ap_statsd_autopilot_sources_count)
    statsd_gauge('automation.autopilot_budgets.total_daily_budget', ap_statsd_total_daily_budget)
    statsd_gauge('automation.autopilot_budgets.unassigned_daily_budget', ap_statsd_unassigned_daily_budget)
    statsd_gauge('automation.autopilot_budgets.adgroups_processed', ap_statsd_adgroups_processed)
'''


def _uniformly_redistribute_remaining_budget(sources, budget_left, new_budgets):
    while budget_left >= 1:
        for s in sources:
            budget_left -= Decimal(1.0)
            new_budgets[s] += Decimal(1)
            if budget_left <= 0:
                break
    return new_budgets


def _get_active_sources_with_spend(active_sources, data):
    active_sources_with_spend = []
    for s in active_sources:
        if data[s].get('spend_perc') > autopilot_settings.AUTOPILOT_MIN_SPEND_PERC:
            active_sources_with_spend.append(s)
    return active_sources_with_spend


def _get_autopilot_budget_constraints(active_sources, daily_budget):
    max_budgets, new_budgets, old_budgets = _get_optimistic_autopilot_budget_constraints(active_sources)
    if sum(new_budgets.values()) > daily_budget:
        max_budgets, new_budgets = _get_minimum_autopilot_budget_constraints(active_sources, daily_budget)
    return max_budgets, new_budgets, old_budgets


def _get_optimistic_autopilot_budget_constraints(active_sources):
    max_budgets = {}
    new_budgets = {}
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
        new_budgets[source] = max(Decimal((current_budget * autopilot_settings.MAX_BUDGET_LOSS).
                                  to_integral_exact(rounding=ROUND_CEILING)), autopilot_settings.MIN_SOURCE_BUDGET)
        old_budgets[source] = current_budget
    return max_budgets, new_budgets, old_budgets


def _get_minimum_autopilot_budget_constraints(active_sources, daily_budget):
    max_budgets = {}
    new_budgets = {}
    for source in active_sources:
        max_budgets[source] = (autopilot_settings.MIN_SOURCE_BUDGET * autopilot_settings.MAX_BUDGET_GAIN).\
            to_integral_exact(rounding=ROUND_CEILING)
        new_budgets[source] = autopilot_settings.MIN_SOURCE_BUDGET
    return max_budgets, new_budgets


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
    def __init__(self, sources, prior=(1.0, 1.0)):
        self.sources = sources
        self.trials = {s: 0 for s in sources}
        self.successes = {s: 0 for s in sources}
        self.prior = prior
        self.banned_sources = []

    def add_result(self, source, success):
        self.trials[source] = self.trials[source] + 1
        if (success):
            self.successes[source] = self.successes[source] + 1

    def ban_source(self, source):
        self.banned_sources.append(source)

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
        return sorted_probs[0][0]

    def get_bandit_status_text(self):
        t = 'source;trials;successes\n'
        for s in self.sources:
            t += str(s.source) + ';' + str(self.trials[s]) + ';' + str(self.successes[s]) + '\n'
        t += 'Banned sources: ' + ', '.join([str(s.source) for s in self.banned_sources])
        return t
