from dash import constants


def get_source_min_max_cpc(states):
    bid_cpc_values = [s.cpc_cc for s in states if s.cpc_cc is not None and
                      s.state == constants.AdGroupSourceSettingsState.ACTIVE]

    return {
        'min_bid_cpc': float(min(bid_cpc_values)) if bid_cpc_values else None,
        'max_bid_cpc': float(max(bid_cpc_values)) if bid_cpc_values else None,
    }


def get_daily_budget_total(states):
    budgets = [s.daily_budget_cc for s in states if
               s is not None and s.daily_budget_cc is not None and
               s.state == constants.AdGroupSourceSettingsState.ACTIVE]

    if not budgets:
        return None

    return sum(budgets)


def campaign_has_available_budget(campaign):
    return campaign.budgets.all().filter_active().exists()
