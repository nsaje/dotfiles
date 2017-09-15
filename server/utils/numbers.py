import decimal


def round_decimal_floor(number):
    return number.quantize(decimal.Decimal('1'), decimal.ROUND_FLOOR)


def round_decimal_half_down(number, places=2):
    exp = decimal.Decimal('10') ** -places
    return number.quantize(exp, decimal.ROUND_HALF_DOWN)
