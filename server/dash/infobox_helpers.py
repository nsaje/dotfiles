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
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    if len(budgets) == 0:
        return Decimal(0)
    all_budget_spends_at_date = [b.get_ideal_budget_spend(at_date) for b in budgets]
    return sum(all_budget_spends_at_date)


def get_ideal_account_spend(user, account, until_date=None):
    at_date = until_date or datetime.datetime.today().date()
    campaigns = dash.models.Campaign.objects.filter(account=account)
    budgets = _retrieve_active_budgetlineitems(campaigns, at_date)
    if len(budgets) == 0:
        return Decimal(0)
    all_budget_spends_at_date = [b.get_ideal_budget_spend(at_date) for b in budgets]
    return sum(all_budget_spends_at_date)


def get_total_and_media_campaign_spend(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    if len(budgets) == 0:
        return Decimal(0), Decimal(0)

    all_budget_spends_at_date = [
        b.get_spend_data(date=at_date, use_decimal=True) for b in budgets
    ]
    return (
        sum(map(lambda bli: bli['total'], all_budget_spends_at_date)),
        sum(map(lambda bli: bli['media'], all_budget_spends_at_date))
    )


def get_daily_media_account_budget(account, at_date):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()
    campaigns = dash.models.Campaign.objects.filter(account=account)
    budgets = _retrieve_active_budgetlineitems(campaigns, at_date)
    if len(budgets) == 0:
        return Decimal(0), Decimal(0)

    all_budget_spends_at_date = [
        b.get_spend_data(date=at_date, use_decimal=True) for b in budgets
    ]
    return (
        sum(map(lambda bli: bli['total'], all_budget_spends_at_date)),
        sum(map(lambda bli: bli['media'], all_budget_spends_at_date))
    )


def get_media_campaign_spend(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    ret = Decimal(0)
    for bli in budgets:
        spend_data = bli.get_spend_data(date=at_date, use_decimal=True)
        ret += spend_data['media']
    return ret


def get_yesterday_adgroup_spend(user, ad_group):
    yesterday_media_cost = reports.api_contentads.get_actual_yesterday_cost(
        {'ad_group': ad_group.id},
        breakdown=['ad_group']
    )
    return sum(yesterday_media_cost.values())


def get_yesterday_campaign_spend(user, campaign):
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    budgets = dash.models.BudgetLineItem.objects.filter(campaign=campaign)
    if len(budgets) == 0:
        return Decimal(0)
    all_budget_spends_at_date = [
        b.get_daily_spend(date=yesterday, use_decimal=True).get('media', 0) for b in budgets
    ]
    return sum(all_budget_spends_at_date)


def get_goal_value(user, campaign, campaign_settings, goal_type):
    # we are interested in reaching the goal by today
    end_date = datetime.datetime.today().date()
    totals_stats = reports.api_helpers.filter_by_permissions(
        reports.api_contentads.query(
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


def goals_and_spend_settings(user, campaign):
    settings = []

    total_campaign_spend_to_date, media_campaign_spend_to_date = get_total_and_media_campaign_spend(user, campaign)
    ideal_campaign_spend_to_date = get_ideal_campaign_spend(user, campaign)

    ratio = 0
    if ideal_campaign_spend_to_date > 0:
        ratio = min(
            total_campaign_spend_to_date / ideal_campaign_spend_to_date,
            1
        )
    campaign_pacing_settings = OverviewSetting(
        'Campaign pacing:',
        '{:.2f}%'.format(ratio * 100),
        description='${:.2f}'.format(media_campaign_spend_to_date)
    ).performance(total_campaign_spend_to_date >= ideal_campaign_spend_to_date)
    settings.append(campaign_pacing_settings.as_dict())

    # TODO: Campaign goals will be disabled until Campaign KPI's ticket gets delivered
    """
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
    """
    is_delivering = ideal_campaign_spend_to_date >= total_campaign_spend_to_date
    return settings, is_delivering


def format_goal_value(goal_value, goal_type):
    if not goal_value:
        return 0
    if goal_type in (dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE,):
        return float(goal_value)
    else:
        return int(goal_value)


def calculate_daily_ad_group_cap(ad_group):
    """
    Daily media cap
    """
    return sum(map(
        _retrieve_daily_cap,
        dash.models.AdGroupSource.objects.filter(ad_group=ad_group)
    ))


def calculate_daily_campaign_cap(campaign):
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).exclude_archived()
    return sum(map(
        _retrieve_daily_cap,
        dash.models.AdGroupSource.objects.filter(
            ad_group=ad_groups
        )
    ))


def calculate_daily_account_cap(account):
    campaigns = dash.models.Campaign.objects.filter(account=account)
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign__in=campaigns
    ).exclude_archived()
    return sum(map(
        _retrieve_daily_cap,
        dash.models.AdGroupSource.objects.filter(
            ad_group=ad_groups
        )
    ))


def calculate_available_media_campaign_budget(campaign):
    # campaign budget based on non-depleted budget line items
    today = datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], today)

    ret = 0
    for bli in budgets:
        available_total_amount = bli.get_available_amount(today)
        available_media_amount = available_total_amount * (Decimal(1) - bli.credit.license_fee)

        ret += available_media_amount
    return ret


def calculate_available_credit(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)

    return sum([Decimal(credit.amount) * (Decimal(1.0) - credit.license_fee) for credit in credits])


def calculate_spend_credit(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)

    budgets = dash.models.BudgetLineItem.objects.filter(credit__in=credits)
    all_budget_spends_at_date = [
        b.get_spend_data(date=today, use_decimal=True) for b in budgets
    ]
    return sum(map(lambda bli: bli['media'], all_budget_spends_at_date))


def calculate_yesterday_account_spend(account):
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    credits = _retrieve_active_creditlineitems(account, yesterday)

    budgets = dash.models.BudgetLineItem.objects.filter(credit__in=credits)
    if len(budgets) == 0:
        return Decimal(0)

    all_budget_spends_at_date = [
        b.get_daily_spend(date=yesterday, use_decimal=True).get('media', 0) for b in budgets
    ]
    return sum(all_budget_spends_at_date)


def create_yesterday_spend_setting(yesterday_cost, daily_budget):
    filled_daily_ratio = None
    if daily_budget > 0:
        filled_daily_ratio = float(yesterday_cost) / float(daily_budget)

    if filled_daily_ratio:
        daily_ratio_description = '{:.2f}% of daily budget'.format(abs(filled_daily_ratio) * 100)
    else:
        daily_ratio_description = 'N/A'

    yesterday_spend_setting = OverviewSetting(
        'Yesterday spend:',
        '${:.2f}'.format(yesterday_cost),
        description=daily_ratio_description,
    ).performance(
        filled_daily_ratio >= 1.0 if filled_daily_ratio else False
    )
    return yesterday_spend_setting


def _retrieve_active_budgetlineitems(campaigns, date):
    return [budget for budget in dash.models.BudgetLineItem.objects.filter(
        campaign__in=campaigns
    ) if budget.state(date) == dash.constants.BudgetLineItemState.ACTIVE]


def _retrieve_active_creditlineitems(account, date):
    return [credit for credit in dash.models.CreditLineItem.objects.filter(
        account=account
    ) if credit.is_active(date) == dash.constants.CreditLineItemStatus.SIGNED]


def _retrieve_daily_cap(ad_group_source):
    adgs_state = ad_group_source.get_latest_state()
    # skip inactive adgroup sources
    if not adgs_state or adgs_state.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
        return 0
    adgs_settings = ad_group_source.get_current_settings()
    if not adgs_settings:
        return 0
    # cc is not actually cc
    return adgs_settings.daily_budget_cc or 0
