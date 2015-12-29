import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import connection, transaction

import dash.models
import dash.constants

TWOPLACES = Decimal('0.01')

def _money_to_decimal(amount):
    return Decimal(amount.strip(' $').replace(',', ''))

def clean_credit_input(account=None, valid_from=None, valid_to=None,
                       amount=None, license_fee=None, total_license_fee=None, notes=None):
    if account:
        account = int(account)
    if valid_from:
        valid_from = datetime.datetime.strptime(valid_from, "%m/%d/%Y").date()
    if valid_to:
        valid_to = datetime.datetime.strptime(valid_to, "%m/%d/%Y").date()
    else:
        valid_to = (valid_from + relativedelta(years=1)) # default 1y
    if amount:
        amount = int(_money_to_decimal(amount))
    if license_fee:
        if '%' in license_fee:
            license_fee = Decimal(license_fee.strip('%')) * Decimal('0.01')
        else:
            license_fee = Decimal(license_fee)
    elif total_license_fee:
        license_fee = (_money_to_decimal(total_license_fee) / Decimal(amount)).quantize(TWOPLACES)
    if notes:
        notes = notes.strip()
    else:
        notes = ''
    return account, valid_from, valid_to, amount, license_fee, notes

def import_credit(account_id, valid_from, valid_to, amount, license_fee, note):
    """
    Import credit item
    """
    return dash.models.CreditLineItem.objects.create(
        account_id=account_id,
        start_date=valid_from,
        end_date=valid_to,
        amount=amount,
        license_fee=license_fee,
        comment=note,
        status=dash.constants.CreditLineItemStatus.SIGNED
    )

@transaction.atomic
def delete_credit(credit):
    """
    Completely delete credit from z1.
    The operation is not allowed via models.
    """
    for budget in credit.budgets.all():
        _delete_budget_traces(budget)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM dash_credithistory WHERE credit_id = %s;", [credit.pk])
    cursor.execute("DELETE FROM dash_creditlineitem WHERE id = %s;", [credit.pk])

@transaction.atomic
def delete_budget(budget):
    """
    Completely delete budget from z1.
    The operation is not allowed via models.
    """
    _delete_budget_traces(budget)

def _delete_budget_traces(budget):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM dash_budgethistory WHERE budget_id = %s;", [budget.pk])
    cursor.execute("DELETE FROM reports_budgetdailystatement WHERE budget_id = %s;", [budget.pk])
    cursor.execute("DELETE FROM dash_budgetlineitem WHERE id = %s;", [budget.pk])
    
