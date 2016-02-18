import calendar
import copy
import datetime
import exceptions
import utils.lc_helper

import reports.api_helpers
from django.db.models import Sum

import dash.constants
import dash.budget
import dash.models
import zemauth.models
import reports.api_contentads
import reports.models

from utils.statsd_helper import statsd_timer

from decimal import Decimal

MAX_PREVIEW_REGIONS = 1


class OverviewSetting(object):

    def __init__(self,
                 name='',
                 value='',
                 description=None,
                 tooltip=None,
                 setting_type='setting',
                 section_start=None,
                 warning=None):
        self.name = name
        self.value = value
        self.description = description
        self.details_label = None
        self.details_hide_label = None
        self.details_content = None
        self.icon = None
        self.warning = warning
        self.type = setting_type
        self.tooltip = tooltip
        self.section_start = section_start

    def comment(self, details_label, details_hide_label, details_description):
        ret = copy.deepcopy(self)
        ret.details_label = details_label
        ret.details_hide_label = details_hide_label
        ret.details_content = details_description
        return ret

    def performance(self, ok):
        ret = copy.deepcopy(self)
        ret.icon = 'happy' if ok else 'sad'
        return ret

    def as_dict(self):
        ret = {}
        for key, value in self.__dict__.iteritems():
            if value is None:
                continue
            ret[key] = value
        return ret


class OverviewSeparator(OverviewSetting):
    def __init__(self):
        super(OverviewSeparator, self).__init__('', '', '', setting_type='hr')


@statsd_timer('dash.infobox_helpers', 'format_flight_time')
def format_flight_time(start_date, end_date):
    start_date_str = start_date.strftime('%m/%d') if start_date else ''
    end_date_str = end_date.strftime('%m/%d') if end_date else 'Ongoing'

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


def create_region_setting(regions):
    preview_regions = regions[:MAX_PREVIEW_REGIONS]
    full_regions = regions

    preview_region = ' ' + ', '.join(preview_regions)
    if len(full_regions) > 1:
        preview_region = ''

    targeting_region_setting = OverviewSetting(
        '',
        'Location:{regions}'.format(regions=preview_region),
    )
    if len(full_regions) > 1:
        targeting_region_setting = targeting_region_setting.comment(
            'Show more',
            'Show less',
            ', '.join(full_regions)
        )
    return targeting_region_setting


@statsd_timer('dash.infobox_helpers', 'get_ideal_campaign_spend')
def get_ideal_campaign_spend(user, campaign, until_date=None):
    at_date = until_date or datetime.datetime.today().date()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    if len(budgets) == 0:
        return Decimal(0)
    all_budget_spends_at_date = [b.get_ideal_budget_spend(at_date) for b in budgets]
    return sum(all_budget_spends_at_date)


@statsd_timer('dash.infobox_helpers', 'get_total_and_media_campaign_spend')
def get_total_and_media_campaign_spend(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    if len(budgets) == 0:
        return Decimal(0), Decimal(0)

    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__in=budgets,
    )
    spend_data = reports.budget_helpers.calculate_spend_data(
        daily_statements,
        date=at_date,
        use_decimal=True
    )
    return spend_data.get('total', Decimal(0)), spend_data.get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'get_media_campaign_spend')
def get_total_media_campaign_budget(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()

    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    ret = Decimal(0)
    for bli in budgets:
        ret += bli.amount * (1 - bli.credit.license_fee)
    return ret


@statsd_timer('dash.infobox_helpers', 'get_media_campaign_spend')
def get_media_campaign_spend(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()

    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__in=budgets,
    )
    return reports.budget_helpers.calculate_spend_data(
        daily_statements,
        date=at_date,
        use_decimal=True
    ).get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'get_yesterday_adgroup_spend')
def get_yesterday_adgroup_spend(user, ad_group):
    yesterday_media_cost = reports.api_contentads.get_actual_yesterday_cost(
        {'ad_group': ad_group.id},
        breakdown=['ad_group']
    )
    return sum(yesterday_media_cost.values())


@statsd_timer('dash.infobox_helpers', 'get_yesterday_campaign_spend')
def get_yesterday_campaign_spend(user, campaign):
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__campaign=campaign,
        date=yesterday,
    )
    return reports.budget_helpers.calculate_spend_data(
        daily_statements,
        use_decimal=True
    ).get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'get_yesterday_all_accounts_spend')
def get_yesterday_all_accounts_spend():
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        date=yesterday
    )
    return reports.budget_helpers.calculate_spend_data(
        daily_statements,
        use_decimal=True
    ).get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'get_mtd_all_accounts_spend')
def get_mtd_all_accounts_spend():
    today = datetime.datetime.utcnow().date()
    daily_statements = reports.models.BudgetDailyStatement.objects.all()
    return reports.budget_helpers.calculate_mtd_spend_data(
        daily_statements,
        date=today,
        use_decimal=True
    ).get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'get_goal_value')
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


@statsd_timer('dash.infobox_helpers', 'get_goal_difference')
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


@statsd_timer('dash.infobox_helpers', 'goals_and_spend_settings')
def goals_and_spend_settings(user, campaign):
    settings = []

    total_campaign_spend_to_date, media_campaign_spend_to_date = get_total_and_media_campaign_spend(user, campaign)
    ideal_campaign_spend_to_date = get_ideal_campaign_spend(user, campaign)
    ratio = 0
    if ideal_campaign_spend_to_date > 0:
        ratio = total_campaign_spend_to_date / ideal_campaign_spend_to_date
    campaign_pacing_settings = OverviewSetting(
        'Campaign pacing:',
        utils.lc_helper.default_currency(media_campaign_spend_to_date),
        description='{:.2f}% on plan'.format(ratio * 100),
    ).performance(total_campaign_spend_to_date >= ideal_campaign_spend_to_date)
    settings.append(campaign_pacing_settings.as_dict())

    is_delivering = ideal_campaign_spend_to_date >= total_campaign_spend_to_date
    return settings, is_delivering


def format_goal_value(goal_value, goal_type):
    if not goal_value:
        return 0
    if goal_type in (dash.constants.CampaignGoal.PERCENT_BOUNCE_RATE,):
        return float(goal_value)
    else:
        return int(goal_value)


@statsd_timer('dash.infobox_helpers', 'calculate_daily_ad_group_cap')
def calculate_daily_ad_group_cap(ad_group):
    """
    Daily media cap
    """
    return _compute_daily_cap([ad_group])


@statsd_timer('dash.infobox_helpers', 'calculate_daily_campaign_cap')
def calculate_daily_campaign_cap(campaign):
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).exclude_archived()
    return _compute_daily_cap(ad_groups)


@statsd_timer('dash.infobox_helpers', 'calculate_daily_account_cap')
def calculate_daily_account_cap(account):
    campaigns = dash.models.Campaign.objects.filter(account=account)
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign__in=campaigns
    ).exclude_archived()
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign__in=campaigns
    ).exclude_archived()
    return _compute_daily_cap(ad_groups)


@statsd_timer('dash.infobox_helpers', 'calculate_available_media_campaign_budget')
def calculate_available_media_campaign_budget(campaign):
    # campaign budget based on non-depleted budget line items
    today = datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], today)

    ret = 0
    for bli in budgets:
        available_total_amount = bli.get_available_amount(today)
        available_media_amount = available_total_amount * (1 - bli.credit.license_fee)
        ret += available_media_amount
    return ret


@statsd_timer('dash.infobox_helpers', 'calculate_available_credit')
def calculate_available_credit(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)

    return sum([credit.effective_amount() * (1 - credit.license_fee) for credit in credits])


@statsd_timer('dash.infobox_helpers', 'calculate_spend_credit')
def calculate_spend_credit(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)
    statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__credit__in=credits
    )
    spend_data = reports.budget_helpers.calculate_spend_data(
        statements,
        date=today,
        use_decimal=True
    )
    return spend_data.get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'calculate_yesterday_account_spend')
def calculate_yesterday_account_spend(account):
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    credits = [c.id for c in _retrieve_active_creditlineitems(account, yesterday)]
    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__credit__in=credits,
        date=yesterday,
    )
    return reports.budget_helpers.calculate_spend_data(
        daily_statements,
        use_decimal=True
    ).get('media', Decimal(0))


@statsd_timer('dash.infobox_helpers', 'create_yesterday_spend_setting')
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
        utils.lc_helper.default_currency(yesterday_cost),
        description=daily_ratio_description,
        tooltip='Yesterday media spend'
    ).performance(
        filled_daily_ratio >= 1.0 if filled_daily_ratio else False
    )
    return yesterday_spend_setting


def create_total_campaign_budget_setting(user, campaign):
    total_media_available = calculate_available_media_campaign_budget(campaign)
    total_media = get_total_media_campaign_budget(user, campaign)

    setting = OverviewSetting(
        'Campaign budget:',
        utils.lc_helper.default_currency(total_media),
        '{} remaining'.format(
            utils.lc_helper.default_currency(total_media_available)
        ),
        tooltip="Campaign media budget"
    )
    return setting


@statsd_timer('dash.infobox_helpers', 'count_active_accounts')
def count_active_accounts():
    account_ids = set(
        dash.models.AdGroupSourceState.objects.all().group_current_states().filter(
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE
        ).values_list(
            'ad_group_source__ad_group__campaign__account',
            flat=True
        )
    )
    return len(account_ids)


@statsd_timer('dash.infobox_helpers', 'calculate_all_accounts_total_budget')
def calculate_all_accounts_total_budget(start_date, end_date):
    '''
    Total budget in date range is amount of all active
    '''
    all_amounts_aggregate = dash.models.BudgetLineItem.objects.all().exclude(
        start_date__gt=end_date
    ).exclude(
        end_date__lt=start_date
    ).aggregate(amount_sum=Sum('amount'))
    return all_amounts_aggregate['amount_sum'] or 0


def calculate_all_accounts_monthly_budget(today):
    start, end = calendar.monthrange(today.year, today.month)
    start_date = datetime.datetime(today.year, today.month, 1)
    end_date = datetime.datetime(today.year, today.month, end)
    return calculate_all_accounts_total_budget(start_date, end_date)


def count_weekly_logged_in_users():
    now = datetime.datetime.utcnow()
    one_week_ago = now - datetime.timedelta(days=7)
    return zemauth.models.User.objects.filter(
        last_login__gte=one_week_ago,
    ).exclude(
        email__contains='@zemanta'
    ).count()


@statsd_timer('dash.infobox_helpers', 'count_weekly_active_users')
def count_weekly_active_users():
    return dash.models.UserActionLog.objects.filter(
        created_dt__gte=_one_week_ago()
    ).exclude(
        created_by__email__contains='@zemanta'
    ).select_related('created_by').distinct('created_by').count()


@statsd_timer('dash.infobox_helpers', 'count_weekly_selfmanaged_actions')
def count_weekly_selfmanaged_actions():
    return dash.models.UserActionLog.objects.filter(
        created_dt__gte=_one_week_ago()
    ).exclude(
        created_by__email__contains='@zemanta'
    ).count()


def _one_week_ago():
    now = datetime.datetime.utcnow()
    return now - datetime.timedelta(days=7)


def _retrieve_active_budgetlineitems(campaign, date):
    if campaign:
        qs = dash.models.BudgetLineItem.objects.filter(
            campaign__in=campaign
        )
    else:
        qs = dash.models.BudgetLineItem.objects.all()
    return qs.filter_active(date)


def is_adgroup_active(ad_group, ad_group_settings=None):
    if not ad_group_settings:
        ad_group_settings = ad_group.get_current_settings()

    ad_group_source_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group=ad_group
    ).group_current_settings()

    running_status = dash.models.AdGroup.get_running_status(ad_group_settings, ad_group_source_settings)
    state = ad_group_settings.state if ad_group_settings else dash.constants.AdGroupSettingsState.INACTIVE

    infobox_status = dash.constants.InfoboxStatus.ACTIVE
    if (running_status == dash.constants.AdGroupRunningStatus.INACTIVE and
            state == dash.constants.AdGroupSettingsState.ACTIVE) or\
            (running_status == dash.constants.AdGroupRunningStatus.ACTIVE and
            state == dash.constants.AdGroupSettingsState.INACTIVE):
        infobox_status = dash.constants.InfoboxStatus.STOPPED
    elif state == dash.constants.AdGroupSettingsState.INACTIVE:
        infobox_status = dash.constants.InfoboxStatus.INACTIVE
    return infobox_status


@statsd_timer('dash.infobox_helpers', 'is_campaign_active')
def is_campaign_active(campaign):
    ad_groups_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__campaign=campaign
    ).group_current_settings()

    for ad_group_settings in ad_groups_settings:
        ad_group = ad_group_settings.ad_group
        if is_adgroup_active(ad_group, ad_group_settings) == dash.constants.InfoboxStatus.ACTIVE:
            return dash.constants.InfoboxStatus.ACTIVE
    return dash.constants.InfoboxStatus.INACTIVE


@statsd_timer('dash.infobox_helpers', 'is_account_active')
def is_account_active(account):
    ad_groups_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__campaign__account=account
    ).group_current_settings()

    for ad_group_settings in ad_groups_settings:
        ad_group = ad_group_settings.ad_group
        if is_adgroup_active(ad_group, ad_group_settings) == dash.constants.InfoboxStatus.ACTIVE:
            return dash.constants.InfoboxStatus.ACTIVE
    return dash.constants.InfoboxStatus.INACTIVE


@statsd_timer('dash.infobox_helpers', '_retrieve_active_creditlineitems')
def _retrieve_active_creditlineitems(account, date):
    return [credit for credit in dash.models.CreditLineItem.objects.filter(
        account=account
    ) if credit.is_active(date)]


@statsd_timer('dash.infobox_helpers', '_compute_daily_cap')
def _compute_daily_cap(ad_groups):
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups
    )
    ad_group_source_states = dash.models.AdGroupSourceState.objects.filter(
        ad_group_source__in=ad_group_sources
    ).group_current_states().values_list('ad_group_source__id', 'state')

    adg_state = dict(ad_group_source_states)

    ad_group_source_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources
    ).group_current_settings().values_list('ad_group_source__id', 'daily_budget_cc')

    adgs_settings = dict(ad_group_source_settings)

    ret = 0
    for adgsid, state in adg_state.iteritems():
        if not state or state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue
        ret += adgs_settings.get(adgsid) or 0
    return ret
