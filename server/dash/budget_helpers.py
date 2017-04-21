import datetime
from decimal import Decimal
from django.db.models import Sum

from utils import converters

TOTALS_FIELDS = ['media_cc', 'data_cc', 'license_fee_cc']


def calculate_mtd_spend_data(statements, date=None, use_decimal=False):
    '''
    Get month-to-date spend data
    returns a dict with the following structure
    {
        'media_cc': 0,
        'data_cc': 0,
        'license_fee_cc': 0,
        'total_cc': 0,
    }
    '''

    if not date:
        date = datetime.datetime.utcnow()

    start_date = datetime.datetime(date.year, date.month, 1)
    statements = statements.filter(
        date__gte=start_date,
        date__lte=date
    )

    spend_data = {
        (key + '_cc'): converters.nano_to_cc(spend or 0)
        for key, spend in statements.aggregate(
            media=Sum('media_spend_nano'),
            data=Sum('data_spend_nano'),
            license_fee=Sum('license_fee_nano'),
            margin=Sum('margin_nano'),
        ).iteritems()
    }
    spend_data['total_cc'] = sum(spend_data[field] for field in TOTALS_FIELDS)
    if not use_decimal:
        return spend_data
    return {
        key[:-3]: Decimal(spend_data[key]) * converters.CC_TO_DECIMAL_DOLAR
        for key in spend_data.keys()
    }


def calculate_spend_data(statements, date=None, use_decimal=False):
    '''
    Calculate spend data given the relevant statements
    returns a dict with the following structure
    {
        'media_cc': 0,
        'data_cc': 0,
        'license_fee_cc': 0,
        'total_cc': 0,
    }
    '''
    if date:
        statements = statements.filter(date__lte=date)

    spend_data = {
        (key + '_cc'): converters.nano_to_cc(spend or 0)
        for key, spend in statements.aggregate(
            media=Sum('media_spend_nano'),
            data=Sum('data_spend_nano'),
            license_fee=Sum('license_fee_nano'),
            margin=Sum('margin_nano'),
        ).iteritems()
    }
    spend_data['total_cc'] = sum(spend_data[field] for field in TOTALS_FIELDS)
    if not use_decimal:
        return spend_data
    return {
        key[:-3]: Decimal(spend_data[key]) * converters.CC_TO_DECIMAL_DOLAR
        for key in spend_data.keys()
    }
