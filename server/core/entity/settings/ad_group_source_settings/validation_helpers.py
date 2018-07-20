from decimal import Decimal

from core import source

from . import exceptions


def validate_daily_budget_cc(daily_budget_cc, source_type, bcm_modifiers=None):
    if daily_budget_cc < 0:
        raise exceptions.DailyBudgetNegative("Daily budget must be positive.")

    min_daily_budget = source_type.get_etfm_min_daily_budget(bcm_modifiers)
    _validate_min_daily_budget(daily_budget_cc, min_daily_budget)

    max_daily_budget = source_type.get_etfm_max_daily_budget(bcm_modifiers)
    _validate_max_daily_budget(daily_budget_cc, max_daily_budget)


def validate_source_cpc_cc(cpc_cc, source, source_type, bcm_modifiers=None):
    if cpc_cc < 0:
        raise exceptions.CPCNegative("CPC must be positive.")

    decimal_places = source_type.cpc_decimal_places
    _validate_cpc_decimal_places(cpc_cc, decimal_places, source.name)

    min_cpc = source_type.get_etfm_min_cpc(bcm_modifiers)
    _validate_min_cpc(cpc_cc, min_cpc, source.name)

    max_cpc = source_type.get_etfm_max_cpc(bcm_modifiers)
    _validate_max_cpc(cpc_cc, max_cpc, source.name)


def validate_ad_group_source_cpc_cc(cpc_cc, ad_group_source, bcm_modifiers=None):
    ad_group_settings = ad_group_source.ad_group.get_current_settings()

    source_type = ad_group_source.source.source_type
    validate_source_cpc_cc(cpc_cc, ad_group_source.source, source_type, bcm_modifiers=bcm_modifiers)

    min_cpc = source_type.get_min_cpc(ad_group_settings, bcm_modifiers)
    _validate_min_cpc(cpc_cc, min_cpc, ad_group_source.source.name)

    max_cpc = ad_group_settings.cpc_cc  # NOTE: no need to apply bcm_modifiers, not an external setting
    _validate_max_cpc(cpc_cc, max_cpc, "ad group")


def validate_b1_sources_group_cpc_cc(cpc_cc, ad_group_settings, bcm_modifiers=None):
    if not ad_group_settings.b1_sources_group_enabled:
        return

    if cpc_cc < 0:
        raise exceptions.RTBSourcesCPCNegative("RTB Sources' bid CPC must be positive.")

    validate_source_cpc_cc(cpc_cc, source.AllRTBSource, source.AllRTBSourceType, bcm_modifiers)

    ad_group_max_cpc = ad_group_settings.cpc_cc  # NOTE: no need to apply bcm_modifiers, not an external setting
    _validate_max_cpc(cpc_cc, ad_group_max_cpc, "ad group")


def validate_b1_sources_group_daily_budget(daily_budget, ad_group_settings, bcm_modifiers):
    if not ad_group_settings.b1_sources_group_enabled:
        return

    validate_daily_budget_cc(daily_budget, source.AllRTBSourceType, bcm_modifiers)


def _validate_cpc_decimal_places(cpc_cc, decimal_places, source_name):
    if decimal_places is not None and _has_too_many_decimal_places(cpc_cc, decimal_places):
        raise exceptions.CPCPrecisionExceeded(
            "CPC precision exceeded.", data={"source_name": source_name, "value": decimal_places}
        )


def _has_too_many_decimal_places(num, decimal_places):
    rounded_num = num.quantize(Decimal("1.{}".format("0" * decimal_places)))
    return rounded_num != num


def _validate_min_cpc(cpc_cc, min_cpc, source_name):
    if min_cpc is not None and cpc_cc < min_cpc:
        raise exceptions.MinimalCPCTooLow(
            "Minimum CPC is too low.", data={"source_name": source_name, "value": min_cpc}
        )


def _validate_max_cpc(cpc_cc, max_cpc, source_name):
    if max_cpc is not None and cpc_cc > max_cpc:
        raise exceptions.MaximalCPCTooHigh("Maximum CPC too high.", data={"source_name": source_name, "value": max_cpc})


def _validate_min_daily_budget(daily_budget, min_daily_budget):
    if min_daily_budget is not None and daily_budget < min_daily_budget:
        raise exceptions.MinimalDailyBudgetTooLow("Daily spend cap too low.", data={"value": min_daily_budget})


def _validate_max_daily_budget(daily_budget, max_daily_budget):
    if max_daily_budget is not None and daily_budget > max_daily_budget:
        raise exceptions.MaximalDailyBudgetTooHigh("Daily spend cap too high.", data={"value": max_daily_budget})
