import datetime
from decimal import Decimal

from django.conf import settings
from django.core import exceptions as exc

import dash.models
import reports.models
import dash.constants
from utils import dates_helper

def nano_to_cc(num):
    return int(round(num / 100000))

def free_inactive_allocated_assets(budget):
    if budget.state() != dash.constants.BudgetLineItemState.INACTIVE:
        raise AssertionError('Budget has to be inactive to be freed.')
    amount_cc = budget.amount * 10000
    spend_data = get_spend_data(budget, date=dates_helper.local_today())
    if amount_cc <= spend_data['total_cc']:
        budget.is_depleted = True
    elif budget.freed_cc:
        # After we completed all syncs, free all the assets including reserve
        free_date = budget.end_date - datetime.timedelta(days=settings.LAST_N_DAY_REPORTS)
        if dates_helper.local_today() > free_date:
            budget.freed_cc = max(0, amount_cc - spend_data['total_cc'])
    else:
        budget.freed_cc = max(
            amount_cc - spend_data['total_cc'] - get_reserve_amount_cc(budget), 0
        )
    budget.save()

def get_reserve_amount_cc(budget, date=None):
    spend_data = get_spend_data(budget)
    return spend_data['total_cc'] * settings.BUDGET_RESERVE_FACTOR

def get_yesterday_spend(budget, date=None):
    if date is None:
        date = dates_helper.local_today()
    return get_spend_data(budget, date=date-datetime.timedelta(days=1))

def get_spend_data(budget, date=None):
    spend_data = {
        'media_cc': 0,
        'data_cc': 0,
        'license_fee_cc': 0,
        'total_cc': 0,
    }
    try:
        statement_objects = reports.models.BudgetDailyStatement.objects
        statement = date and statement_objects.get(budget=budget, date=date)\
                    or statement_objects.filter(budget=budget).order_by('-date')[0]
    except IndexError:
        pass
    except exc.ObjectDoesNotExist:
        pass
    else:
        spend_data['media_cc'] = nano_to_cc(statement.media_spend_nano)
        spend_data['data_cc'] = nano_to_cc(statement.data_spend_nano)
        spend_data['license_fee'] = nano_to_cc(statement.license_fee_nano)
        spend_data['total_cc'] = nano_to_cc(
            statement.data_spend_nano + statement.media_spend_nano + statement.license_fee_nano
        )
    for key in spend_data.keys():
        spend_data[key[:-3]] = Decimal(spend_data[key]) * Decimal('0.0001')
    return spend_data

