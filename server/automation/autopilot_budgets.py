import datetime
import logging
import operator
import traceback
import pytz
from decimal import Decimal, ROUND_CEILING
from random import betavariate, random

from django.core.mail import send_mail
from django.conf import settings
from utils import pagerduty_helper

import dash
import dash.views.helpers
import automation.settings
import automation.constants
import reports.api_contentads
from automation import helpers
from dash import constants
from utils.statsd_helper import statsd_gauge, statsd_timer


logger = logging.getLogger(__name__)

MAX_BUDGET_GAIN = Decimal(1.2)
MAX_BUDGET_LOSS = Decimal(0.8)
MIN_SOURCE_BUDGET = Decimal(10.0)
GOALS_COLUMNS = {
    'bounce_and_spend': {'bounce_rate': 0.7, 'spend_perc': 0.3}
}
GOALS_WORST_VALUE = {
    'bounce_rate': 100.00,
    'spend': 0.00,
}
DEBUG_EMAILS = ['davorin.kopic@zemanta.com']


@statsd_timer('automation.autopilot_budgets', 'adjust_autopilot_ad_groups_budgets_timer')
def adjust_autopilot_ad_groups_budgets():
    adgroups = get_adgroups_on_autopilot()
    statsd_gauge('automation.autopilot_budgets.autopilot_adgroups_count', len(adgroups))
    ap_statsd_autopilot_sources_count = 0
    ap_statsd_total_daily_budget = Decimal('0.0')
    ap_statsd_unassigned_daily_budget = Decimal('0.0')
    ap_statsd_adgroups_processed = 0

    for adgroup in adgroups:
        goal = _get_adgroups_autopilot_goal(adgroup)
        sources = dash.views.helpers.get_active_ad_group_sources(dash.models.AdGroup, [adgroup])
        active_sources = [s for s in sources if
                          s.get_current_settings().state == constants.AdGroupSourceSettingsState.ACTIVE]
        ap_statsd_autopilot_sources_count += len(active_sources)

        data = get_historic_data(adgroup, active_sources, GOALS_COLUMNS.get(goal).keys())
        max_budgets, new_budgets, old_budgets = _get_autopilot_budget_constraints(active_sources)

        total_daily_budget = adgroup.get_current_settings().autopilot_daily_budget
        ap_statsd_total_daily_budget += total_daily_budget

        bandit = BetaBandit(active_sources)

        budget_left = total_daily_budget - sum(new_budgets.values())

        # Train bandit
        for i in range(budget_left):
            s = bandit.get_recommendation()
            bandit.add_result(s, predict_outcome_success(s, data[s], goal))

        # Redistribute budgets
        while budget_left >= 1:
            budget_left -= Decimal(1.0)
            s = bandit.get_recommendation()
            new_budgets[s] += 1
            if new_budgets[s] >= max_budgets[s]:
                bandit.ban_source(s)

        set_new_daily_budgets(active_sources, new_budgets)

        # send debug email, will be completely removed
        email_changes_text = 'Total Budget:\t' + str(total_daily_budget) +\
            '\nBudget Assigned:\t' + str(sum(new_budgets.values())) +\
            '\nBudget Left Unassigned:\t' + str(total_daily_budget - sum(new_budgets.values())) +\
            '\n\nSource\tPreviousBudget\tNewBudget\tMaxGuideline\tSpend_perc_after_budget_allocation\tBounceRate\n'
        for source in active_sources:
            email_changes_text += ''.join([str(source), '\t', str(old_budgets[source]), '\t',
                                          str(source.get_current_settings().daily_budget_cc), '\t',
                                          str(max_budgets[source]), '\t',
                                          str(get_spend_perc(source)), '\t',
                                          str(data[source].get('bounce_rate')), '\n'])
        send_autopilot_daily_budget_changes_email(adgroup.name, DEBUG_EMAILS, email_changes_text)

        ap_statsd_unassigned_daily_budget += budget_left
        ap_statsd_adgroups_processed += 1

    statsd_gauge('automation.autopilot_budgets.autopilot_sources_count', ap_statsd_autopilot_sources_count)
    statsd_gauge('automation.autopilot_budgets.total_daily_budget', ap_statsd_total_daily_budget)
    statsd_gauge('automation.autopilot_budgets.unassigned_daily_budget', ap_statsd_unassigned_daily_budget)
    statsd_gauge('automation.autopilot_budgets.adgroups_processed', ap_statsd_adgroups_processed)


def _get_adgroups_autopilot_goal(adgroup):
    # TODO: When Campaign Goals are finished will be fetched from there
    return 'bounce_and_spend'


def _get_autopilot_budget_constraints(active_sources):
    max_budgets = {}
    new_budgets = {}
    old_budgets = {}
    for source in active_sources:
        current_budget = source.get_current_settings().daily_budget_cc
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
            if adg.get_current_settings().autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE]


def predict_outcome_success(source, data, goal):
    # Only 'Volume (% spend) and Bounce Rate' is supported atm, other goals will be supported eventually
    if goal == 'bounce_and_spend':
        spend_perc = data.get('spend_perc')
        bounce_rate = data.get('bounce_rate')
        pos_bounce_rate = (100 - bounce_rate) / 100
        prob_success = spend_perc * GOALS_COLUMNS.get(goal).get('spend_perc') +\
            pos_bounce_rate * GOALS_COLUMNS.get(goal).get('bounce_rate')
        return prob_success > random()
    return random() > 0.5


def get_spend_perc(ad_group_source, day=datetime.date.today()):
    yesterday_spend = reports.api.get_day_cost(
        day,
        ad_group=ad_group_source.ad_group,
        source=ad_group_source.source
    ).get('cost')

    if yesterday_spend:
        return float(Decimal(yesterday_spend) / ad_group_source.get_current_settings().daily_budget_cc)
    return 0.0


def get_historic_data(ad_group, ad_group_sources, columns):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today = datetime.date(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)
    days_ago = yesterday - datetime.timedelta(days=2)
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
                data[ags][col] = get_spend_perc(ags, today)
            elif stat and col in stat:
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
        logger.exception(u'Auto-pilot daily budgets e-mail for adgroup %s to %s' +
                         'was not sent because an exception was raised:',
                         adgroup_name,
                         u''.join(emails))
        desc = {
            'adgroup_name': adgroup_name,
            'email': ''.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_daily_budgets_autopilot_email',
            description='Auto-pilot daily budgets e-mail for adgroup was not sent because ' +
                        'an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc
        )


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
