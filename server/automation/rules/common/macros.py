import decimal
import re
from typing import Any
from typing import Dict

import core.features.multicurrency
import core.models

from .. import config
from .. import constants
from .. import exceptions

EMAIL_CONTAINS_NESTED_MACRO_REGEX = re.compile(r"{[^}]*{")
EMAIL_EXTRACT_MACROS_REGEX = re.compile(r"{([^}]*)}")
EMAIL_MACRO_SPLIT_WINDOW_REGEX = re.compile(r"(.*)_(LAST_(?:\d+_)?DAYS?)$")

CURRENCY_MACROS = [
    constants.EmailActionMacro.TOTAL_SPEND,
    constants.EmailActionMacro.AVG_CPC,
    constants.EmailActionMacro.AVG_CPM,
    constants.EmailActionMacro.AVG_TIME_ON_SITE,
    constants.EmailActionMacro.AVG_COST_PER_VISIT,
    constants.EmailActionMacro.AVG_COST_PER_NEW_VISITOR,
    constants.EmailActionMacro.AVG_COST_PER_PAGEVIEW,
    constants.EmailActionMacro.AVG_COST_PER_NON_BOUNCED_VISIT,
    constants.EmailActionMacro.AVG_COST_PER_MINUTE,
    constants.EmailActionMacro.AVG_COST_PER_UNIQUE_USER,
    constants.EmailActionMacro.AVG_CPV,
    constants.EmailActionMacro.AVG_CPCV,
    constants.EmailActionMacro.MRC50_VCPM,
]
PERCENT_MACROS = [constants.EmailActionMacro.PERCENT_NEW_USERS]


def validate(content) -> None:
    if EMAIL_CONTAINS_NESTED_MACRO_REGEX.search(content):
        raise exceptions.InvalidMacros(f"Nested macros not supported.")
    invalid_macros = []
    for macro in EMAIL_EXTRACT_MACROS_REGEX.findall(content):
        if not _is_valid(macro):
            invalid_macros.append(macro)
    if invalid_macros:
        raise exceptions.InvalidMacros(
            "Unknown macro{}: {}.".format("s" if len(invalid_macros) > 1 else "", ", ".join(invalid_macros))
        )


def _is_valid(macro):
    if macro in config.EMAIL_ACTION_SETTINGS_MACROS:
        return True
    postfix_window_match = EMAIL_MACRO_SPLIT_WINDOW_REGEX.match(macro)
    if postfix_window_match and postfix_window_match.group(1) in config.EMAIL_ACTION_STATS_MACROS:
        return True
    return False


def expand(content: str, ad_group: core.models.AdGroup, target_stats: Dict[str, Dict[int, Any]]) -> str:
    account_currency = ad_group.campaign.account.currency
    for macro in set(EMAIL_EXTRACT_MACROS_REGEX.findall(content)):
        value = _get_macro_value(macro, ad_group, account_currency, target_stats)
        content = content.replace("{" + macro + "}", str(value))
    return content


def _get_macro_value(macro, ad_group, currency, target_stats):
    postfix_window_match = EMAIL_MACRO_SPLIT_WINDOW_REGEX.match(macro)
    if postfix_window_match:
        return _get_stat_macro_value(*postfix_window_match.groups(), currency, target_stats)
    elif macro == constants.EmailActionMacro.AD_GROUP_DAILY_CAP:
        return _get_ad_group_daily_cap_macro_value(ad_group, currency)
    elif macro == constants.EmailActionMacro.CAMPAIGN_BUDGET:
        return _get_campaign_budget_macro_value(ad_group, currency)
    elif macro == constants.EmailActionMacro.AGENCY_ID:
        return ad_group.campaign.account.agency_id
    elif macro == constants.EmailActionMacro.AGENCY_NAME:
        return ad_group.campaign.account.agency.name
    elif macro == constants.EmailActionMacro.ACCOUNT_ID:
        return ad_group.campaign.account_id
    elif macro == constants.EmailActionMacro.ACCOUNT_NAME:
        return ad_group.campaign.account.name
    elif macro == constants.EmailActionMacro.CAMPAIGN_ID:
        return ad_group.campaign_id
    elif macro == constants.EmailActionMacro.CAMPAIGN_NAME:
        return ad_group.campaign.name
    elif macro == constants.EmailActionMacro.AD_GROUP_ID:
        return ad_group.id
    elif macro == constants.EmailActionMacro.AD_GROUP_NAME:
        return ad_group.name
    else:
        raise exceptions.InvalidMacros("Invalid macro: %s" % macro)


def _get_stat_macro_value(macro_prefix: str, window: str, currency, target_stats: Dict[str, Dict[int, Any]]):
    stat_type = constants.EMAIL_MACRO_METRIC_TYPE_MAPPING[macro_prefix]
    stat_key = constants.METRIC_STATS_MAPPING[stat_type]

    window_constant_value = constants.MetricWindow.get_constant_value(window)
    macro_stat = target_stats[stat_key].get(window_constant_value)
    if macro_stat is None:
        macro_stat = config.STATS_FIELDS_DEFAULTS[stat_type]

    if macro_prefix in CURRENCY_MACROS and macro_stat is not None:
        value = core.features.multicurrency.format_value_in_currency(
            macro_stat, places=2, rounding=decimal.ROUND_HALF_DOWN, currency=currency
        )
    elif macro_prefix in PERCENT_MACROS and macro_stat is not None:
        value = "{:.2f}%".format(macro_stat)
    elif macro_stat is None:
        value = "N/A"
    else:
        value = str(macro_stat)

    return value


def _get_ad_group_daily_cap_macro_value(ad_group, currency):
    local_daily_cap = ad_group.compute_local_daily_cap()
    return core.features.multicurrency.format_value_in_currency(
        local_daily_cap, places=2, rounding=decimal.ROUND_HALF_DOWN, currency=currency
    )


def _get_campaign_budget_macro_value(ad_group, currency):
    active_budget_line_items = ad_group.campaign.budgets.all().filter_today()
    total_amount = sum(budget.amount for budget in active_budget_line_items)
    return core.features.multicurrency.format_value_in_currency(
        total_amount, places=2, rounding=decimal.ROUND_HALF_DOWN, currency=currency
    )
