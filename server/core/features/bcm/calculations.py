from decimal import Decimal

from utils import numbers

ZERO = Decimal("0.0000")


def calculate_min_bid_value(min_bid_value, bcm_modifiers):
    if not bcm_modifiers or not min_bid_value:
        return min_bid_value

    etfm_min_bid_value = apply_fees_and_margin(
        min_bid_value, bcm_modifiers["service_fee"], bcm_modifiers["fee"], bcm_modifiers["margin"]
    )
    rounded = numbers.round_decimal_ceiling(etfm_min_bid_value, places=3)
    return rounded


def calculate_max_bid_value(max_bid_value, bcm_modifiers):
    if not bcm_modifiers or not max_bid_value:
        return max_bid_value

    etfm_max_bid_value = apply_fees_and_margin(
        max_bid_value, bcm_modifiers["service_fee"], bcm_modifiers["fee"], bcm_modifiers["margin"]
    )
    rounded = numbers.round_decimal_floor(etfm_max_bid_value, places=3)
    return rounded


def calculate_min_daily_budget(min_daily_budget, bcm_modifiers):
    if not bcm_modifiers:
        return min_daily_budget

    etfm_min_daily_budget = apply_fees_and_margin(
        min_daily_budget, bcm_modifiers["service_fee"], bcm_modifiers["fee"], bcm_modifiers["margin"]
    )
    rounded = numbers.round_decimal_ceiling(etfm_min_daily_budget, places=0)
    return rounded


def calculate_max_daily_budget(max_daily_budget, bcm_modifiers):
    if not bcm_modifiers:
        return max_daily_budget

    etfm_max_daily_budget = apply_fees_and_margin(
        max_daily_budget, bcm_modifiers["service_fee"], bcm_modifiers["fee"], bcm_modifiers["margin"]
    )
    rounded = numbers.round_decimal_floor(etfm_max_daily_budget, places=0)
    return rounded


def apply_fees_and_margin(number, service_fee, license_fee, margin):
    return number / ((1 - (service_fee or ZERO)) * (1 - (license_fee or ZERO)) * (1 - (margin or ZERO)))


def apply_fee(number, fee):
    return number / (1 - (fee or ZERO))


def calculate_fees_and_margin(number, service_fee, license_fee, margin):
    return apply_fees_and_margin(number, service_fee, license_fee, margin) - number


def calculate_fee(number, fee):
    return apply_fee(number, fee) - number


def subtract_fees_and_margin(number, service_fee, license_fee, margin):
    return number * ((1 - (service_fee or ZERO)) * (1 - (license_fee or ZERO)) * (1 - (margin or ZERO)))
