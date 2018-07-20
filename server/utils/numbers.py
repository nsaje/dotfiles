import decimal
from math import log10, floor


def round_decimal_floor(number, places=2):
    return _round(number, places, decimal.ROUND_FLOOR)


def round_decimal_ceiling(number, places=2):
    return _round(number, places, decimal.ROUND_CEILING)


def round_decimal_half_down(number, places=2):
    return _round(number, places, decimal.ROUND_HALF_DOWN)


def round_to_significant_figures(number, sig):
    significant_figures = sig - int(floor(log10(abs(number)))) - 1
    return round(number, significant_figures)


def _round(number, places, rounding):
    exp = decimal.Decimal("10") ** -places
    return number.quantize(exp, rounding)
