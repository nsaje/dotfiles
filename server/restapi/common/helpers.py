import core.models
import zemauth.features.entity_permission.helpers
import zemauth.models
from zemauth.features.entity_permission import Permission


def get_applied_deals_dict(configured_deals):
    exclusive_deals = []
    non_exclusive_deals = []
    for direct_deal in configured_deals:
        deal_dto = _get_deal_dto(direct_deal)
        if deal_dto["exclusive"]:
            exclusive_deals.append(deal_dto)
        else:
            non_exclusive_deals.append(deal_dto)

    for exclusive_deal in exclusive_deals:
        for non_exclusive_deal in non_exclusive_deals:
            if (
                exclusive_deal["source"] == non_exclusive_deal["source"]
                and exclusive_deal["deal_id"] == non_exclusive_deal["deal_id"]
            ):
                non_exclusive_deal.update({"is_applied": False})

    return exclusive_deals + non_exclusive_deals


def get_users_for_manager(user, account, current_manager=None):
    users_queryset = None
    if user.has_perm("zemauth.can_see_all_users_for_managers"):
        users_queryset = zemauth.models.User.objects.all()
    else:
        if account.id is not None:
            queryset_user_permission = account.users.all()
            queryset_entity_permission = account.get_users_with(Permission.READ)
            queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
                user, Permission.READ, queryset_user_permission, queryset_entity_permission
            )
            users_queryset = queryset
        if account.is_agency():
            queryset_user_permission = account.agency.users.all()
            queryset_entity_permission = account.agency.get_users_with(Permission.READ)
            queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
                user, Permission.READ, queryset_user_permission, queryset_entity_permission
            )
            if users_queryset is not None:
                users_queryset |= queryset
            else:
                users_queryset = queryset

    if current_manager is not None:
        queryset = zemauth.models.User.objects.filter(pk=current_manager.id)
        if users_queryset is not None:
            users_queryset |= queryset
        else:
            users_queryset = queryset

    return users_queryset.filter(is_active=True).distinct() if users_queryset is not None else []


def get_user_full_name_or_email(user, default_value="/"):
    if user is None:
        return default_value

    result = user.get_full_name() or user.email
    return result


def _get_deal_dto(direct_deal):
    return {
        "level": direct_deal.level,
        "direct_deal_connection_id": direct_deal.id,
        "deal_id": direct_deal.deal.deal_id,
        "source": direct_deal.deal.source.name,
        "exclusive": direct_deal.exclusive,
        "description": direct_deal.deal.description,
        "is_applied": True,
    }


def get_available_sources(user, agency, account=None):
    show_all_sources = user.has_perm("zemauth.can_see_all_available_sources")
    available_sources_queryset = core.models.Source.objects.filter(deprecated=False)
    if show_all_sources:
        return list(available_sources_queryset)
    available_sources_queryset = available_sources_queryset.filter(released=True)
    if agency is not None and agency.available_sources.exists():
        available_sources_queryset = agency.available_sources.all()
    if account and account.id is not None:
        account_sources = account.allowed_sources.filter(released=True)
        return list({*available_sources_queryset, *account_sources})
    return list(available_sources_queryset)
