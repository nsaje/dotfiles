from decimal import Decimal

CC_TO_MICRO = 1E2
MICRO_TO_NANO = 1E3


def decimal_to_int(x):
    return int(round(x))


def micro_to_cc(x):
    return decimal_to_int(Decimal(x) / CC_TO_MICRO)