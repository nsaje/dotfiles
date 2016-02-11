import datetime
import logging
import operator
import traceback
import exceptions
from decimal import Decimal, ROUND_CEILING
from random import betavariate, random

from django.core.mail import send_mail
from utils import pagerduty_helper

import dash
import dash.views.helpers
import automation.settings
import automation.constants
import automation.autopilot
import reports.api_contentads
from automation import helpers
from dash import constants
from utils.statsd_helper import statsd_gauge, statsd_timer
from utils import dates_helper


logger = logging.getLogger(__name__)

MAX_BUDGET_GAIN = Decimal(1.2)
MAX_BUDGET_LOSS = Decimal(0.8)
MIN_SOURCE_BUDGET = Decimal(10.0)
GOALS_COLUMNS = {
    'bounce_and_spend': {'bounce_rate': 0.7, 'spend_perc': Decimal(0.3)}
}
GOALS_WORST_VALUE = {
    'bounce_rate': 100.00,
    'spend': Decimal(0.00),
}
AUTOPILOT_DATA_LOOKBACK_DAYS = 2
AUTOPILOT_MIN_SPEND_PERC = Decimal(0.50)
BUDGET_AUTOPILOT_MIN_DAILY_BUDGET = Decimal(100)
DEBUG_EMAILS = ['davorin.kopic@zemanta.com', 'tadej.pavlic@zemanta.com', 'urska.kosec@zemanta.com']


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


def _send_debug_emails(cpc_changes, total_daily_budget, new_budgets,
                       active_sources, old_budgets, max_budgets, bandit, data, adgroup):
    # send debug emails, will be completely removed
    for camp, adgroup_changes in cpc_changes.iteritems():
        automation.autopilot.send_autopilot_CPC_changes_email(
            camp.name,
            camp.id,
            camp.account.name,
            DEBUG_EMAILS,
            adgroup_changes
        )

    email_changes_text = 'Total Budget:\t' + str(total_daily_budget) +\
        '\nBudget Assigned:\t' + str(sum(new_budgets.values())) +\
        '\nBudget Left Unassigned:\t' + str(total_daily_budget - sum(new_budgets.values())) +\
        '\n\nSource;PreviousBudget;NewBudget;MaxGuideline;Spend_perc_after_budget_allocation;BounceRate\n'
    for source in active_sources:
        email_changes_text += ';'.join([str(source.source), str(old_budgets[source]),
                                        str(source.get_current_settings().daily_budget_cc),
                                        str(max_budgets[source]),
                                        str('{0:.4g}'.format(get_spend_perc(source))),
                                        str(data[source].get('bounce_rate')), '\n'])
        email_changes_text += '\n' + bandit.get_bandit_status_text()

        send_autopilot_daily_budget_changes_email(str(adgroup.id), DEBUG_EMAILS, email_changes_text)


def _uniformly_redistribute_remaining_budget(sources, budget_left, new_budgets):
    while budget_left >= 1:
        for s in sources:
            budget_left -= Decimal(1.0)
            new_budgets[s] += 1
            if budget_left <= 0:
                break
    return new_budgets


def _get_active_sources_with_spend(active_sources, data):
    active_sources_with_spend = []
    for s in active_sources:
        if data[s].get('spend_perc') > AUTOPILOT_MIN_SPEND_PERC:
            active_sources_with_spend.append(s)
    return active_sources_with_spend


def _get_adgroups_autopilot_goal(adgroup):
    # TODO: When Campaign Goals are finished will be fetched from there
    return 'bounce_and_spend'


def _get_autopilot_budget_constraints(active_sources):
    max_budgets = {}
    new_budgets = {}
    old_budgets = {}
    for source in active_sources:
        current_budget = source.get_current_settings().daily_budget_cc
        if not current_budget:
            current_budget = MIN_SOURCE_BUDGET
        max_budgets[source] = (current_budget * MAX_BUDGET_GAIN).to_integral_exact(rounding=ROUND_CEILING)
        new_budgets[source] = max(
            (current_budget * MAX_BUDGET_LOSS).to_integral_exact(rounding=ROUND_CEILING), MIN_SOURCE_BUDGET)
        old_budgets[source] = current_budget
    return max_budgets, new_budgets, old_budgets


def set_new_daily_budgets(ad_group_sources, new_daily_budgets):
    for source in ad_group_sources:
        automation.helpers.update_ad_group_source_value(source, u'daily_budget_cc', Decimal(new_daily_budgets[source]))


def get_adgroups_on_autopilot():
    active_adgroups = helpers.get_all_active_ad_groups()
    return [adg for adg in active_adgroups
            if adg.get_current_settings().autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET]


def predict_outcome_success(source, data, goal):
    # Only 'Volume (% spend) and Bounce Rate' is supported atm, other goals will be supported eventually
    if goal == 'bounce_and_spend':
        spend_perc = data.get('spend_perc')
        bounce_rate = data.get('bounce_rate')
        pos_bounce_rate = (100 - bounce_rate) / 100
        prob_success = min(float(spend_perc * GOALS_COLUMNS.get(goal).get('spend_perc')), float(GOALS_COLUMNS.get(goal).get('spend_perc'))) +\
            pos_bounce_rate * GOALS_COLUMNS.get(goal).get('bounce_rate')
        return prob_success > random()
    raise exceptions.NotImplementedError('Budget Auto-Pilot Goal is not implemented: ', goal)


def get_spend_perc(ad_group_source, day=datetime.date.today() - datetime.timedelta(days=1)):
    yesterday_spend = reports.api.get_day_cost(
        day,
        ad_group=ad_group_source.ad_group,
        source=ad_group_source.source
    ).get('cost')

    if yesterday_spend:
        return Decimal(yesterday_spend) / ad_group_source.get_current_settings().daily_budget_cc
    return Decimal(0.0)


def get_historic_data(ad_group, ad_group_sources, columns):
    today = dates_helper.local_today()
    yesterday = today - datetime.timedelta(days=1)
    days_ago = yesterday - datetime.timedelta(days=AUTOPILOT_DATA_LOOKBACK_DAYS)
    stats = reports.api_contentads.query(
        days_ago,
        yesterday,
        breakdown=['source'],
        ad_group=ad_group,
        source=[s.source.id for s in ad_group_sources]
    )

    data = {}
    for ags in ad_group_sources:
        stat = None
        for s in stats:
            if s.get('source') == ags.source.id:
                stat = s
                break
        data[ags] = {}
        for col in columns:
            data[ags][col] = GOALS_WORST_VALUE.get(col)
            if col == 'spend_perc':
                data[ags][col] = get_spend_perc(ags, yesterday)
            elif stat and col in stat and stat[col]:
                data[ags][col] = stat[col]
    return data


def send_autopilot_daily_budget_changes_email(adgroup_name, emails, changes_text):
    body = u'''Hi account manager of {adgroup_name}

On your ad group {adgroup_name}, which is set to auto-pilot, the system made the following changes:

{changes}

Yours truly,
Zemanta
    '''
    body = body.format(
        adgroup_name=adgroup_name,
        changes=''.join(changes_text)
    )
    try:
        send_mail(
            u'Ad Group Auto-Pilot Budget Changes - {adgroup_name}'.format(
                adgroup_name=adgroup_name
            ),
            body,
            u'Zemanta <{}>'.format(automation.settings.AUTOPILOT_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Auto-pilot daily budgets e-mail for adgroup %s to %s ' +
                         'was not sent because an exception was raised:',
                         adgroup_name,
                         u''.join(emails))
        desc = {
            'adgroup_name': adgroup_name,
            'email': ', '.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_daily_budgets_autopilot_email',
            description='Auto-pilot daily budgets e-mail for adgroup was not sent because ' +
                        'an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc
        )


def get_adgroup_minimum_daily_budget(adgroup=None):
    return BUDGET_AUTOPILOT_MIN_DAILY_BUDGET


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
