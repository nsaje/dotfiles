def get_applied_deals_dict(configured_deals):
    exclusive_deals = []
    non_exclusive_deals = []
    for direct_deal in configured_deals:
        for deal in direct_deal.deals.all():
            deal_dto = _get_deal_dto(direct_deal, deal)
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


def _get_deal_dto(direct_deal, deal):
    return {
        "level": direct_deal.level,
        "direct_deal_connection_id": direct_deal.id,
        "deal_id": deal.deal_id,
        "source": direct_deal.source.name,
        "exclusive": direct_deal.exclusive,
        "description": deal.description,
        "is_applied": True,
    }
