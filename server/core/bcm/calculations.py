from decimal import Decimal

ZERO = Decimal('0.0000')


def apply_fee_and_margin(number, license_fee, margin):
    return Decimal(number) / ((1 - (license_fee or ZERO)) * (1 - (margin or ZERO)))


def apply_fee(number, license_fee):
    return Decimal(number) / (1 - (license_fee or ZERO))


def apply_margin(number, margin):
    return Decimal(number) / (1 - (margin or ZERO))
