import collections

from django.db.models.query import QuerySet

import automation.campaignstop
import core.features.delivery_status
import core.models
import dash.constants


def get_account_delivery_status_map(accounts):
    detailed_delivery_status_map = get_account_detailed_delivery_status_map(accounts)
    delivery_status_map = {k: _map_delivery_status_from_detailed(v) for k, v in detailed_delivery_status_map.items()}

    return delivery_status_map


def get_account_detailed_delivery_status_map(accounts):
    delivery_status_map = collections.defaultdict(dict)

    if not isinstance(accounts, QuerySet):
        accounts = core.models.Account.objects.filter(id__in=[account.id for account in accounts])

    accounts = accounts.select_related("agency").prefetch_related("campaign_set")
    for account in accounts:
        delivery_status = get_account_detailed_delivery_status(account)
        delivery_status_map[account.id] = delivery_status

    return delivery_status_map


def get_account_delivery_status(account):
    return _map_delivery_status_from_detailed(get_account_detailed_delivery_status(account))


def get_account_detailed_delivery_status(account):
    if _is_disabled(account):
        return core.features.delivery_status.DetailedDeliveryStatus.DISABLED
    running_exists = core.models.AdGroup.objects.filter(campaign__account=account).filter_current_and_active().exists()
    if running_exists:
        return core.features.delivery_status.DetailedDeliveryStatus.ACTIVE

    active_exists = core.models.AdGroup.objects.filter(campaign__account=account).filter_active().exists()
    return (
        core.features.delivery_status.DetailedDeliveryStatus.INACTIVE
        if active_exists
        else core.features.delivery_status.DetailedDeliveryStatus.STOPPED
    )


def _is_disabled(account):
    return account.is_disabled or (account.agency and account.agency.is_disabled)


def get_campaign_delivery_status_map(campaigns):
    detailed_delivery_status_map = get_campaign_detailed_delivery_status_map(campaigns)
    delivery_status_map = {k: _map_delivery_status_from_detailed(v) for k, v in detailed_delivery_status_map.items()}

    return delivery_status_map


def get_campaign_detailed_delivery_status_map(campaigns):
    delivery_status_map = collections.defaultdict(dict)

    if not isinstance(campaigns, QuerySet):
        campaigns = core.models.Campaign.objects.filter(id__in=[campaign.id for campaign in campaigns])

    campaigns = campaigns.select_related("settings", "account__agency")
    for campaign in campaigns:
        delivery_status = get_campaign_detailed_delivery_status(campaign)
        delivery_status_map[campaign.id] = delivery_status

    return delivery_status_map


def get_campaign_delivery_status(campaign):
    return _map_delivery_status_from_detailed(get_campaign_detailed_delivery_status(campaign))


def get_campaign_detailed_delivery_status(campaign):
    if not campaign.account.agency_uses_realtime_autopilot():  # TODO: RTAP: remove this after Phase 1
        return _get_campaign_delivery_status_legacy(campaign)

    if not campaign.account.is_enabled():
        return core.features.delivery_status.DetailedDeliveryStatus.DISABLED
    if campaign.real_time_campaign_stop:
        campaignstop_state = automation.campaignstop.get_campaignstop_state(campaign)
        campaignstop_state_status = _get_campaignstop_state_status(
            campaignstop_state, campaign_budget_optimization_enabled=campaign.settings.autopilot
        )
        if campaignstop_state_status:
            return campaignstop_state_status

    running_exists = core.models.AdGroup.objects.filter(campaign=campaign).filter_current_and_active().exists()
    if running_exists:
        if campaign.settings.autopilot:
            return core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION
        return core.features.delivery_status.DetailedDeliveryStatus.ACTIVE

    active_exists = core.models.AdGroup.objects.filter(campaign=campaign).filter_active().exists()
    return (
        core.features.delivery_status.DetailedDeliveryStatus.INACTIVE
        if active_exists
        else core.features.delivery_status.DetailedDeliveryStatus.STOPPED
    )


def _get_campaign_delivery_status_legacy(campaign):
    if not campaign.account.is_enabled():
        return core.features.delivery_status.DetailedDeliveryStatus.DISABLED
    if campaign.real_time_campaign_stop:
        campaignstop_state = automation.campaignstop.get_campaignstop_state(campaign)
        campaignstop_state_status = _get_campaignstop_state_status_legacy(
            campaignstop_state, autopilot=campaign.settings.autopilot
        )
        if campaignstop_state_status:
            return campaignstop_state_status

    running_exists = core.models.AdGroup.objects.filter(campaign=campaign).filter_current_and_active().exists()
    if running_exists:
        if campaign.settings.autopilot:
            return core.features.delivery_status.DetailedDeliveryStatus.AUTOPILOT
        return core.features.delivery_status.DetailedDeliveryStatus.ACTIVE

    active_exists = core.models.AdGroup.objects.filter(campaign=campaign).filter_active().exists()
    return (
        core.features.delivery_status.DetailedDeliveryStatus.INACTIVE
        if active_exists
        else core.features.delivery_status.DetailedDeliveryStatus.STOPPED
    )


def get_ad_group_delivery_status_map(ad_groups):
    detailed_delivery_status_map = get_ad_group_detailed_delivery_status_map(ad_groups)
    delivery_status_map = {k: _map_delivery_status_from_detailed(v) for k, v in detailed_delivery_status_map.items()}

    return delivery_status_map


def get_ad_group_detailed_delivery_status_map(ad_groups):
    delivery_status_map = collections.defaultdict(dict)
    if not isinstance(ad_groups, QuerySet):
        ad_groups = core.models.AdGroup.objects.filter(id__in=[ad_group.id for ad_group in ad_groups])

    ad_groups = ad_groups.select_related("campaign__account__agency", "settings", "campaign__settings")
    for ad_group in ad_groups:
        delivery_status = get_ad_group_detailed_delivery_status(ad_group)
        delivery_status_map[ad_group.id] = delivery_status

    return delivery_status_map


def get_ad_group_delivery_status(ad_group):
    return _map_delivery_status_from_detailed(get_ad_group_detailed_delivery_status(ad_group))


def get_ad_group_detailed_delivery_status(ad_group):
    if not ad_group.campaign.account.is_enabled():
        return core.features.delivery_status.DetailedDeliveryStatus.DISABLED
    delivery_status = core.models.AdGroup.get_running_status(ad_group.settings)

    agency_uses_realtime_autopilot = (
        ad_group.campaign.account.agency.uses_realtime_autopilot if ad_group.campaign.account.agency else False
    )
    if not agency_uses_realtime_autopilot:  # TODO: RTAP: remove this after Phase 1
        return _get_ad_group_delivery_status_legacy(
            ad_group.settings.autopilot_state,
            delivery_status,
            ad_group.settings.state,
            ad_group.campaign.real_time_campaign_stop,
            automation.campaignstop.get_campaignstop_state(ad_group.campaign),
            ad_group.campaign.settings.autopilot,
        )

    return get_ad_group_detailed_delivery_status_from_state(
        ad_group.settings.autopilot_state,
        delivery_status,
        ad_group.settings.state,
        ad_group.campaign.real_time_campaign_stop,
        automation.campaignstop.get_campaignstop_state(ad_group.campaign),
        ad_group.campaign.settings.autopilot,
    )


def _get_ad_group_delivery_status_legacy(
    autopilot_state, delivery_status, state, real_time_campaign_stop, campaignstop_state, is_campaign_autopilot
):
    if (
        state == dash.constants.AdGroupSettingsState.INACTIVE
        and delivery_status == dash.constants.AdGroupRunningStatus.INACTIVE
    ):
        return core.features.delivery_status.DetailedDeliveryStatus.STOPPED

    if (
        delivery_status == dash.constants.AdGroupRunningStatus.INACTIVE
        and state == dash.constants.AdGroupSettingsState.ACTIVE
    ) or (
        delivery_status == dash.constants.AdGroupRunningStatus.ACTIVE
        and state == dash.constants.AdGroupSettingsState.INACTIVE
    ):
        return core.features.delivery_status.DetailedDeliveryStatus.INACTIVE

    autopilot = (
        autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET or is_campaign_autopilot
    )
    price_discovery = autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC

    if real_time_campaign_stop and campaignstop_state:
        campaignstop_state_status = _get_campaignstop_state_status_legacy(
            campaignstop_state, autopilot=autopilot, price_discovery=price_discovery
        )
        if campaignstop_state_status:
            return campaignstop_state_status

    if autopilot:
        return core.features.delivery_status.DetailedDeliveryStatus.AUTOPILOT
    elif price_discovery:
        return core.features.delivery_status.DetailedDeliveryStatus.ACTIVE_PRICE_DISCOVERY

    return core.features.delivery_status.DetailedDeliveryStatus.ACTIVE


def get_ad_group_detailed_delivery_status_from_state(
    autopilot_state,
    delivery_status,
    state,
    real_time_campaign_stop,
    campaignstop_state,
    campaign_budget_optimization_enabled,
):
    if (
        state == dash.constants.AdGroupSettingsState.INACTIVE
        and delivery_status == dash.constants.AdGroupRunningStatus.INACTIVE
    ):
        return core.features.delivery_status.DetailedDeliveryStatus.STOPPED

    if (
        delivery_status == dash.constants.AdGroupRunningStatus.INACTIVE
        and state == dash.constants.AdGroupSettingsState.ACTIVE
    ) or (
        delivery_status == dash.constants.AdGroupRunningStatus.ACTIVE
        and state == dash.constants.AdGroupSettingsState.INACTIVE
    ):
        return core.features.delivery_status.DetailedDeliveryStatus.INACTIVE

    optimal_bid_strategy_enabled = autopilot_state != dash.constants.AdGroupSettingsAutopilotState.INACTIVE

    if real_time_campaign_stop and campaignstop_state:
        campaignstop_state_status = _get_campaignstop_state_status(
            campaignstop_state,
            campaign_budget_optimization_enabled=campaign_budget_optimization_enabled,
            optimal_bid_strategy_enabled=optimal_bid_strategy_enabled,
        )
        if campaignstop_state_status:
            return campaignstop_state_status

    if campaign_budget_optimization_enabled and optimal_bid_strategy_enabled:
        return core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION_OPTIMAL_BID
    elif campaign_budget_optimization_enabled:
        return core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION
    elif optimal_bid_strategy_enabled:
        return core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID

    return core.features.delivery_status.DetailedDeliveryStatus.ACTIVE


def _get_campaignstop_state_status(
    campaignstop_state, campaign_budget_optimization_enabled=False, optimal_bid_strategy_enabled=False
):
    if not campaignstop_state["allowed_to_run"]:
        if campaignstop_state["pending_budget_updates"]:
            if campaign_budget_optimization_enabled and optimal_bid_strategy_enabled:
                return (
                    core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION_OPTIMAL_BID
                )
            elif campaign_budget_optimization_enabled:
                return (
                    core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION
                )
            elif optimal_bid_strategy_enabled:
                return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID
            return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE
        return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED
    if campaignstop_state["almost_depleted"]:
        return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET
    return None


def _get_campaignstop_state_status_legacy(campaignstop_state, autopilot=False, price_discovery=False):
    if not campaignstop_state["allowed_to_run"]:
        if campaignstop_state["pending_budget_updates"]:
            if autopilot:
                return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT
            if price_discovery:
                return (
                    core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY
                )
            return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE
        return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED
    if campaignstop_state["almost_depleted"]:
        return core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET
    return None


def _map_delivery_status_from_detailed(detailed_delivery_status):
    if detailed_delivery_status == core.features.delivery_status.DetailedDeliveryStatus.DISABLED:
        return core.features.delivery_status.DeliveryStatus.DISABLED

    if detailed_delivery_status in (
        core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE,
        core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION,
        core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID,
        core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION_OPTIMAL_BID,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION_OPTIMAL_BID,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET,
        core.features.delivery_status.DetailedDeliveryStatus.AUTOPILOT,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT,
        core.features.delivery_status.DetailedDeliveryStatus.ACTIVE_PRICE_DISCOVERY,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY,
    ):
        return core.features.delivery_status.DeliveryStatus.ACTIVE

    if detailed_delivery_status in (
        core.features.delivery_status.DetailedDeliveryStatus.STOPPED,
        core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED,
    ):
        return core.features.delivery_status.DeliveryStatus.STOPPED

    if detailed_delivery_status == core.features.delivery_status.DetailedDeliveryStatus.INACTIVE:
        return core.features.delivery_status.DeliveryStatus.INACTIVE
