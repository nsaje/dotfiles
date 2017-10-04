import decimal


def round_decimal_floor(number, places=2):
    return _round(number, places, decimal.ROUND_FLOOR)


def round_decimal_ceiling(number, places=2):
    return _round(number, places, decimal.ROUND_CEILING)


def round_decimal_half_down(number, places=2):
    return _round(number, places, decimal.ROUND_HALF_DOWN)


def _round(number, places, rounding):
    exp = decimal.Decimal('10') ** -places
    return number.quantize(exp, rounding)
