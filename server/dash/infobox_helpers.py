import copy
import datetime
from decimal import ROUND_HALF_DOWN
from decimal import Decimal

from django.core.cache import caches
from django.db import models
from django.db.models import Sum

import core.features.bid_modifiers
import core.features.delivery_status
import core.features.multicurrency
import dash.campaign_goals
import dash.constants
import dash.models
import etl.materialization_run
import redshiftapi.api_breakdowns
import utils.cache_helper
import utils.dates_helper
import utils.lc_helper
import zemauth.models
from utils import converters
from utils import dates_helper
from zemauth.features.entity_permission import Permission

MAX_PREVIEW_REGIONS = 1


class OverviewSetting(object):
    def __init__(
        self,
        name="",
        value="",
        description=None,
        tooltip=None,
        setting_type="setting",
        section_start=None,
        internal=False,
        warning=None,
        flag=None,
    ):
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
        self.children = []
        self.flag = flag

    def comment(self, details_label, details_description):
        ret = copy.deepcopy(self)
        ret.details_label = details_label
        ret.details_content = details_description
        return ret

    def add_child(self, child):
        self.children.append(child)

    def as_dict(self):
        ret = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            ret[key] = value
        return ret


class OverviewSeparator(OverviewSetting):
    def __init__(self):
        super(OverviewSeparator, self).__init__("", "", "", setting_type="hr")


def format_flight_time(start_date, end_date, no_ad_groups_or_budgets):
    if no_ad_groups_or_budgets:
        return "-", None

    start_date_str = start_date.strftime("%m/%d") if start_date else ""
    end_date_str = end_date.strftime("%m/%d") if end_date else "Ongoing"

    flight_time = "{start_date} - {end_date}".format(start_date=start_date_str, end_date=end_date_str)
    today = dates_helper.local_today()
    if not end_date:
        flight_time_left_days = None
    elif today > end_date:
        flight_time_left_days = 0
    else:
        flight_time_left_days = (end_date - today).days + 1
    return flight_time, flight_time_left_days


def create_bid_value_overview_settings(ad_group):
    if not ad_group.campaign.account.agency_uses_realtime_autopilot():  # TODO: RTAP: remove this after Phase 1
        return create_bid_value_overview_settings_legacy(ad_group)

    overview_settings = []

    bidding_type = "CPC" if ad_group.bidding_type == dash.constants.BiddingType.CPC else "CPM"

    if ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.INACTIVE:
        tooltip_text = (
            "<p>Bid {bidding_type} displays the autopilot’s target bid set in ad group settings</p>"
        ).format(bidding_type=bidding_type)

        formatted_bid_value = _format_ad_group_bid_value(
            ad_group.settings.local_bid, ad_group.campaign.account.currency
        )

        overview_settings.append(
            OverviewSetting(name="Bid {}:".format(bidding_type), value=formatted_bid_value, tooltip=tooltip_text)
        )
    else:
        tooltip_text = (
            "<p>Maximum bid {bidding_type} displays autopilot’s maximum allowed bid {bidding_type} set in ad group settings.</p>"
            + "<p>Autopilot will never buy with {bidding_type} higher than <strong>maximum {bidding_type}</strong>.</p>"
            if ad_group.settings.local_bid is not None
            else "<p>Autopilot bids are not restricted.</p>"
            + "<p>Autopilot will find the optimal {bidding_type} to fill the ad group's daily budget.</p>"
        ).format(bidding_type=bidding_type)

        formatted_bid_value = (
            _format_ad_group_bid_value(ad_group.settings.local_bid, ad_group.campaign.account.currency)
            if ad_group.settings.local_bid is not None
            else "No limit"
        )

        overview_settings.append(
            OverviewSetting(name="Max bid {}:".format(bidding_type), value=formatted_bid_value, tooltip=tooltip_text)
        )

    if ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.INACTIVE:
        tooltip_text = (
            "<p>Final bid {bidding_type} range displays minimum and maximum possible bid {bidding_type} based on autopilot’s target bid and on bid modifiers applied by you on all dimensions.</p>"
        ).format(bidding_type=bidding_type)
    else:
        tooltip_text = (
            "<p>Final bid {bidding_type} range displays minimum and maximum possible bid {bidding_type} based on autopilot’s maximum bid {bidding_type} and bid modifiers applied by you on all dimensions.</p>"
        ).format(bidding_type=bidding_type)

    min_bid, max_bid = core.features.bid_modifiers.get_min_max_local_bids(ad_group)

    if ad_group.settings.autopilot_state != dash.constants.AdGroupSettingsAutopilotState.INACTIVE:
        if max_bid is None:
            return overview_settings
        else:
            min_bid = 0.0001

    formatted_min_bid_value = _format_ad_group_bid_value(min_bid, ad_group.campaign.account.currency, places=4)
    formatted_max_bid_value = _format_ad_group_bid_value(max_bid, ad_group.campaign.account.currency, places=4)

    overview_settings.append(
        OverviewSetting(
            name="Final bid {} range:".format(bidding_type),
            value="{} - {}".format(formatted_min_bid_value, formatted_max_bid_value),
            tooltip=tooltip_text,
        )
    )

    return overview_settings


def _format_ad_group_bid_value(bid_value, currency, places=4):
    return utils.lc_helper.format_currency(
        bid_value,
        places=places,
        rounding=ROUND_HALF_DOWN,
        curr=core.features.multicurrency.get_currency_symbol(currency),
    )


def create_region_setting(regions):
    preview_regions = regions[:MAX_PREVIEW_REGIONS]
    full_regions = regions

    preview_region = " " + ", ".join(preview_regions)
    if len(full_regions) > 1:
        preview_region = ""

    targeting_region_setting = OverviewSetting("", "Location:{regions}".format(regions=preview_region))
    if len(full_regions) > 1:
        targeting_region_setting = targeting_region_setting.comment("Show more", ", ".join(full_regions))
    return targeting_region_setting


def get_ideal_campaign_spend(user, campaign, until_date=None):
    at_date = until_date or dates_helper.local_today()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    if len(budgets) == 0:
        return Decimal(0)
    all_budget_spends_at_date = [b.get_ideal_budget_spend(at_date) for b in budgets]
    return sum(all_budget_spends_at_date)


def get_total_campaign_budgets_amount(user, campaign, until_date=None):
    # campaign budget based on non-depleted budget line items
    at_date = until_date or utils.dates_helper.local_today()
    budgets = _retrieve_active_budgetlineitems([campaign], at_date)
    return sum(x.amount for x in budgets)


def get_yesterday_adgroup_spend(ad_group):
    constraints = {"ad_group_id": [ad_group.id]}
    return _get_yesterday_spend("ad_group_id", constraints)


def get_yesterday_account_spend(account):
    constraints = {"account_id": [account.id]}
    return _get_yesterday_spend("account_id", constraints)


def get_yesterday_accounts_spend(accounts, use_local_currency):
    constraints = {"account_id": [account.id for account in accounts]}
    return _get_yesterday_spend("account_id", constraints, use_local_currency=use_local_currency)


def _get_yesterday_spend(breakdown, constraints, use_local_currency=True):
    yesterday = utils.dates_helper.local_yesterday()
    constraints.update({"date__gte": yesterday, "date__lte": yesterday})
    query_results = redshiftapi.api_breakdowns.query_with_background_cache(
        [breakdown],
        constraints,
        parents=None,
        goals=None,
        use_publishers_view=False,
        metrics=["yesterday_etfm_cost", "local_yesterday_etfm_cost"],
    )

    ret = {"yesterday_etfm_cost": 0}
    for row in query_results:
        if use_local_currency:
            ret["yesterday_etfm_cost"] += row["local_yesterday_etfm_cost"] or 0
        else:
            ret["yesterday_etfm_cost"] += row["yesterday_etfm_cost"] or 0
    return ret


def get_mtd_accounts_spend(accounts, use_local_currency):
    constraints = {"account_id": [account.id for account in accounts]}
    return _get_mtd_spend("account_id", constraints, use_local_currency)


def _get_mtd_spend(breakdown, constraints, use_local_currency):
    start_date = utils.dates_helper.local_today().replace(day=1)
    constraints.update({"date__gte": start_date})
    query_results = redshiftapi.api_breakdowns.query_with_background_cache(
        [breakdown],
        constraints,
        parents=None,
        goals=None,
        use_publishers_view=False,
        metrics=["e_media_cost", "et_cost", "etfm_cost", "local_e_media_cost", "local_et_cost", "local_etfm_cost"],
    )

    ret = {"e_media_cost": 0, "et_cost": 0, "etfm_cost": 0}
    for row in query_results:
        if use_local_currency:
            ret["e_media_cost"] += row["local_e_media_cost"] or 0
            ret["et_cost"] += row["local_et_cost"] or 0
            ret["etfm_cost"] += row["local_etfm_cost"] or 0
        else:
            ret["e_media_cost"] += row["e_media_cost"] or 0
            ret["et_cost"] += row["et_cost"] or 0
            ret["etfm_cost"] += row["etfm_cost"] or 0
    return ret


def create_yesterday_data_setting():
    yesterday_data_complete = etl.materialization_run.etl_data_complete_for_date(utils.dates_helper.local_yesterday())
    yesterday_data_flag = "Complete" if yesterday_data_complete else "Partial"
    return OverviewSetting("Yesterday data:", flag=yesterday_data_flag)


def calculate_daily_ad_group_cap(ad_group):
    """
    Daily media cap
    """
    return _compute_daily_cap(id=ad_group.id)


def calculate_daily_campaign_cap(campaign):
    return _compute_daily_cap(campaign_id=campaign.id)


def calculate_daily_account_cap(account):
    return _compute_daily_cap(campaign__account_id=account.id)


def calculate_available_campaign_budget(campaign):
    # campaign budget based on non-depleted budget line items
    today = dates_helper.local_today()
    budgets = _retrieve_active_budgetlineitems([campaign], today)
    return sum(x.get_local_available_etfm_amount(today) for x in budgets)


def calculate_allocated_and_available_credit(account):
    credits = _retrieve_active_creditlineitems(account)
    credit_total = credits.aggregate(amount_sum=Sum("amount"))
    budget_total = dash.models.BudgetLineItem.objects.filter(credit__in=credits).aggregate(
        amount_sum=Sum("amount"), freed_sum=converters.CC_TO_DECIMAL_CURRENCY * Sum("freed_cc")
    )
    assigned = credit_total["amount_sum"] or 0
    allocated = (budget_total["amount_sum"] or 0) - (budget_total["freed_sum"] or 0)

    return allocated, (assigned or 0) - allocated


def calculate_credit_refund(account):
    return core.features.bcm.RefundLineItem.objects.filter(
        credit__account=account, start_date=utils.dates_helper.local_today().replace(day=1)
    ).aggregate(Sum("amount"))["amount__sum"]


def create_yesterday_spend_setting(yesterday_costs, daily_budget, currency):
    yesterday_cost = yesterday_costs["yesterday_etfm_cost"]
    currency_symbol = core.features.multicurrency.get_currency_symbol(currency)

    filled_daily_ratio = None
    if daily_budget > 0:
        filled_daily_ratio = float(yesterday_cost or 0) / float(daily_budget)

    if filled_daily_ratio:
        daily_ratio_description = "{:.2f}% of {} Daily Spend Cap".format(
            abs(filled_daily_ratio) * 100, utils.lc_helper.format_currency(daily_budget, curr=currency_symbol)
        )
    else:
        daily_ratio_description = "N/A"

    yesterday_spend_setting = OverviewSetting(
        "Yesterday spend:",
        utils.lc_helper.format_currency(yesterday_cost, curr=currency_symbol),
        description=daily_ratio_description,
    )
    return yesterday_spend_setting


def count_active_adgroups(campaign):
    return dash.models.AdGroup.objects.filter(campaign=campaign).filter_current_and_active().count()


def count_active_campaigns(account):
    active_campaign_ids = set(
        dash.models.AdGroup.objects.filter(campaign__account=account)
        .filter_current_and_active()
        .values_list("campaign", flat=True)
    )
    return len(active_campaign_ids)


def count_active_agency_accounts(user):
    accounts = (
        dash.models.AdGroup.objects.all().filter_current_and_active().filter_by_entity_permission(user, Permission.READ)
    )
    return accounts.order_by().values("campaign__account").distinct().count()


def _active_account_ids():
    cache = caches["dash_db_cache"]
    cache_key = "active_account_ids"
    active_account_ids = cache.get(cache_key, None)
    if active_account_ids is not None:
        return active_account_ids

    active_account_ids = set(
        dash.models.AdGroup.objects.all()
        .filter_current_and_active()
        .order_by()  # disable default adgroup order
        .values_list("campaign__account", flat=True)
        .distinct()
    )

    cache.set(cache_key, active_account_ids)
    return active_account_ids


def count_active_accounts(filtered_agencies, filtered_account_types):
    count_filtered_ids = (
        dash.models.Account.objects.all()
        .filter(id__in=_active_account_ids())
        .filter_by_agencies(filtered_agencies)
        .filter_by_account_types(filtered_account_types)
        .count()
    )
    return count_filtered_ids


def format_username(user):
    if not user:
        return "N/A"
    return user.get_full_name()


def _filter_user_by_account_type(users, filtered_account_types):
    if not filtered_account_types:
        return users
    latest_account_settings = (
        dash.models.AccountSettings.objects.all()
        .filter(
            models.Q(account__entitypermission__user__in=users)
            | models.Q(account__agency__entitypermission__user__in=users)
        )
        .group_current_settings()
    )

    filtered_latest_account_settings = (
        dash.models.AccountSettings.objects.filter(pk__in=latest_account_settings)
        .filter(account_type__in=filtered_account_types)
        .values_list("account_id", flat=True)
    )

    return (
        users.filter(models.Q(entitypermission__account__id__in=filtered_latest_account_settings))
        .union(users.filter_by_internal())
        .distinct()
    )


def count_weekly_logged_in_users(filtered_agencies, filtered_account_types):
    logged_in_users = (
        zemauth.models.User.objects.filter(last_login__gte=_one_week_ago(), last_login__lte=_until_today())
        .filter_selfmanaged()
        .filter_by_agencies(filtered_agencies)
    )
    return _filter_user_by_account_type(logged_in_users, filtered_account_types).count()


def _active_user_ids():
    cache = caches["dash_db_cache"]
    cache_key = "active_user_ids"
    active_user_ids = cache.get(cache_key, None)
    if active_user_ids is not None:
        return active_user_ids

    active_user_ids = set(
        dash.models.History.objects.all()
        .filter(created_dt__gte=_one_week_ago(), created_dt__lte=_until_today())
        .filter_selfmanaged()
        .values_list("created_by_id", flat=True)
        .distinct()
    )

    cache.set(cache_key, active_user_ids)
    return active_user_ids


def _one_week_ago():
    now = utils.dates_helper.local_midnight_to_utc_time()
    return now - datetime.timedelta(days=7)


def _until_today():
    return utils.dates_helper.local_midnight_to_utc_time()


def _retrieve_active_budgetlineitems(campaign, date):
    if not campaign:
        return dash.models.BudgetLineItem.objects.none()

    qs = dash.models.BudgetLineItem.objects.filter(campaign__in=campaign)

    return qs.filter_active(date)


def get_entity_delivery_text(status, agency_uses_realtime_autopilot):
    if not agency_uses_realtime_autopilot:  # TODO: RTAP: remove this after Phase 1
        return get_entity_delivery_text_legacy(status)

    if status == core.features.delivery_status.DetailedDeliveryStatus.DISABLED:
        return "Disabled - Contact Zemanta CSM"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
    ):
        return "Active"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION,
    ):
        return "Active - Budget optimization"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID,
    ):
        return "Active - Optimal bid optimization"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION_OPTIMAL_BID,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION_OPTIMAL_BID,
    ):
        return "Active - Budget and optimal bid optimization"
    if status == core.features.delivery_status.DetailedDeliveryStatus.STOPPED:
        return "Paused"
    if status == core.features.delivery_status.DetailedDeliveryStatus.INACTIVE:
        return "Inactive"
    if status == core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED:
        return "Stopped - Out of budget"
    if status == core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET:
        return "Active - Running out of budget"


def _retrieve_active_creditlineitems(account):
    ret = dash.models.CreditLineItem.objects.filter(account=account)
    if account.agency is not None:
        ret |= dash.models.CreditLineItem.objects.filter(agency=account.agency)
    ret = ret.filter(currency=account.currency)
    return ret.filter_active()


def _compute_daily_cap(**filters):
    return dash.models.AdGroup.objects.filter(**filters).compute_total_local_daily_cap()


def get_primary_campaign_goal(user, campaign, start_date, end_date, currency=dash.constants.Currency.USD):
    primary_goal = dash.campaign_goals.fetch_goals([campaign.pk], end_date).first()
    if primary_goal is None or not primary_goal.primary:
        return []

    performance = dash.campaign_goals.get_goals_performance_campaign(
        user, campaign, start_date, end_date, local_values=True
    )
    return _get_primary_campaign_goal(performance, currency)


def get_primary_campaign_goal_ad_group(user, ad_group, start_date, end_date, currency=dash.constants.Currency.USD):
    primary_goal = dash.campaign_goals.fetch_goals([ad_group.campaign_id], end_date).first()
    if primary_goal is None or not primary_goal.primary:
        return []

    performance = dash.campaign_goals.get_goals_performance_ad_group(
        user, ad_group, start_date, end_date, local_values=True
    )
    return _get_primary_campaign_goal(performance, currency)


def _get_primary_campaign_goal(performance, currency):
    settings = []

    status, metric_value, planned_value, campaign_goal = performance[0]
    goal_description = dash.campaign_goals.format_campaign_goal(
        campaign_goal.type, metric_value, campaign_goal.conversion_goal, currency
    )

    primary_campaign_goal_setting = OverviewSetting(
        "Primary Goal:",
        goal_description,
        planned_value
        and "planned {}".format(dash.campaign_goals.format_value(campaign_goal.type, planned_value, currency))
        or None,
        section_start=True,
    )

    primary_campaign_goal_setting.icon = dash.campaign_goals.STATUS_TO_EMOTICON_MAP[status]
    settings.append(primary_campaign_goal_setting.as_dict())

    return settings


def calculate_flight_dates(ags_start_date, ags_end_date, budgets_start_date, budgets_end_date):
    start_date = None
    end_date = None

    if ags_start_date:
        start_date = max(ags_start_date, budgets_start_date or datetime.date.min)
    elif budgets_start_date:
        start_date = budgets_start_date

    if ags_end_date:
        end_date = min(ags_end_date, budgets_end_date or datetime.date.max)
    elif budgets_end_date:
        end_date = budgets_end_date

    return start_date, end_date


def calculate_budgets_flight_dates_for_date_range(campaign, start_date, end_date):
    budgets_start_date = None
    budgets_end_date = None

    campaign_budgets = (
        dash.models.BudgetLineItem.objects.filter(campaign=campaign)
        .exclude(start_date__gt=end_date or datetime.date.max)
        .exclude(end_date__lt=start_date or datetime.date.min)
        .order_by("start_date", "end_date")
    )

    for budget in campaign_budgets:
        if not budgets_start_date:
            budgets_start_date = budget.start_date

        if not budgets_end_date:
            budgets_end_date = budget.end_date

        if budgets_end_date < budget.start_date:
            # Non-overlapping budgets
            today = utils.dates_helper.local_today()
            if budgets_end_date >= today:
                # Use flight dates of currently active or upcoming budgets
                return budgets_start_date, budgets_end_date
            else:
                # Proceed finding flight dates of budgets that will be active next
                budgets_start_date = budget.start_date
                budgets_end_date = budget.end_date
        elif budgets_end_date < budget.end_date:
            # Overlapping budgets, extend range
            budgets_end_date = budget.end_date

    return budgets_start_date, budgets_end_date


# LEGACY - TODO: RTAP: remove everything below this line after Phase 1
def create_bid_value_overview_settings_legacy(ad_group):
    overview_settings = []

    bidding_type = "CPC" if ad_group.bidding_type == dash.constants.BiddingType.CPC else "CPM"

    if ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.INACTIVE:
        tooltip_text = (
            "<p>Bid {bidding_type} is set in the ad group settings.</p>"
            + "<p>Bidder will try to optimize traffic buying towards this {bidding_type}.</p>"
            + "<p>You can use bid modifiers to change the bid {bidding_type} for subset of traffic based on traffic characteristics like publisher, device and others.</p>"
        ).format(bidding_type=bidding_type)

        formatted_bid_value = _format_ad_group_bid_value(
            ad_group.settings.local_cpc
            if ad_group.bidding_type == dash.constants.BiddingType.CPC
            else ad_group.settings.local_cpm,
            ad_group.campaign.account.currency,
        )
        overview_settings.append(
            OverviewSetting(name="Bid {}:".format(bidding_type), value=formatted_bid_value, tooltip=tooltip_text)
        )
    else:
        tooltip_text = (
            "<p>You can set the maximum autopilot bid {bidding_type} in the ad group settings.</p>"
            + "<p>Autopilot will never buy with {bidding_type} higher than <strong>maximum {bidding_type}</strong>.</p>"
        ).format(bidding_type=bidding_type)

        formatted_bid_value = (
            _format_ad_group_bid_value(ad_group.settings.local_max_autopilot_bid, ad_group.campaign.account.currency)
            if ad_group.settings.local_max_autopilot_bid is not None
            else "No limit"
        )
        overview_settings.append(
            OverviewSetting(name="Max bid {}:".format(bidding_type), value=formatted_bid_value, tooltip=tooltip_text)
        )

    tooltip_text = (
        "<p>When you are using bid modifiers your bid {bidding_type} is no longer a fixed value. Instead, it depends on the type of the traffic and varies from auction to auction."
        + "<p>Final bid {bidding_type} displays the minimal and maximal possible {bidding_type} when bid modifiers are applied.</p>"
    ).format(bidding_type=bidding_type)

    min_bid, max_bid = core.features.bid_modifiers.get_min_max_local_bids(ad_group)
    formatted_min_bid_value = _format_ad_group_bid_value(min_bid, ad_group.campaign.account.currency, places=4)
    formatted_max_bid_value = _format_ad_group_bid_value(max_bid, ad_group.campaign.account.currency, places=4)

    overview_settings.append(
        OverviewSetting(
            name="Final bid {} range:".format(bidding_type),
            value="{} - {}".format(formatted_min_bid_value, formatted_max_bid_value),
            tooltip=tooltip_text,
        )
    )

    return overview_settings


def get_entity_delivery_text_legacy(status):
    if status == core.features.delivery_status.DetailedDeliveryStatus.DISABLED:
        return "Disabled - Contact Zemanta CSM"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
    ):
        return "Active"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.AUTOPILOT,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT,
    ):
        return "Active - Autopilot mode"
    if status in (
        core.features.delivery_status.DetailedDeliveryStatus.ACTIVE_PRICE_DISCOVERY,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY,
    ):
        return "Active - Price Discovery"
    if status == core.features.delivery_status.DetailedDeliveryStatus.STOPPED:
        return "Paused"
    if status == core.features.delivery_status.DetailedDeliveryStatus.INACTIVE:
        return "Inactive"
    if status == core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED:
        return "Stopped - Out of budget"
    if status == core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET:
        return "Active - Running out of budget"
