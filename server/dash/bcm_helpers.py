import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import connection, transaction
from django.db.models import Q, Sum, F, DecimalField

import dash.models
import dash.constants
import reports.models

TWOPLACES = Decimal('0.01')
SPEND_PROJECTION_DAYS = 3


def _money_to_decimal(amount):
    return Decimal(amount.strip(' $').replace(',', ''))


def get_campaign_media_budget_data(campaign_ids):
    budget_data = dash.models.BudgetLineItem.objects.filter(
        campaign__id__in=campaign_ids,
        credit__status=dash.constants.CreditLineItemStatus.SIGNED
    ).values('campaign_id').order_by().annotate(
        media=Sum(
            F('amount') * (1 - F('credit__license_fee')),
            output_field=DecimalField(max_digits=10, decimal_places=4)
        )
    )
    media_spend_data = reports.models.BudgetDailyStatement.objects.filter(
        budget__campaign_id__in=campaign_ids
    ).values('budget__campaign_id').order_by().annotate(
        media_nano=Sum('media_spend_nano')
    )

    campaign_budget = {
        row['campaign_id']: row['media']
        for row in budget_data
    }
    campaign_spend = {
        row['budget__campaign_id']: dash.models.nano_to_dec(row['media_nano'])
        for row in media_spend_data
    }
    return campaign_budget, campaign_spend


def get_account_media_budget_data(account_ids):
    budget_data = dash.models.BudgetLineItem.objects.filter(
        credit__account__id__in=account_ids,
    ).values('credit__account_id').order_by().annotate(
        media=Sum(
            F('amount') * (1 - F('credit__license_fee')),
            output_field=DecimalField(max_digits=10, decimal_places=4)
        )
    )
    account_budget = {
        row['credit__account_id']: row['media']
        for row in budget_data
    }

    media_spend_data = reports.models.BudgetDailyStatement.objects.filter(
        budget__credit__account_id__in=account_ids
    ).values('budget__credit__account_id').order_by().annotate(
        media_nano=Sum('media_spend_nano')
    )
    account_spend = {
        row['budget__credit__account_id']: dash.models.nano_to_dec(row['media_nano'])
        for row in media_spend_data
    }

    return account_budget, account_spend


def get_projections(accounts, start_date, end_date):
    yesterday = datetime.date.today() - datetime.timedelta(1)
    projections = {
        'spend_projection': {
            acc.pk: Decimal('0.0') for acc in accounts
        },
        'credit_projection': {
            acc.pk: Decimal('0.0') for acc in accounts
        },
    }
    account_credits = dash.models.CreditLineItem.objects.filter(
        account__in=accounts,
        status=dash.constants.CreditLineItemStatus.SIGNED,
    ).exclude(
        Q(end_date__lt=start_date) | Q(start_date__gt=end_date)
    ).select_related('account')
    for credit in account_credits:
        credit_days = Decimal((credit.end_date - credit.start_date).days + 1)
        total = credit.get_allocated_amount()
        overlap = credit.get_overlap(start_date, end_date)
        overlap_days = Decimal(((overlap[1] - overlap[0]).days + 1))
        projections['credit_projection'][credit.account.pk] += (total / credit_days) * overlap_days

    reports.models.BudgetDailyStatement.objects.filter(budget__credit__in=account_credits)
    days = (end_date - start_date).days + 1
    spend_data = reports.models.BudgetDailyStatement.objects.filter(
        budget__credit__account__in=accounts,
        date__lte=min(end_date, yesterday),
        date__gte=min(end_date, yesterday) - datetime.timedelta(2)
    ).values('budget__credit__account_id').order_by().annotate(
        media_nano=Sum('media_spend_nano'),
        data_nano=Sum('data_spend_nano'),
        fee_nano=Sum('license_fee_nano'),
    )
    for spend in spend_data:
        account_id = spend['budget__credit__account_id']
        total_nano = spend['media_nano'] + spend['data_nano'] + spend['fee_nano']
        projections['spend_projection'][account_id] = min(
            (dash.models.nano_to_dec(total_nano) / Decimal(SPEND_PROJECTION_DAYS)) * days,
            projections['credit_projection'][account_id]
        )
    return projections


def clean_credit_input(account=None, valid_from=None, valid_to=None,
                       amount=None, license_fee=None, total_license_fee=None, notes=None):
    if account:
        account = int(account)
    if valid_from:
        valid_from = datetime.datetime.strptime(valid_from, "%m/%d/%Y").date()
    if valid_to:
        valid_to = datetime.datetime.strptime(valid_to, "%m/%d/%Y").date()
    else:
        valid_to = (valid_from + relativedelta(years=1))  # default 1y
    if amount:
        amount = int(round(_money_to_decimal(amount)))
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
