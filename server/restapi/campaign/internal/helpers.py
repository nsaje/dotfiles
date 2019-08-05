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
        "can_archive": campaign.can_archive(),
        "can_restore": campaign.can_restore(),
        "currency": campaign.account.currency,
    }

    if user.has_perm("zemauth.can_see_campaign_goals"):
        extra["goals_defaults"] = core.features.goals.get_campaign_goals_defaults(campaign.account)

    if user.has_perm("zemauth.can_modify_campaign_manager"):
        extra["campaign_managers"] = get_campaign_managers(user, campaign)

    if user.has_perm("zemauth.can_see_backend_hacks"):
        extra["hacks"] = get_hacks(campaign)

    if user.has_perm("zemauth.can_see_deals_in_ui"):
        extra["deals"] = get_deals(campaign)

    if user.has_perm("zemauth.can_see_new_budgets"):
        active_budget_items = campaign.settings.budgets
        budget_items = get_budget_items(campaign)
        credit_items = get_credit_items(campaign)

        extra["budgets_overview"] = get_budgets_overview(
            user, campaign, active_budget_items, budget_items, credit_items
        )
        extra["budgets_depleted"] = get_depleted_budgets(budget_items)
        extra["account_credits"] = credit_items

    return extra


def get_budget_items(campaign):
    return (
        core.features.bcm.BudgetLineItem.objects.filter(campaign_id=campaign.id)
        .select_related("credit")
        .order_by("-created_dt")
        .annotate_spend_data()
    )


def get_credit_items(campaign):
    return (
        core.features.bcm.CreditLineItem.objects.filter_by_account(campaign.account)
        .filter(currency=campaign.account.currency)
        .prefetch_related("budgets")
    )


def get_budgets_overview(user, campaign, active_budget_items, budget_items, credit_items):
    data = {
        "available_budgets_sum": Decimal("0.0000"),
        "unallocated_credit": Decimal("0.0000"),
        "campaign_spend": Decimal("0.0000"),
    }

    for item in active_budget_items:
        spend_data = item.get_local_spend_data()
        if campaign.account.uses_bcm_v2:
            spend = spend_data["etfm_total"]
        else:
            spend = spend_data["etf_total"]
        allocated = item.allocated_amount()
        data["available_budgets_sum"] += allocated - spend

    if should_add_platform_costs(user, campaign):
        data["media_spend"] = Decimal("0.0000")
        data["data_spend"] = Decimal("0.0000")
        data["license_fee"] = Decimal("0.0000")

    if should_add_agency_costs(user):
        data["margin"] = Decimal("0.0000")

    for item in credit_items:
        if item.status != dash.constants.CreditLineItemStatus.SIGNED or item.is_past():
            continue
        data["unallocated_credit"] += Decimal(item.amount - item.flat_fee() - item.get_allocated_amount())

    for item in budget_items:
        if item.state() == dash.constants.BudgetLineItemState.PENDING:
            continue

        spend_data = item.get_local_spend_data()

        if campaign.account.uses_bcm_v2:
            data["campaign_spend"] += spend_data["etfm_total"]
        else:
            data["campaign_spend"] += spend_data["etf_total"]

        if should_add_platform_costs(user, campaign):
            data["media_spend"] += spend_data["media"]
            data["data_spend"] += spend_data["data"]
            data["license_fee"] += spend_data["license_fee"]

        if should_add_agency_costs(user):
            data["margin"] += spend_data["margin"]

    return data


def should_add_platform_costs(user, campaign):
    return not campaign.account.uses_bcm_v2 or user.has_perm("zemauth.can_view_platform_cost_breakdown")


def should_add_agency_costs(user):
    return user.has_perm("zemauth.can_manage_agency_margin")


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
