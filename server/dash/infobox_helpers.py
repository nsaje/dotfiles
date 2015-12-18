import datetime
import exceptions

import reports.api_helpers

import dash.constants
import dash.budget
import dash.models
import reports.api_contentads


def get_reports_api_module(user):
    if user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
        return reports.api_contentads
    return reports.api


def calculate_flight_time(start_date, end_date):
    end_date = end_date
    if end_date is not None:
        end_date_str = end_date.strftime('%m/%d')
    else:
        end_date_str = ''

    flight_time = "{start_date} - {end_date}".format(
        start_date=start_date.strftime('%m/%d'),
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


def get_ideal_campaign_spend(user, campaign):
    # I use campaign budget line items here
    # (which aren't yet in production - 2015/12/09)
    today = datetime.datetime.today().date()
    budgets = dash.models.BudgetLineItem.objects.filter(campaign=campaign)
    return sum( [b.get_ideal_budget_spend(today) for b in budgets] )


def get_total_campaign_spend(user, campaign):
    # TODO: this depends on new budget system to come in place
    # so it's disabled for the moment
    # today = datetime.datetime.today().date()
    # budgets = models.BudgetLineItem.objects.filter(campaign=campaign)
    # return sum( [budget.get_spend() for budget in budgets] )
    campaign_budget = dash.budget.CampaignBudget(campaign)
    return campaign_budget.get_spend()


def get_yesterday_total_cost(user, campaign):
    yesterday_cost = get_reports_api_module(
        user
    ).get_yesterday_cost(campaign=campaign)
    yesterday_total_cost = None
    if yesterday_cost:
        yesterday_total_cost = sum(yesterday_cost.values())
    return yesterday_total_cost


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
        raise exceptions.NotImplementedError()
    elif goal_type == dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE:
        return totals_stats.get('bounce_rate', 0) or 0
    elif goal_type == dash.constants.CampaignGoal.NEW_UNIQUE_VISITORS:
        return totals_stats.get('new_visits_sum', 0) or 0
    elif goal_type == dash.constants.CampaignGoal.SECONDS_TIME_ON_SITE:
        return totals_stats.get('avg_tos', 0) or 0
    elif goal_type == dash.constants.Campaigngoal.PAGES_PER_SESSION:
        return totals_stats.get('pv_per_visit', 0) or 0

    # assuming we will add moar campaign goals in the future
    raise exceptions.NotImplementedError()


def get_goal_difference(goal_type, target, actual):
    """
    Returns difference in value, description and success tuple
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
            diff=diff,
            word='above' if diff > 0 else 'below',
        )
        success = diff >= 0
        return diff, description, success
