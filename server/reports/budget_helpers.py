import datetime
from decimal import Decimal
from django.db.models import Sum


SHORT_NAME_MAX_LENGTH = 22
CC_TO_DEC_MULTIPLIER = Decimal('0.0001')
TO_CC_MULTIPLIER = 10**4
TO_NANO_MULTIPLIER = 10**9


def nano_to_cc(num):
    return int(round(num * 0.00001))


def nano_to_dec(num):
    return Decimal(nano_to_cc(num) * CC_TO_DEC_MULTIPLIER)


def calculate_mtd_spend_data(statements, date=None, use_decimal=False):
    '''
    Get month-to-date spend data
    '''
    spend_data = {
        'media_cc': 0,
        'data_cc': 0,
        'license_fee_cc': 0,
        'total_cc': 0,
    }

    if not date:
        date = datetime.datetime.utcnow()

    start_date = datetime.datetime(date.year, date.month, 1)
    statements = statements.filter(
        date__gte=start_date,
        date__lte=date
    )

    spend_data = {
        (key + '_cc'): nano_to_cc(spend or 0)
        for key, spend in statements.aggregate(
            media=Sum('media_spend_nano'),
            data=Sum('data_spend_nano'),
            license_fee=Sum('license_fee_nano'),
        ).iteritems()
    }
    spend_data['total_cc'] = sum(spend_data.values())
    if not use_decimal:
        return spend_data
    return {
        key[:-3]: Decimal(spend_data[key]) * CC_TO_DEC_MULTIPLIER
        for key in spend_data.keys()
    }


def calculate_spend_data(statements, date=None, use_decimal=False):
    spend_data = {
        'media_cc': 0,
        'data_cc': 0,
        'license_fee_cc': 0,
        'total_cc': 0,
    }
    if date:
       statements = statements.filter(date__lte=date)

    spend_data = {
        (key + '_cc'): nano_to_cc(spend or 0)
        for key, spend in statements.aggregate(
            media=Sum('media_spend_nano'),
            data=Sum('data_spend_nano'),
            license_fee=Sum('license_fee_nano'),
        ).iteritems()
    }
    spend_data['total_cc'] = sum(spend_data.values())
    if not use_decimal:
        return spend_data
    return {
        key[:-3]: Decimal(spend_data[key]) * CC_TO_DEC_MULTIPLIER
        for key in spend_data.keys()
    }


"""
def get_daily_spend(self, date, use_decimal=False):
    spend_data = {
        'media_cc': 0, 'data_cc': 0,
        'license_fee_cc': 0, 'total_cc': 0,
    }
    try:
        statement = date and self.statements.get(date=date)\
            or self.get_latest_statement()
    except ObjectDoesNotExist:
        pass
    else:
        spend_data['media_cc'] = nano_to_cc(statement.media_spend_nano)
        spend_data['data_cc'] = nano_to_cc(statement.data_spend_nano)
        spend_data['license_fee_cc'] = nano_to_cc(statement.license_fee_nano)
        spend_data['total_cc'] = nano_to_cc(
            statement.data_spend_nano + statement.media_spend_nano + statement.license_fee_nano
        )
    if not use_decimal:
        return spend_data
    return {
        key[:-3]: Decimal(spend_data[key]) * CC_TO_DEC_MULTIPLIER
        for key in spend_data.keys()
    }
"""
