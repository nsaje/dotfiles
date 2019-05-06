from decimal import Decimal

CC_TO_MICRO = 10 ** 2
CC_TO_NANO = 10 ** 5
MICRO_TO_NANO = 10 ** 3
CURRENCY_TO_CC = 10 ** 4
CURRENCY_TO_MICRO = 10 ** 6
CURRENCY_TO_NANO = 10 ** 9

CC_TO_DECIMAL_CURRENCY = Decimal("0.0001")


def decimal_to_int(num):
    return int(round(num or 0))


def micro_to_cc(num):
    return decimal_to_int(Decimal(num or 0) / CC_TO_MICRO)


def nano_to_cc(num):
    return int(round((num or 0) * 0.00001))


def nano_to_decimal(num):
    return Decimal(nano_to_cc(num) * CC_TO_DECIMAL_CURRENCY)


def cc_to_decimal(val_cc):
    if val_cc is None:
        return None
    return Decimal(val_cc) / 10000


def x_to_bool(x):
    if isinstance(x, str):
        return x.lower() in ["true", "t", "1"]
    return bool(x)
