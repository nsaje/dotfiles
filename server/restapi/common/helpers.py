import core.models
import zemauth.models


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
            users_queryset = account.users.all()
        if account.is_agency():
            if users_queryset is not None:
                users_queryset |= account.agency.users.all()
            else:
                users_queryset = account.agency.users.all()

    if current_manager is not None:
        if users_queryset is not None:
            users_queryset |= zemauth.models.User.objects.filter(pk=current_manager.id)
        else:
            users_queryset = zemauth.models.User.objects.filter(pk=current_manager.id)

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


def get_available_sources(user, agency):
    available_sources_queryset = core.models.Source.objects.all()
    if agency is not None and agency.allowed_sources.count() > 0:
        available_sources_queryset = agency.allowed_sources.all()
    if not user.has_perm("zemauth.can_see_all_available_sources"):
        available_sources_queryset = available_sources_queryset.filter(released=True, deprecated=False)
    return list(available_sources_queryset)
