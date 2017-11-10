import copy
import datetime
import influx
import utils.lc_helper

from django.db import models
from django.db.models import Sum, F, ExpressionWrapper
from django.core.cache import caches

import dash.constants
import dash.models
import dash.campaign_goals
import zemauth.models
import redshiftapi.api_breakdowns
import utils.dates_helper
import utils.lc_helper
import utils.cache_helper

from utils import converters

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

    def comment(self, details_label, details_description):
        ret = copy.deepcopy(self)
        ret.details_label = details_label
        ret.details_content = details_description
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

    daily_statements = dash.models.BudgetDailyStatement.objects.filter(
        budget__in=budgets,
        date__lte=at_date,
    )
    spend_data = daily_statements.calculate_spend_data()
    return spend_data.get('etf_total', Decimal(0)), spend_data.get('media', Decimal(0))


def get_total_spend_campaign_budget(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or utils.dates_helper.local_today()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)

    if campaign.account.uses_bcm_v2:
        return sum(x.amount for x in budgets)

    ret = Decimal(0)
    for bli in budgets:
        ret += bli.amount * (1 - bli.credit.license_fee)
    return ret


def get_media_campaign_spend(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or datetime.datetime.utcnow().date()

    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    daily_statements = dash.models.BudgetDailyStatement.objects.filter(
        budget__in=budgets,
        date__lte=at_date,
    )
    return daily_statements.calculate_spend_data().get('media', Decimal(0))


def get_yesterday_adgroup_spend(user, ad_group):
    yesterday = utils.dates_helper.local_yesterday()
    query_results = redshiftapi.api_breakdowns.query_all(
        ['ad_group_id'],
        constraints={
            'date__gte': yesterday,
            'date__lte': yesterday,
            'ad_group_id': [ad_group.id],
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
        metrics=['e_yesterday_cost', 'yesterday_et_cost', 'yesterday_etfm_cost']
    )
    return dict(
        e_yesterday_cost=sum(row['e_yesterday_cost'] for row in query_results),
        yesterday_et_cost=sum(row['yesterday_et_cost'] for row in query_results),
        yesterday_etfm_cost=sum(row['yesterday_etfm_cost'] for row in query_results),
    )


def get_yesterday_campaign_spend(user, campaign):
    yesterday = utils.dates_helper.local_yesterday()
    query_results = redshiftapi.api_breakdowns.query_all(
        ['campaign_id'],
        constraints={
            'date__gte': yesterday,
            'date__lte': yesterday,
            'campaign_id': [campaign.id],
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
        metrics=['e_yesterday_cost', 'yesterday_et_cost', 'yesterday_etfm_cost']
    )
    return dict(
        e_yesterday_cost=sum(row['e_yesterday_cost'] for row in query_results),
        yesterday_et_cost=sum(row['yesterday_et_cost'] for row in query_results),
        yesterday_etfm_cost=sum(row['yesterday_etfm_cost'] for row in query_results),
    )


def get_yesterday_account_spend(account):
    yesterday = utils.dates_helper.local_yesterday()

    credits = [c.id for c in _retrieve_active_creditlineitems(account, yesterday)]
    daily_statements = dash.models.BudgetDailyStatement.objects.filter(
        budget__credit__in=credits,
        budget__campaign__account=account,
        date=yesterday,
    )
    spend_data = daily_statements.calculate_spend_data()
    return dict(
        e_yesterday_cost=spend_data.get('et_total', Decimal(0)),
        yesterday_et_cost=spend_data.get('et_total', Decimal(0)),
        yesterday_etfm_cost=spend_data.get('etfm_total', Decimal(0)),
    )


def get_yesterday_all_accounts_spend(filtered_agencies, filtered_account_types):
    yesterday = utils.dates_helper.local_yesterday()

    daily_statements = dash.models.BudgetDailyStatement.objects.filter(
        date=yesterday
    )
    daily_statements = _filter_daily_statements(
        daily_statements,
        filtered_agencies,
        filtered_account_types
    )
    spend_data = daily_statements.calculate_spend_data()
    return dict(
        e_yesterday_cost=spend_data.get('et_total', Decimal(0)),
        yesterday_et_cost=spend_data.get('et_total', Decimal(0)),
        yesterday_etfm_cost=spend_data.get('etfm_total', Decimal(0)),
    )


def get_yesterday_agency_spend(accounts):
    yesterday = utils.dates_helper.local_yesterday()

    daily_statements = dash.models.BudgetDailyStatement.objects.filter(
        date=yesterday,
        budget__campaign__account__in=accounts
    )

    spend_data = daily_statements.calculate_spend_data()
    return dict(
        e_yesterday_cost=spend_data.get('et_total', Decimal(0)),
        yesterday_et_cost=spend_data.get('et_total', Decimal(0)),
        yesterday_etfm_cost=spend_data.get('etfm_total', Decimal(0)),
    )


def get_mtd_all_accounts_spend(filtered_agencies, filtered_account_types):
    start_date = utils.dates_helper.local_today().replace(day=1)

    daily_statements = dash.models.BudgetDailyStatement.objects.all().filter(date__gte=start_date)
    daily_statements = _filter_daily_statements(
        daily_statements,
        filtered_agencies,
        filtered_account_types
    )
    return dict(
        e_media_cost=daily_statements.calculate_spend_data().get('media', Decimal(0)),
        et_cost=daily_statements.calculate_spend_data().get('et_total', Decimal(0)),
        etfm_cost=daily_statements.calculate_spend_data().get('etfm_total', Decimal(0)),
    )


def get_mtd_agency_spend(accounts):
    start_date = utils.dates_helper.local_today().replace(day=1)

    daily_statements = dash.models.BudgetDailyStatement.objects.filter(
        budget__campaign__account__in=accounts
    ).filter(date__gte=start_date)

    return dict(
        e_media_cost=daily_statements.calculate_spend_data().get('media', Decimal(0)),
        et_cost=daily_statements.calculate_spend_data().get('et_total', Decimal(0)),
        etfm_cost=daily_statements.calculate_spend_data().get('etfm_total', Decimal(0)),
    )


def _filter_daily_statements(statements, filtered_agencies, filtered_account_types):
    if filtered_agencies:
        statements = statements.filter(
            budget__campaign__account__agency__in=filtered_agencies
        )
    if filtered_account_types:
        acs_ids = dash.models.AccountSettings.objects.all()\
            .filter(account__campaign__budgets__statements__in=statements)\
            .group_current_settings()\
            .values_list('id', flat=True)
        filtered_ac_ids = dash.models.AccountSettings.objects.all()\
            .filter(id__in=acs_ids)\
            .filter(account_type__in=filtered_account_types)\
            .values_list('account__id', flat=True)
        statements = statements.filter(
            budget__campaign__account__id__in=filtered_ac_ids)
    return statements


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


def calculate_available_campaign_budget(campaign):
    # campaign budget based on non-depleted budget line items
    today = datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], today)

    if campaign.account.uses_bcm_v2:
        return sum(x.get_available_etfm_amount(today) for x in budgets)

    ret = 0
    for bli in budgets:
        available_total_amount = bli.get_available_amount(today)
        available_amount = available_total_amount * (1 - bli.credit.license_fee)
        ret += available_amount
    return ret


def calculate_allocated_and_available_credit(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)
    credit_total = credits.aggregate(
        amount_sum=Sum('amount'),
        flat_fee_sum=converters.CC_TO_DECIMAL_DOLAR * Sum('flat_fee_cc'))
    budget_total = dash.models.BudgetLineItem.objects.filter(
        credit__in=credits
    ).aggregate(
        amount_sum=Sum('amount'),
        freed_sum=converters.CC_TO_DECIMAL_DOLAR * Sum('freed_cc')
    )
    assigned = (credit_total['amount_sum'] or 0) - (credit_total['flat_fee_sum'] or 0)
    allocated = (budget_total['amount_sum'] or 0) - (budget_total['freed_sum'] or 0)

    return allocated, (assigned or 0) - allocated


def calculate_spend_and_available_budget(account):
    today = datetime.datetime.utcnow().date()
    credits = _retrieve_active_creditlineitems(account, today)
    account_budgets = _retrieve_active_budgetlineitems(account.campaign_set.all(), today)

    statements = dash.models.BudgetDailyStatement.objects.filter(
        budget__credit__in=credits,
        budget__in=account_budgets,
        date__lte=today,
    )
    spend_data = statements.calculate_spend_data()

    remaining_media = account_budgets.aggregate(
        amount_sum=ExpressionWrapper(
            Sum(F('amount') * (1.0 - F('credit__license_fee'))),
            output_field=models.DecimalField()
        )
    )
    return spend_data.get('media', Decimal(0)),\
        (remaining_media['amount_sum'] or 0) - (spend_data.get('media', Decimal(0) or 0))


def create_yesterday_spend_setting(yesterday_costs, daily_budget, uses_bcm_v2=False):
    yesterday_cost = yesterday_costs['yesterday_etfm_cost'] if uses_bcm_v2 else yesterday_costs['e_yesterday_cost']

    filled_daily_ratio = None
    if daily_budget > 0:
        filled_daily_ratio = float(yesterday_cost or 0) / float(daily_budget)

    if filled_daily_ratio:
        daily_ratio_description = '{:.2f}% of {} Daily Spend Cap'.format(
            abs(filled_daily_ratio) * 100,
            utils.lc_helper.default_currency(daily_budget)
        )
    else:
        daily_ratio_description = 'N/A'

    yesterday_spend_setting = OverviewSetting(
        'Yesterday spend:',
        utils.lc_helper.default_currency(yesterday_cost),
        description=daily_ratio_description,
        tooltip='Yesterday spend' if uses_bcm_v2 else 'Yesterday media spend'
    )
    return yesterday_spend_setting


def create_total_campaign_budget_setting(user, campaign):
    total_spend = get_total_spend_campaign_budget(user, campaign)
    total_spend_available = calculate_available_campaign_budget(campaign)

    setting = OverviewSetting(
        'Campaign budget:',
        utils.lc_helper.default_currency(total_spend),
        '{} remaining'.format(
            utils.lc_helper.default_currency(total_spend_available)
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


def count_active_agency_accounts(user):
    return dash.models.Account.objects.all().filter_by_user(user).filter(
        id__in=set(
            dash.models.AdGroup.objects.all()
            .filter_running()
            .values_list(
                'campaign__account',
                flat=True
            )
        )
    ).count()


def count_active_accounts(filtered_agencies, filtered_account_types):
    account_ids = set(
        dash.models.AdGroup.objects.all()
        .filter_running()
        .values_list(
            'campaign__account',
            flat=True
        )
    )
    count_filtered_ids = dash.models.Account.objects.all()\
        .filter(id__in=account_ids)\
        .filter_by_agencies(filtered_agencies)\
        .filter_by_account_types(filtered_account_types)\
        .count()
    return count_filtered_ids


def format_username(user):
    if not user:
        return 'N/A'
    return user.get_full_name()


def _filter_user_by_account_type(users, filtered_account_types):
    if not filtered_account_types:
        return users
    latest_account_settings = dash.models.AccountSettings.objects.all()\
        .filter(
            models.Q(account__users__in=users) |
            models.Q(account__agency__users__in=users)
    )\
        .group_current_settings()

    filtered_latest_account_settings = dash.models.AccountSettings.objects\
        .filter(pk__in=latest_account_settings)\
        .filter(account_type__in=filtered_account_types)\
        .values_list('account_id', flat=True)

    return users.filter(
        models.Q(account__id__in=filtered_latest_account_settings) |
        models.Q(groups__permissions__codename='can_see_all_accounts') |
        models.Q(user_permissions__codename='can_see_all_accounts')
    )


def count_weekly_logged_in_users(filtered_agencies, filtered_account_types):
    logged_in_users = zemauth.models.User.objects.filter(
        last_login__gte=_one_week_ago(),
        last_login__lte=_until_today())\
        .filter_selfmanaged()\
        .filter_by_agencies(filtered_agencies)
    return _filter_user_by_account_type(
        logged_in_users,
        filtered_account_types).count()


def get_weekly_active_users(filtered_agencies, filtered_account_types):
    # NOTE: data returned by this function might be a bit old, because cache is invalidated after
    # a certain time and not when data actually changes. This behaviour is by design - currently
    # it is ok if this data is a bit dated - confirmed by product

    cache = caches['dash_db_cache']
    cache_key = _filtered_agencies_account_types_cache_key(
        'active_users_ids', filtered_agencies, filtered_account_types)
    active_users_ids = cache.get(cache_key, None)
    if active_users_ids is not None:
        influx.incr('infobox.cache', 1, method='get_weekly_active_users', outcome='hit')
        return zemauth.models.User.objects.filter(pk__in=active_users_ids)

    influx.incr('infobox.cache', 1, method='get_weekly_active_users', outcome='miss')
    actions = dash.models.History.objects\
        .filter(
            created_dt__gte=_one_week_ago(),
            created_dt__lte=_until_today())\
        .filter_selfmanaged().distinct('created_by_id')

    users = zemauth.models.User.objects.all().filter(
        pk__in=actions.values_list('created_by_id', flat=True)
    ).filter_by_agencies(filtered_agencies)

    users = _filter_user_by_account_type(
        users,
        filtered_account_types)
    cache.set(cache_key, [x.pk for x in users])
    return users


def count_weekly_selfmanaged_actions(filtered_agencies, filtered_account_types):
    # NOTE: data returned by this function might be a bit old, because cache is invalidated after
    # a certain time and not when data actually changes. This behaviour is by design - currently
    # it is ok if this data is a bit dated - confirmed by product

    # cache = caches['dash_db_cache']
    # cache_key = _filtered_agencies_account_types_cache_key(
    #     'selfmanaged_actions', filtered_agencies, filtered_account_types)
    # count = cache.get(cache_key, None)

    # if count is not None:
    #     influx.incr('infobox.cache', 1, method='count_weekly_selfmanaged_actions', outcome='hit')
    #     return count

    # influx.incr('infobox.cache', 1, method='count_weekly_selfmanaged_actions', outcome='miss')
    # actions = dash.models.History.objects\
    #     .filter(
    #         created_dt__gte=_one_week_ago(),
    #         created_dt__lte=_until_today())\
    #     .filter_selfmanaged()

    # users = zemauth.models.User.objects.all().filter(
    #     pk__in=actions.values_list('created_by_id', flat=True))\
    #     .filter_by_agencies(filtered_agencies)
    # filtered_users = _filter_user_by_account_type(users, filtered_account_types)

    # count = actions.filter(created_by__in=filtered_users).count()
    # cache.set(cache_key, count)

    # return count
    return 0


def _filtered_agencies_account_types_cache_key(name, filtered_agencies, filtered_account_types):
    key = "{}__{}".format(
        sorted(filtered_agencies.values_list('pk', flat=True)) if filtered_agencies is not None else '',
        sorted(filtered_account_types) if filtered_account_types is not None else ''
    )
    return utils.cache_helper.get_cache_key(name, key)


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


def get_adgroup_running_status(user, ad_group_settings, filtered_sources=None):
    state = ad_group_settings.state if ad_group_settings else dash.constants.AdGroupSettingsState.INACTIVE
    autopilot_state = (ad_group_settings.autopilot_state if ad_group_settings
                       else dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
    running_status = dash.models.AdGroup.get_running_status(ad_group_settings)

    return get_adgroup_running_status_class(
        user,
        autopilot_state,
        running_status,
        state,
        ad_group_settings.landing_mode
    )


def get_adgroup_running_status_class(user, autopilot_state, running_status, state, is_in_landing):
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

    if autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return dash.constants.InfoboxStatus.AUTOPILOT
    elif autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC:
        return dash.constants.InfoboxStatus.ACTIVE_PRICE_DISCOVERY

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


def get_entity_delivery_text(status):
    if status == dash.constants.InfoboxStatus.ACTIVE:
        return 'Active'
    if status == dash.constants.InfoboxStatus.AUTOPILOT:
        return 'Active - Autopilot mode'
    if status == dash.constants.InfoboxStatus.LANDING_MODE:
        return 'Active - Landing mode'
    if status == dash.constants.InfoboxStatus.ACTIVE_PRICE_DISCOVERY:
        return 'Active - Price Discovery'
    if status == dash.constants.InfoboxStatus.STOPPED:
        return 'Paused'
    if status == dash.constants.InfoboxStatus.INACTIVE:
        return 'Inactive'


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
    ad_group_source_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group__in=ad_groups
    ).group_current_settings().values(
        'ad_group_source__source_id',
        'ad_group_source__ad_group_id',
        'daily_budget_cc',
        'state',
        'ad_group_source__source__source_type__type'
    )

    ad_group_settings = {
        ags.ad_group_id: ags for ags in
        dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_groups).group_current_settings()
    }

    ret = 0

    ad_groups_with_active_b1_sources = set()
    for agss in ad_group_source_settings:
        if agss['state'] != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue

        ags = ad_group_settings[agss['ad_group_source__ad_group_id']]

        if ags.state != dash.constants.AdGroupSettingsState.ACTIVE:
            continue

        if ags.b1_sources_group_enabled and\
           agss['ad_group_source__source__source_type__type'] == dash.constants.SourceType.B1:
            ad_groups_with_active_b1_sources.add(ags.ad_group_id)
            continue

        ret += agss['daily_budget_cc'] or 0

    for ad_group_id in ad_groups_with_active_b1_sources:
        ags = ad_group_settings[ad_group_id]
        if ags.state != dash.constants.AdGroupSettingsState.ACTIVE:
            continue

        if not ags.b1_sources_group_enabled:
            continue

        if ags.b1_sources_group_state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue

        ret += ags.b1_sources_group_daily_budget

    return ret


def get_primary_campaign_goal(user, campaign, start_date, end_date):
    primary_goal = dash.campaign_goals.fetch_goals([campaign.pk], end_date).first()
    if primary_goal is None or not primary_goal.primary:
        return []

    performance = dash.campaign_goals.get_goals_performance_campaign(
        user, campaign, start_date, end_date)
    return _get_primary_campaign_goal(user, campaign, performance)


def get_primary_campaign_goal_ad_group(user, ad_group, start_date, end_date):
    primary_goal = dash.campaign_goals.fetch_goals([ad_group.campaign_id], end_date).first()
    if primary_goal is None or not primary_goal.primary:
        return []

    performance = dash.campaign_goals.get_goals_performance_ad_group(
        user, ad_group, start_date, end_date)
    return _get_primary_campaign_goal(user, ad_group.campaign, performance)


def _get_primary_campaign_goal(user, campaign, performance):
    settings = []

    permissions = user.get_all_permissions_with_access_levels()

    status, metric_value, planned_value, campaign_goal = performance[0]
    goal_description = dash.campaign_goals.format_campaign_goal(
        campaign_goal.type,
        metric_value,
        campaign_goal.conversion_goal
    )

    primary_campaign_goal_setting = OverviewSetting(
        'Primary Goal:',
        goal_description,
        planned_value and 'planned {}'.format(
            dash.campaign_goals.format_value(campaign_goal.type, planned_value),
        ) or None,
        section_start=True,
        internal=not permissions.get('zemauth.campaign_goal_performance'),
    )

    primary_campaign_goal_setting.icon = dash.campaign_goals.STATUS_TO_EMOTICON_MAP[status]
    settings.append(primary_campaign_goal_setting.as_dict())

    return settings
