import copy
import datetime
import utils.lc_helper

import reports.api_helpers
from django.db import models
from django.db.models import Sum, F, ExpressionWrapper

import dash.constants
import dash.models
import dash.campaign_goals
import zemauth.models
import reports.api_contentads
import reports.models
import utils.dates_helper
import utils.lc_helper

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
                 internal=False,
                 warning=None):
        self.name = name
        self.value = value
        self.description = description
        self.details_label = None
        self.details_hide_label = None
        self.details_content = None
        self.icon = None
        self.internal = internal
        self.warning = warning
        self.type = setting_type
        self.tooltip = tooltip
        self.section_start = section_start
        self.value_class = None

    def comment(self, details_label, details_hide_label, details_description):
        ret = copy.deepcopy(self)
        ret.details_label = details_label
        ret.details_hide_label = details_hide_label
        ret.details_content = details_description
        return ret

    def performance(self, ok):
        ret = copy.deepcopy(self)
        if ok is None:
            ret.icon = dash.constants.Emoticon.NEUTRAL
        else:
            ret.icon = dash.constants.Emoticon.HAPPY if ok else dash.constants.Emoticon.SAD
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


def get_ideal_campaign_spend(user, campaign, until_date=None):
    at_date = until_date or datetime.datetime.today().date()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
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

    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__in=budgets,
    )
    spend_data = reports.budget_helpers.calculate_spend_data(
        daily_statements,
        date=at_date,
        use_decimal=True
    )
    return spend_data.get('total', Decimal(0)), spend_data.get('media', Decimal(0))


def get_total_media_campaign_budget(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()

    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    ret = Decimal(0)
    for bli in budgets:
        ret += bli.amount * (1 - bli.credit.license_fee)
    return ret


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


def get_yesterday_adgroup_spend(user, ad_group):
    yesterday_media_cost = reports.api_contentads.get_actual_yesterday_cost(
        {'ad_group': ad_group.id},
        breakdown=['ad_group']
    )
    return sum(yesterday_media_cost.values())


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


def get_yesterday_all_accounts_spend():
    yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
    daily_statements = reports.models.BudgetDailyStatement.objects.filter(
        date=yesterday
    )
    return reports.budget_helpers.calculate_spend_data(
        daily_statements,
        use_decimal=True
    ).get('media', Decimal(0))


def get_mtd_all_accounts_spend():
    daily_statements = reports.models.BudgetDailyStatement.objects.all()
    return reports.budget_helpers.calculate_mtd_spend_data(
        daily_statements,
        date=_until_today(),
        use_decimal=True
    ).get('media', Decimal(0))


def calculate_daily_ad_group_cap(ad_group):
    """
    Daily media cap
    """
    return _compute_daily_cap([ad_group])


def calculate_daily_campaign_cap(campaign):
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).exclude_archived()
    return _compute_daily_cap(ad_groups)


def calculate_daily_account_cap(account):
    ad_groups = dash.models.AdGroup.objects.filter(
        campaign__account=account
    ).exclude_archived()
    return _compute_daily_cap(ad_groups)


def calculate_available_media_account_budget(account):
    # campaign budget based on non-depleted budget line items
    today = datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems(account.campaign_set.all(), today)

    ret = 0
    for bli in budgets:
        available_total_amount = bli.get_available_amount(today)
        available_media_amount = available_total_amount * (1 - bli.credit.license_fee)
        ret += available_media_amount
    return ret


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


def calculate_allocated_and_available_credit(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)
    credit_total = credits.aggregate(amount_sum=Sum('amount'))
    budget_total = dash.models.BudgetLineItem.objects.filter(
        credit__in=credits
    ).aggregate(
        amount_sum=Sum('amount'),
        freed_sum=dash.models.CC_TO_DEC_MULTIPLIER * Sum('freed_cc')
    )
    allocated = (budget_total['amount_sum'] or 0) - (budget_total['freed_sum'] or 0)
    return allocated, \
        (credit_total['amount_sum'] or 0) - allocated


def calculate_spend_and_available_budget(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)
    account_budgets = _retrieve_active_budgetlineitems(account.campaign_set.all(), today)

    statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__credit__in=credits,
        budget__in=account_budgets
    )
    spend_data = reports.budget_helpers.calculate_spend_data(
        statements,
        date=today,
        use_decimal=True
    )

    remaining_media = account_budgets.aggregate(
        amount_sum=ExpressionWrapper(
            Sum(F('amount') * (1.0 - F('credit__license_fee'))),
            output_field=models.DecimalField()
        )
    )
    return spend_data.get('media', Decimal(0)),\
        (remaining_media['amount_sum'] or 0) - (spend_data.get('media', Decimal(0) or 0))


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


def create_yesterday_spend_setting(yesterday_cost, daily_budget):
    filled_daily_ratio = None
    if daily_budget > 0:
        filled_daily_ratio = float(yesterday_cost or 0) / float(daily_budget)

    if filled_daily_ratio:
        daily_ratio_description = '{:.2f}% of daily budget'.format(abs(filled_daily_ratio) * 100)
    else:
        daily_ratio_description = 'N/A'

    yesterday_spend_setting = OverviewSetting(
        'Yesterday spend:',
        utils.lc_helper.default_currency(yesterday_cost),
        description=daily_ratio_description,
        tooltip='Yesterday media spend'
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


def count_active_adgroups(campaign):
    return dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).filter_running().count()


def count_active_campaigns(account):
    active_campaign_ids = set(dash.models.AdGroup.objects.filter(
        campaign__account=account
    ).filter_running().values_list(
        'campaign',
        flat=True
    ))
    return len(active_campaign_ids)


def count_active_accounts():
    account_ids = set(
        dash.models.AdGroup.objects.all()
        .filter_running()
        .values_list(
            'campaign__account',
            flat=True
        )
    )
    return len(account_ids)


def format_username(user):
    if not user:
        return 'N/A'
    return user.get_full_name()


def count_weekly_logged_in_users():
    return zemauth.models.User.objects.filter(
        last_login__gte=_one_week_ago(),
        last_login__lte=_until_today(),
    ).exclude(
        email__contains='@zemanta'
    ).exclude(
        is_test_user=True
    ).count()


def get_weekly_active_users():
    return [action.created_by for action in dash.models.UserActionLog.objects.filter(
        created_dt__gte=_one_week_ago(),
        created_dt__lte=_until_today(),
    ).exclude(
        created_by__email__contains='@zemanta'
    ).exclude(
        created_by__is_test_user=True
    ).select_related('created_by').distinct('created_by')]


def count_weekly_selfmanaged_actions():
    return dash.models.UserActionLog.objects.filter(
        created_dt__gte=_one_week_ago(),
        created_dt__lte=_until_today(),
    ).exclude(
        created_by__email__contains='@zemanta'
    ).exclude(
        created_by__is_test_user=True
    ).count()


def _one_week_ago():
    now = utils.dates_helper.local_midnight_to_utc_time()
    return now - datetime.timedelta(days=7)


def _until_today():
    return utils.dates_helper.local_midnight_to_utc_time()


def _retrieve_active_budgetlineitems(campaign, date):
    if not campaign:
        return dash.models.BudgetLineItem.objects.none()

    qs = dash.models.BudgetLineItem.objects.filter(
        campaign__in=campaign
    )

    return qs.filter_active(date)


def get_adgroup_running_status(ad_group_settings, filtered_sources=None):
    state = ad_group_settings.state if ad_group_settings else dash.constants.AdGroupSettingsState.INACTIVE
    autopilot_state = (ad_group_settings.autopilot_state if ad_group_settings
                       else dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
    ad_groups_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group=ad_group_settings.ad_group).group_current_settings().\
        filter_by_sources(filtered_sources)
    running_status = dash.models.AdGroup.get_running_status(ad_group_settings, ad_groups_sources_settings)

    return get_adgroup_running_status_class(autopilot_state, running_status, state,
                                            ad_group_settings.landing_mode)


def get_adgroup_running_status_class(autopilot_state, running_status, state, is_in_landing):
    if is_in_landing:
        return dash.constants.InfoboxStatus.LANDING_MODE

    if state == dash.constants.AdGroupSettingsState.INACTIVE and\
       running_status == dash.constants.AdGroupRunningStatus.INACTIVE:
        return dash.constants.InfoboxStatus.STOPPED

    if (running_status == dash.constants.AdGroupRunningStatus.INACTIVE and
            state == dash.constants.AdGroupSettingsState.ACTIVE) or\
            (running_status == dash.constants.AdGroupRunningStatus.ACTIVE and
             state == dash.constants.AdGroupSettingsState.INACTIVE):
        return dash.constants.InfoboxStatus.INACTIVE

    if autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET or\
            autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
        return dash.constants.InfoboxStatus.AUTOPILOT

    return dash.constants.InfoboxStatus.ACTIVE


def get_campaign_running_status(campaign, campaign_settings):
    if campaign_settings.landing_mode:
        return dash.constants.InfoboxStatus.LANDING_MODE

    running_exists = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).filter_running().exists()
    if running_exists:
        return dash.constants.InfoboxStatus.ACTIVE

    active_exists = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).filter_active().exists()
    return dash.constants.InfoboxStatus.INACTIVE if active_exists else dash.constants.InfoboxStatus.STOPPED


def get_account_running_status(account):
    running_exists = dash.models.AdGroup.objects.filter(
        campaign__account=account
    ).filter_running().exists()
    if running_exists:
        return dash.constants.InfoboxStatus.ACTIVE

    active_exists = dash.models.AdGroup.objects.filter(
        campaign__account=account
    ).filter_active().exists()
    return dash.constants.InfoboxStatus.INACTIVE if active_exists else dash.constants.InfoboxStatus.STOPPED


def _retrieve_active_creditlineitems(account, date):
    ret = dash.models.CreditLineItem.objects.filter(
        account=account
    )
    if account.agency is not None:
        ret |= dash.models.CreditLineItem.objects.filter(
            agency=account.agency
        )
    return ret.filter_active()


def _compute_daily_cap(ad_groups):
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups
    )

    ad_group_source_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources
    ).group_current_settings().values_list('ad_group_source__id', 'daily_budget_cc')

    adgs_settings = dict(ad_group_source_settings)

    ad_group_source_states = dash.models.AdGroupSourceState.objects.filter(
        ad_group_source__in=ad_group_sources
    ).group_current_states()

    ret = 0
    for adgs_state in ad_group_source_states:
        if not adgs_state.state or adgs_state.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue
        ret += adgs_settings.get(adgs_state.ad_group_source_id) or adgs_state.daily_budget_cc or 0

    return ret


def get_campaign_goal_list(user, constraints, start_date, end_date):
    performance = dash.campaign_goals.get_goals_performance(user, constraints, start_date, end_date)

    settings = []
    first = True
    permissions = user.get_all_permissions_with_access_levels()
    for status, metric_value, planned_value, campaign_goal in performance:
        goal_description = dash.campaign_goals.format_campaign_goal(
            campaign_goal.type,
            metric_value,
            campaign_goal.conversion_goal
        )

        entry = OverviewSetting(
            '' if not first else 'Goals:',
            goal_description,
            planned_value and 'planned {}'.format(
                dash.campaign_goals.format_value(campaign_goal.type, planned_value),
            ) or None,
            section_start=first,
            internal=first and not permissions.get('zemauth.campaign_goal_performance'),
        )
        if campaign_goal.primary:
            entry.value_class = 'primary'

        entry.icon = dash.campaign_goals.STATUS_TO_EMOTICON_MAP[status]
        settings.append(entry.as_dict())
        first = False
    return settings
