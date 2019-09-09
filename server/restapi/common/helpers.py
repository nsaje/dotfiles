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
    if user.has_perm("zemauth.can_see_all_users_for_managers"):
        users = zemauth.models.User.objects.all()
    else:
        users = account.users.all()
        if account.is_agency():
            users |= account.agency.users.all()

    if current_manager is not None:
        users |= zemauth.models.User.objects.filter(pk=current_manager.id)

    return users.filter(is_active=True).distinct()


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
        "source": direct_deal.source.name,
        "exclusive": direct_deal.exclusive,
        "description": direct_deal.deal.description,
        "is_applied": True,
    }
