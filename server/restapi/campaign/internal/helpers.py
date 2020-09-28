from decimal import Decimal

import core.features.bcm
import core.features.goals
import dash.campaign_goals
import dash.constants
import dash.features.custom_flags
import dash.models
import restapi.common.helpers


def get_extra_data(user, campaign):
    extra = {
        "archived": campaign.settings.archived,
        "language": campaign.settings.language,
        "can_restore": campaign.can_restore(),
        "agency_id": campaign.account.agency_id,
        "currency": campaign.account.currency,
    }

    extra["goals_defaults"] = core.features.goals.get_campaign_goals_defaults(campaign.account)

    extra["campaign_managers"] = get_campaign_managers(user, campaign)

    if user.has_perm("zemauth.can_see_backend_hacks"):
        extra["hacks"] = get_hacks(campaign)

    if user.has_perm("zemauth.can_see_deals_in_ui"):
        extra["deals"] = get_deals(campaign)

    budget_items = get_budget_items(campaign)
    credit_items = get_credit_items(campaign)

    extra["budgets_overview"] = get_budgets_overview(user, campaign, budget_items, credit_items)
    extra["budgets_depleted"] = get_depleted_budgets(budget_items)
    extra["credits"] = credit_items

    return extra


def get_budget_items(campaign):
    return (
        core.features.bcm.BudgetLineItem.objects.filter(campaign_id=campaign.id)
        .select_related("credit")
        .order_by("-created_dt")
        .annotate_spend_data()
    )


def get_credit_items(campaign):
    return core.features.bcm.CreditLineItem.objects.filter_by_account(campaign.account).filter(
        currency=campaign.account.currency
    )


def get_budgets_overview(user, campaign, budget_items, credit_items):
    can_add_base_costs = user.has_base_costs_and_service_fee_perm_on(campaign)
    can_add_platform_costs = user.has_media_cost_data_cost_and_licence_fee_perm_on(campaign)
    can_add_agency_margin = user.has_agency_spend_and_margin_perm_on(campaign)

    data = {
        "available_budgets_sum": Decimal("0.0000"),
        "unallocated_credit": Decimal("0.0000"),
        "campaign_spend": Decimal("0.0000"),
    }

    if can_add_base_costs:
        data["base_media_spend"] = Decimal("0.0000")
        data["base_data_spend"] = Decimal("0.0000")
        data["service_fee"] = Decimal("0.0000")

    if can_add_platform_costs:
        data["media_spend"] = Decimal("0.0000")
        data["data_spend"] = Decimal("0.0000")
        data["license_fee"] = Decimal("0.0000")

    if can_add_agency_margin:
        data["margin"] = Decimal("0.0000")

    for item in campaign.settings.budgets:
        spend_data = item.get_local_spend_data()
        allocated = item.allocated_amount()
        data["available_budgets_sum"] += allocated - spend_data["etfm_total"]

    for item in credit_items:
        if item.status != dash.constants.CreditLineItemStatus.SIGNED or item.is_past():
            continue
        data["unallocated_credit"] += Decimal(item.amount - item.get_allocated_amount())

    for item in budget_items:
        if item.state() == dash.constants.BudgetLineItemState.PENDING:
            continue

        spend_data = item.get_local_spend_data()
        data["campaign_spend"] += spend_data["etfm_total"]

        if can_add_base_costs:
            data["base_media_spend"] += spend_data["base_media"]
            data["base_data_spend"] += spend_data["base_data"]
            data["service_fee"] += spend_data["service_fee"]

        if can_add_platform_costs:
            data["media_spend"] += spend_data["media"]
            data["data_spend"] += spend_data["data"]
            data["license_fee"] += spend_data["license_fee"]

        if can_add_agency_margin:
            data["margin"] += spend_data["margin"]

    return data


def get_depleted_budgets(budget_items):
    return [
        item
        for item in budget_items
        if item.state() in (dash.constants.BudgetLineItemState.DEPLETED, dash.constants.BudgetLineItemState.INACTIVE)
    ]


def get_campaign_managers(user, campaign):
    users = restapi.common.helpers.get_users_for_manager(user, campaign.account, campaign.settings.campaign_manager)
    return [{"id": user.id, "name": restapi.common.helpers.get_user_full_name_or_email(user)} for user in users]


def get_deals(campaign):
    if campaign.id is None:
        return []
    return restapi.common.helpers.get_applied_deals_dict(campaign.get_all_configured_deals())


def get_hacks(campaign):
    if campaign.id is None:
        return []
    return dash.models.CustomHack.objects.all().filter_applied(campaign=campaign).filter_active(
        True
    ).to_dict_list() + dash.features.custom_flags.helpers.get_all_custom_flags_on_campaign(campaign)
