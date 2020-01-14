import decimal


def multiply_as_decimals(value_1, value_2, precision=decimal.Decimal("1.0000")):
    return (decimal.Decimal(value_1) * decimal.Decimal(value_2)).quantize(precision)


def equal_decimals(value_1, value_2, precision=decimal.Decimal("1.0000")):
    return abs(decimal.Decimal(value_1) - decimal.Decimal(value_2)).quantize(precision) == decimal.Decimal(
        "0"
    ).quantize(precision)
