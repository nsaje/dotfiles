import copy
import datetime

from django.db import models
from django.db.models import Sum
from django.core.cache import caches

import automation.campaignstop
import core.multicurrency

import dash.constants
import dash.models
import dash.campaign_goals

import redshiftapi.api_breakdowns

import utils.dates_helper
import utils.lc_helper
import utils.cache_helper

import zemauth.models

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
        for key, value in self.__dict__.items():
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


def get_total_campaign_budgets_amount(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or utils.dates_helper.local_today()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)

    if campaign.account.uses_bcm_v2:
        return sum(x.amount for x in budgets)

    ret = Decimal(0)
    for bli in budgets:
        ret += bli.amount * (1 - bli.credit.license_fee)
    return ret


def get_yesterday_adgroup_spend(user, ad_group, use_local_currency):
    constraints = {
        'ad_group_id': [ad_group.id]
    }
    return _get_yesterday_spend('ad_group_id', constraints, use_local_currency)


def get_yesterday_campaign_spend(user, campaign, use_local_currency):
    constraints = {
        'campaign_id': [campaign.id]
    }
    return _get_yesterday_spend('campaign_id', constraints, use_local_currency)


def get_yesterday_account_spend(account, use_local_currency):
    constraints = {
        'account_id': [account.id]
    }
    return _get_yesterday_spend('account_id', constraints, use_local_currency)


def get_yesterday_accounts_spend(accounts, use_local_currency):
    constraints = {
        'account_id': [account.id for account in accounts]
    }
    return _get_yesterday_spend('account_id', constraints, use_local_currency)


def _get_yesterday_spend(breakdown, constraints, use_local_currency):
    yesterday = utils.dates_helper.local_yesterday()
    constraints.update({
        'date__gte': yesterday,
        'date__lte': yesterday,
    })
    query_results = redshiftapi.api_breakdowns.query_with_background_cache(
        [breakdown],
        constraints,
        parents=None,
        goals=None,
        use_publishers_view=False,
        metrics=[
            'e_yesterday_cost',
            'yesterday_et_cost',
            'yesterday_etfm_cost',
            'local_e_yesterday_cost',
            'local_yesterday_et_cost',
            'local_yesterday_etfm_cost',
        ]
    )

    ret = {
        'e_yesterday_cost': 0,
        'yesterday_et_cost': 0,
        'yesterday_etfm_cost': 0,
    }
    for row in query_results:
        if use_local_currency:
            ret['e_yesterday_cost'] += row['local_e_yesterday_cost']
            ret['yesterday_et_cost'] += row['local_yesterday_et_cost']
            ret['yesterday_etfm_cost'] += row['local_yesterday_etfm_cost']
        else:
            ret['e_yesterday_cost'] += row['e_yesterday_cost']
            ret['yesterday_et_cost'] += row['yesterday_et_cost']
            ret['yesterday_etfm_cost'] += row['yesterday_etfm_cost']
    return ret


def get_mtd_accounts_spend(accounts, use_local_currency):
    constraints = {
        'account_id': [account.id for account in accounts]
    }
    return _get_mtd_spend('account_id', constraints, use_local_currency)


def _get_mtd_spend(breakdown, constraints, use_local_currency):
    start_date = utils.dates_helper.local_today().replace(day=1)
    constraints.update({
        'date__gte': start_date,
    })
    query_results = redshiftapi.api_breakdowns.query_with_background_cache(
        [breakdown],
        constraints,
        parents=None,
        goals=None,
        use_publishers_view=False,
        metrics=[
            'e_media_cost',
            'et_cost',
            'etfm_cost',
            'local_e_media_cost',
            'local_et_cost',
            'local_etfm_cost',
        ]
    )

    ret = {
        'e_media_cost': 0,
        'et_cost': 0,
        'etfm_cost': 0,
    }
    for row in query_results:
        if use_local_currency:
            ret['e_media_cost'] += row['local_e_media_cost']
            ret['et_cost'] += row['local_et_cost']
            ret['etfm_cost'] += row['local_etfm_cost']
        else:
            ret['e_media_cost'] += row['e_media_cost']
            ret['et_cost'] += row['et_cost']
            ret['etfm_cost'] += row['etfm_cost']
    return ret


def calculate_daily_ad_group_cap(ad_group, use_local_currency):
    """
    Daily media cap
    """
    return _compute_daily_cap(use_local_currency, id=ad_group.id)


def calculate_daily_campaign_cap(campaign, use_local_currency):
    return _compute_daily_cap(use_local_currency, campaign_id=campaign.id)


def calculate_daily_account_cap(account, use_local_currency):
    return _compute_daily_cap(use_local_currency, campaign__account_id=account.id)


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


def calculate_available_campaign_budget(campaign, use_local_currency):
    # campaign budget based on non-depleted budget line items
    today = datetime.datetime.utcnow().date()
    budgets = _retrieve_active_budgetlineitems([campaign], today)

    if campaign.account.uses_bcm_v2:
        if use_local_currency:
            return sum(x.get_local_available_etfm_amount(today) for x in budgets)
        else:
            return sum(x.get_available_etfm_amount(today) for x in budgets)

    ret = 0
    for bli in budgets:
        if use_local_currency:
            available_total_amount = bli.get_local_available_amount(today)
        else:
            available_total_amount = bli.get_available_amount(today)
        available_amount = available_total_amount * (1 - bli.credit.license_fee)
        ret += available_amount
    return ret


def calculate_allocated_and_available_credit(account, use_local_currency):
    credits = _retrieve_active_creditlineitems(account, use_local_currency=use_local_currency)
    credit_total = credits.aggregate(
        amount_sum=Sum('amount'),
        flat_fee_sum=converters.CC_TO_DECIMAL_CURRENCY * Sum('flat_fee_cc'))
    budget_total = dash.models.BudgetLineItem.objects.filter(
        credit__in=credits
    ).aggregate(
        amount_sum=Sum('amount'),
        freed_sum=converters.CC_TO_DECIMAL_CURRENCY * Sum('freed_cc')
    )
    assigned = (credit_total['amount_sum'] or 0) - (credit_total['flat_fee_sum'] or 0)
    allocated = (budget_total['amount_sum'] or 0) - (budget_total['freed_sum'] or 0)

    return allocated, (assigned or 0) - allocated


def create_yesterday_spend_setting(yesterday_costs, daily_budget, currency, uses_bcm_v2=False):
    yesterday_cost = yesterday_costs['yesterday_etfm_cost'] if uses_bcm_v2 else yesterday_costs['e_yesterday_cost']
    currency_symbol = core.multicurrency.get_currency_symbol(currency)

    filled_daily_ratio = None
    if daily_budget > 0:
        filled_daily_ratio = float(yesterday_cost or 0) / float(daily_budget)

    if filled_daily_ratio:
        daily_ratio_description = '{:.2f}% of {} Daily Spend Cap'.format(
            abs(filled_daily_ratio) * 100,
            utils.lc_helper.format_currency(daily_budget, curr=currency_symbol)
        )
    else:
        daily_ratio_description = 'N/A'

    yesterday_spend_setting = OverviewSetting(
        'Yesterday spend:',
        utils.lc_helper.format_currency(yesterday_cost, curr=currency_symbol),
        description=daily_ratio_description,
        tooltip='Yesterday spend' if uses_bcm_v2 else 'Yesterday media spend'
    )
    return yesterday_spend_setting


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
    return (
        dash.models.AdGroup.objects.all()
        .filter_running()
        .filter_by_user(user)
        .order_by()  # disable default adgroup order
        .values('campaign__account')
        .distinct()
        .count()
    )


def _active_account_ids():
    cache = caches['dash_db_cache']
    cache_key = 'active_account_ids'
    active_account_ids = cache.get(cache_key, None)
    if active_account_ids is not None:
        return active_account_ids

    active_account_ids = set(
        dash.models.AdGroup.objects.all()
        .filter_running()
        .order_by()  # disable default adgroup order
        .values_list(
            'campaign__account',
            flat=True
        ).distinct()
    )

    cache.set(cache_key, active_account_ids)
    return active_account_ids


def count_active_accounts(filtered_agencies, filtered_account_types):
    count_filtered_ids = dash.models.Account.objects.all()\
        .filter(id__in=_active_account_ids())\
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


def _active_user_ids():
    cache = caches['dash_db_cache']
    cache_key = 'active_user_ids'
    active_user_ids = cache.get(cache_key, None)
    if active_user_ids is not None:
        return active_user_ids

    active_user_ids = set(
        dash.models.History.objects.all()
        .filter(
            created_dt__gte=_one_week_ago(),
            created_dt__lte=_until_today(),
        )
        .filter_selfmanaged()
        .values_list('created_by_id', flat=True)
        .distinct()
    )

    cache.set(cache_key, active_user_ids)
    return active_user_ids


def get_weekly_active_users(filtered_agencies, filtered_account_types):
    # NOTE: data returned by this function might be a bit old, because cache is invalidated after
    # a certain time and not when data actually changes. This behaviour is by design - currently
    # it is ok if this data is a bit dated - confirmed by product

    users = zemauth.models.User.objects.all().filter(
        pk__in=_active_user_ids()
    ).filter_by_agencies(filtered_agencies)

    users = _filter_user_by_account_type(
        users,
        filtered_account_types)
    return users


def count_weekly_selfmanaged_actions(filtered_agencies, filtered_account_types):
    # NOTE: data returned by this function might be a bit old, because cache is invalidated after
    # a certain time and not when data actually changes. This behaviour is by design - currently
    # it is ok if this data is a bit dated - confirmed by product

    # cache = caches['dash_db_cache']
    # cache_key = utils.cache_helper.get_cache_key(
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


def get_adgroup_running_status(user, ad_group, filtered_sources=None):
    running_status = dash.models.AdGroup.get_running_status(ad_group.settings)

    return get_adgroup_running_status_class(
        user,
        ad_group.settings.autopilot_state,
        running_status,
        ad_group.settings.state,
        ad_group.settings.ad_group.campaign.real_time_campaign_stop,
        automation.campaignstop.get_campaignstop_state(ad_group.campaign),
        ad_group.settings.landing_mode,
        ad_group.campaign.settings.autopilot,
    )


def get_adgroup_running_status_class(
        user, autopilot_state, running_status, state,
        real_time_campaign_stop, campaignstop_state, is_in_landing, is_campaign_autopilot):
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

    autopilot = autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET or is_campaign_autopilot
    price_discovery = autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC

    if real_time_campaign_stop and campaignstop_state:
        campaignstop_state_status = _get_campaignstop_state_status(campaignstop_state, autopilot=autopilot, price_discovery=price_discovery)
        if campaignstop_state_status:
            return campaignstop_state_status

    if autopilot:
        return dash.constants.InfoboxStatus.AUTOPILOT
    elif price_discovery:
        return dash.constants.InfoboxStatus.ACTIVE_PRICE_DISCOVERY

    return dash.constants.InfoboxStatus.ACTIVE


def get_campaign_running_status(campaign):
    if campaign.settings.landing_mode:
        return dash.constants.InfoboxStatus.LANDING_MODE

    if campaign.real_time_campaign_stop:
        campaignstop_state = automation.campaignstop.get_campaignstop_state(campaign)
        campaignstop_state_status = _get_campaignstop_state_status(campaignstop_state, autopilot=campaign.settings.autopilot)
        if campaignstop_state_status:
            return campaignstop_state_status

    running_exists = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).filter_running().exists()
    if running_exists:
        if campaign.settings.autopilot:
            return dash.constants.InfoboxStatus.AUTOPILOT
        return dash.constants.InfoboxStatus.ACTIVE

    active_exists = dash.models.AdGroup.objects.filter(
        campaign=campaign
    ).filter_active().exists()
    return dash.constants.InfoboxStatus.INACTIVE if active_exists else dash.constants.InfoboxStatus.STOPPED


def _get_campaignstop_state_status(campaignstop_state, autopilot=False, price_discovery=False):
        if not campaignstop_state['allowed_to_run']:
            if campaignstop_state['pending_budget_updates']:
                if autopilot:
                    return dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT
                if price_discovery:
                    return dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY
                return dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE
            return dash.constants.InfoboxStatus.CAMPAIGNSTOP_STOPPED
        if campaignstop_state['almost_depleted']:
            return dash.constants.InfoboxStatus.CAMPAIGNSTOP_LOW_BUDGET
        return None


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
    if status in (dash.constants.InfoboxStatus.ACTIVE,
                  dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE):
        return 'Active'
    if status in (dash.constants.InfoboxStatus.AUTOPILOT,
                  dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT):
        return 'Active - Autopilot mode'
    if status == dash.constants.InfoboxStatus.LANDING_MODE:
        return 'Active - Landing mode'
    if status in (dash.constants.InfoboxStatus.ACTIVE_PRICE_DISCOVERY,
                  dash.constants.InfoboxStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY):
        return 'Active - Price Discovery'
    if status == dash.constants.InfoboxStatus.STOPPED:
        return 'Paused'
    if status == dash.constants.InfoboxStatus.INACTIVE:
        return 'Inactive'
    if status == dash.constants.InfoboxStatus.CAMPAIGNSTOP_STOPPED:
        return 'Stopped - Out of budget (add budget to resume)'
    if status == dash.constants.InfoboxStatus.CAMPAIGNSTOP_LOW_BUDGET:
        return 'Active - Running out of budget'


def _retrieve_active_creditlineitems(account, use_local_currency=False):
    ret = dash.models.CreditLineItem.objects.filter(
        account=account
    )
    if account.agency is not None:
        ret |= dash.models.CreditLineItem.objects.filter(
            agency=account.agency
        )
    if use_local_currency:
        ret = ret.filter(currency=account.currency)
    else:
        ret = ret.filter(currency=dash.constants.Currency.USD)
    return ret.filter_active()


def _compute_daily_cap(use_local_currency, **filters):
    ad_groups = dash.models.AdGroup.objects.filter(
        settings__state=dash.constants.AdGroupSettingsState.ACTIVE,
        **filters
    ).select_related('settings')

    adgroup_sources = dash.models.AdGroupSource.objects.filter(
        settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
        ad_group__in=ad_groups,
    ).values(
        'settings__daily_budget_cc',
        'settings__local_daily_budget_cc',
        'ad_group_id',
        'source__source_type__type',
    )

    adgroup_map = {ad_group.id: ad_group for ad_group in ad_groups}
    ret = 0

    ad_groups_with_active_b1_sources = set()
    for adgroup_source in adgroup_sources:
        adgroup_settings = adgroup_map[adgroup_source['ad_group_id']].settings

        if adgroup_settings.b1_sources_group_enabled and\
           adgroup_source['source__source_type__type'] == dash.constants.SourceType.B1:
            ad_groups_with_active_b1_sources.add(adgroup_source['ad_group_id'])
            continue

        if use_local_currency:
            ret += adgroup_source['settings__local_daily_budget_cc'] or 0
        else:
            ret += adgroup_source['settings__daily_budget_cc'] or 0

    for ad_group_id in ad_groups_with_active_b1_sources:
        ags = adgroup_map[ad_group_id].settings

        if not ags.b1_sources_group_enabled:
            continue

        if ags.b1_sources_group_state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue

        if use_local_currency:
            ret += ags.local_b1_sources_group_daily_budget or 0
        else:
            ret += ags.b1_sources_group_daily_budget or 0

    return ret


def get_primary_campaign_goal(user, campaign, start_date, end_date, currency=dash.constants.Currency.USD, local_values=False):
    primary_goal = dash.campaign_goals.fetch_goals([campaign.pk], end_date).first()
    if primary_goal is None or not primary_goal.primary:
        return []

    performance = dash.campaign_goals.get_goals_performance_campaign(
        user, campaign, start_date, end_date, local_values)
    return _get_primary_campaign_goal(user, campaign, performance, currency)


def get_primary_campaign_goal_ad_group(user, ad_group, start_date, end_date, currency=dash.constants.Currency.USD, local_values=False):
    primary_goal = dash.campaign_goals.fetch_goals([ad_group.campaign_id], end_date).first()
    if primary_goal is None or not primary_goal.primary:
        return []

    performance = dash.campaign_goals.get_goals_performance_ad_group(
        user, ad_group, start_date, end_date, local_values)
    return _get_primary_campaign_goal(user, ad_group.campaign, performance, currency)


def _get_primary_campaign_goal(user, campaign, performance, currency):
    settings = []

    permissions = user.get_all_permissions_with_access_levels()

    status, metric_value, planned_value, campaign_goal = performance[0]
    goal_description = dash.campaign_goals.format_campaign_goal(
        campaign_goal.type,
        metric_value,
        campaign_goal.conversion_goal,
        currency,
    )

    primary_campaign_goal_setting = OverviewSetting(
        'Primary Goal:',
        goal_description,
        planned_value and 'planned {}'.format(
            dash.campaign_goals.format_value(campaign_goal.type, planned_value, currency),
        ) or None,
        section_start=True,
        internal=not permissions.get('zemauth.campaign_goal_performance'),
    )

    primary_campaign_goal_setting.icon = dash.campaign_goals.STATUS_TO_EMOTICON_MAP[status]
    settings.append(primary_campaign_goal_setting.as_dict())

    return settings
