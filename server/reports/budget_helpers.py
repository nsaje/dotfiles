import datetime
from decimal import Decimal
from django.db.models import Sum


CC_TO_DEC_MULTIPLIER = Decimal('0.0001')


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
    '''
    Calculate spend data given the relevant statements
    '''
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
