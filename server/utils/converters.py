from decimal import Decimal

CC_TO_MICRO = int(1E2)
CC_TO_NANO = int(1E5)
MICRO_TO_NANO = int(1E3)
DOLAR_TO_NANO = int(1E9)


def decimal_to_int(x):
    return int(round(x))


def micro_to_cc(x):
    return decimal_to_int(Decimal(x) / CC_TO_MICRO)
