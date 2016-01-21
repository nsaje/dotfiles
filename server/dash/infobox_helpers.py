import copy
import datetime
import exceptions

import reports.api_helpers

import dash.constants
import dash.budget
import dash.models
import reports.api_contentads

from decimal import Decimal


class OverviewSetting(object):

    def __init__(self, name='', value='', description=None, tooltip=None, setting_type='setting'):
        self.name = name
        self.value = value
        self.description = description
        self.details_label = None
        self.details_content = None
        self.icon = None
        self.type = setting_type
        self.tooltip = tooltip

    def comment(self, details_label, details_description):
        ret = copy.deepcopy(self)
        ret.details_label = details_label
        ret.details_content = details_description
        return ret

    def performance(self, ok):
        ret = copy.deepcopy(self)
        ret.icon = 'happy' if ok else 'sad'
        return ret

    def as_dict(self):
        ret = {}
        for key, value in self.__dict__.iteritems():
            if value is not None:
                ret[key] = value
        return ret


class OverviewSeparator(OverviewSetting):
    def __init__(self):
        super(OverviewSeparator, self).__init__('', '', '', setting_type='hr')


def get_reports_api_module(user):
    if user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
        return reports.api_contentads
    return reports.api


def format_flight_time(start_date, end_date):
    start_date_str = start_date.strftime('%m/%d') if start_date else ''
    end_date_str = end_date.strftime('%m/%d') if end_date else ''

    flight_time = "{start_date} - {end_date}".format(
        start_date=start_date_str,
        end_date=end_date_str,
    )
    today = datetime.datetime.today().date()
    if not end_date:
        flight_time_left_days = None
    elif today > end_date:
        flight_time_left_days = 0
    else:
        flight_time_left_days = (end_date - today).days + 1
    return flight_time, flight_time_left_days


def get_ideal_campaign_spend(user, campaign, until_date=None):
    at_date = until_date or datetime.datetime.today().date()
    budgets = dash.models.BudgetLineItem.objects.filter(campaign=campaign)

    all_budget_spends_at_date = [b.get_ideal_budget_spend(at_date) for b in budgets]
    return sum(all_budget_spends_at_date)


def get_total_campaign_spend(user, campaign, until_date=None):
    campaign_budget = dash.budget.CampaignBudget(campaign)
    return campaign_budget.get_spend(until_date=until_date)


def get_yesterday_spend(user, campaign):
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    budgets = dash.models.BudgetLineItem.objects.filter(campaign=campaign)

    all_budget_spends_at_date = [
        b.get_spend_data(date=yesterday, use_decimal=True)['total'] for b in budgets
    ]
    return sum(all_budget_spends_at_date)


def get_goal_value(user, campaign, campaign_settings, goal_type):
    # we are interested in reaching the goal by today
    end_date = datetime.datetime.today().date()
    totals_stats = reports.api_helpers.filter_by_permissions(
        get_reports_api_module(user).query(
            campaign.created_dt,
            end_date,
            campaign=campaign,
        ), user)
    if goal_type == dash.constants.CampaignGoal.CPA:
        # CPA is still being implemented via Conversion&Goals epic
        return 0  # TODO implement this properly
    elif goal_type == dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE:
        return totals_stats.get('bounce_rate', 0) or 0
    elif goal_type == dash.constants.CampaignGoal.NEW_UNIQUE_VISITORS:
        return totals_stats.get('new_visits', 0) or 0
    elif goal_type == dash.constants.CampaignGoal.SECONDS_TIME_ON_SITE:
        return totals_stats.get('avg_tos', 0) or 0
    elif goal_type == dash.constants.CampaignGoal.PAGES_PER_SESSION:
        return totals_stats.get('pv_per_visit', 0) or 0

    # assuming we will add moar campaign goals in the future
    raise exceptions.NotImplementedError()


def get_goal_difference(goal_type, target, actual):
    """
    Returns difference as (value, description, success) tuple
    """
    if actual is None:
        return 0, "N/A", False

    if goal_type in (dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE,):
        diff = target - actual
        rate = diff / target if target > 0 else 0
        description = '{rate:.2f}% {word} planned'.format(
            rate=rate,
            word='above' if rate > 0 else 'below'
        )
        success = diff <= 0
        return diff, description, success
    else:
        diff = target - actual
        description = '{diff} {word} planned'.format(
            diff=abs(diff),
            word='above' if diff < 0 else 'below',
        )
        success = diff <= 0
        return diff, description, success


def calculate_daily_cap(campaign):
    daily_cap_cc = Decimal(0)
    ad_groups = dash.models.AdGroup.objects.filter(campaign=campaign).exclude_archived()
    for ad_group in ad_groups:
        ad_group_settings = ad_group.get_current_settings()
        daily_cap_cc = daily_cap_cc + Decimal(ad_group_settings.daily_budget_cc) or Decimal(0)
    # TODO: daily_cap_cc IS NOT CC
    return int(daily_cap_cc)


def goals_and_spend_settings(user, campaign):
    settings = []

    filled_daily_ratio = 0
    yesterday_cost = get_yesterday_spend(user, campaign) or 0
    campaign_daily_budget = calculate_daily_cap(campaign)

    if campaign_daily_budget > 0:
        filled_daily_ratio = min(yesterday_cost / float(campaign_daily_budget), 1)

    yesterday_spend_settings = OverviewSetting(
        'Yesterday spend:',
        '${:.2f}'.format(yesterday_cost),
        description='{:.2f}% of daily cap'.format(abs(filled_daily_ratio) * 100),
    ).performance(
        filled_daily_ratio >= 1.0
    )
    settings.append(yesterday_spend_settings.as_dict())

    total_campaign_spend_to_date = get_total_campaign_spend(user, campaign)
    ideal_campaign_spend_to_date = get_ideal_campaign_spend(user, campaign)

    ratio = 0
    if ideal_campaign_spend_to_date > 0:
        ratio = min(
            (total_campaign_spend_to_date - ideal_campaign_spend_to_date) / ideal_campaign_spend_to_date,
            1)
    campaign_pacing_settings = OverviewSetting(
        'Campaign pacing:',
        '{:.2f}%'.format(ratio * 100),
        description='${:.2f}'.format(total_campaign_spend_to_date)
    ).performance(total_campaign_spend_to_date >= ideal_campaign_spend_to_date)
    settings.append(campaign_pacing_settings.as_dict())

    campaign_settings = campaign.get_current_settings()
    campaign_goals = [(
        campaign_settings.campaign_goal,
        campaign_settings.goal_quantity,
    )
    ]
    for i, (goal, quantity) in enumerate(campaign_goals):
        text = dash.constants.CampaignGoal.get_text(goal)
        name = 'Campaign goals:' if i == 0 else ''

        try:
            goal_value = get_goal_value(user, campaign, campaign_settings, goal)
        except NotImplementedError:
            goal_value = None
        goal_diff, description, success = get_goal_difference(
            goal,
            float(quantity),
            goal_value
        )
        goal_setting = OverviewSetting(
            name,
            '{actual_goal} {value}'.format(
                actual_goal=format_goal_value(goal_value, goal),
                value=text
            ),
            description
        ).performance(success)
        settings.append(goal_setting.as_dict())

    is_delivering = ideal_campaign_spend_to_date >= total_campaign_spend_to_date
    return settings, is_delivering


def format_goal_value(goal_value, goal_type):
    if not goal_value:
        return 0
    if goal_type in (dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE,):
        return float(goal_value)
    else:
        return int(goal_value)
