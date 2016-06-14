import sys
import decimal

from django.db import connection, transaction, DatabaseError
from django.core.exceptions import ValidationError

import utils.command_helpers
import utils.converters
import dash.models

MODEL_CREDITS = 'credits'
MODEL_BUDGETS = 'budgets'
MODELS = (
    MODEL_CREDITS,
    MODEL_BUDGETS,
)

UPDATABLE_FIELDS = {
    'amount': int,
    'start_date': str,
    'end_date': str,
    'license_fee': str,
    'flat_fee_cc': int,
    'freed_cc': int,
}

INVALIDATE_DAILY_STATEMENTS_FIELDS = ('license_fee', )


@transaction.atomic
def update_credits(object_list, updates):
    cursor = connection.cursor()
    set_sql, values = _updates_to_sql(updates)
    cursor.execute('UPDATE dash_creditlineitem SET {} WHERE id in ({});'.format(
        set_sql,
        ', '.join(str(c.pk) for c in object_list)
    ), values)


@transaction.atomic
def update_budgets(object_list, updates):
    cursor = connection.cursor()
    set_sql, values = _updates_to_sql(updates)
    cursor.execute('UPDATE dash_budgetlineitem SET {} WHERE id in ({});'.format(
        set_sql,
        ', '.join(str(b.pk) for b in object_list)
    ), values)


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


def _updates_to_sql(updates):
    sql, args = '', []
    for field, value in updates.iteritems():
        sql += field + ' = %s'
        args.append(value)
    return sql, args


class Command(utils.command_helpers.ExceptionCommand):
    help = """Manage credits and budgets
    Usage: ./manage.py bcm update|delete budgets|credits ids [options]

    Options can be any fields that have to be updated.
    Special option is --credits - update budgets that belong to specified credits
    """

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('action', nargs=1, choices=('update', 'delete'), type=str)
        parser.add_argument('model', nargs=1, choices=MODELS, type=str)
        parser.add_argument('ids', nargs='*', type=int)

        parser.add_argument('--credits', dest='credit', nargs='*', type=int)
        parser.add_argument('--no-confirm', dest='no_confirm', action='store_true')

        for field, field_type in UPDATABLE_FIELDS.iteritems():
            parser.add_argument('--' + field, dest=field, nargs='?', type=field_type)

    def _get_updates(self, options):
        updates = {}
        for field in UPDATABLE_FIELDS:
            value = options.get(field)
            if value:
                updates[field] = value
        return updates

    def _validate(self, model, object_list):
        self._validate_dates(model, object_list)
        if model == MODEL_CREDITS:
            self._validate_credit_amounts(object_list)
        else:
            self._validate_credit_amounts(set([
                obj.credit for obj in object_list
            ]))

    def _validate_dates(self, model, object_list):
        for obj in object_list:
            if obj.start_date > obj.end_date:
                raise ValidationError('Start date cannot be bigger than end date')

        if model == MODEL_CREDITS:
            for obj in object_list:
                for budget in obj.budgets.all():
                    if budget.start_date < obj.start_date:
                        raise ValidationError(
                            'Budget start date cannot be smaller than credit\'s end date'
                        )
                    if budget.end_date > obj.end_date:
                        raise ValidationError(
                            'Budget end date cannot be bigger than the credit\'s end date'
                        )

    def _validate_credit_amounts(self, credit_list):
        for credit in credit_list:
            if credit.amount < credit.get_allocated_amount():
                raise ValidationError('Amounts in budgets don\'t match credit\'s')

    def handle(self, **options):
        action = options['action'][0]
        model = options['model'][0]
        ids = options['ids']

        object_list = self._get_objects(model, ids, credit_ids=options.get('credit'))
        if not object_list:
            self._error('No matching {}'.format(model))

        self._print_object_list(action, model, object_list)

        if not options.get('no_confirm') and not self._confirm('Are you sure?'):
            self._print('Canceled.')
            return

        try:
            with transaction.atomic():
                self._handle_action(action, model, object_list, options)
        except ValidationError:
            self._error('Validation failed.')
        except DatabaseError:
            self._error('Wrong fields.')

    def _handle_action(self, action, model, object_list, options):
        if action == 'update':
            updates = self._get_updates(options)
            if not updates:
                self._error('Nothing to change')
            if model == MODEL_CREDITS:
                update_credits(object_list, updates)
            else:
                update_budgets(object_list, updates)

            object_list = [type(obj).objects.get(pk=obj.pk) for obj in object_list]
            self._validate(model, object_list)

            for obj in object_list:
                obj.save()

            if set(updates.keys()) & set(INVALIDATE_DAILY_STATEMENTS_FIELDS):
                self._print('WARNING: Daily statements should be reprocessed')

        elif action == 'delete':
            for obj in object_list:
                if model == MODEL_CREDITS:
                    delete_credit(obj)
                else:
                    delete_budget(obj)

    def _get_objects(self, model, ids, credit_ids=None):
        if model == MODEL_CREDITS:
            return dash.models.CreditLineItem.objects.filter(pk__in=ids)
        elif model == MODEL_BUDGETS:
            if credit_ids:
                return dash.models.BudgetLineItem.objects.filter(
                    credit_id__in=credit_ids,
                )
            else:
                return dash.models.BudgetLineItem.objects.filter(
                    pk__in=ids
                )
        return None

    def _confirm(self, message):
        return raw_input('{} [yN] '.format(message)).lower() == 'y'

    def _print(self, msg):
        self.stdout.write('{}\n'.format(msg))

    def _error(self, msg):
        self.stderr.write('{}\n'.format(msg))
        sys.exit(1)

    def _print_object_list(self, action, model, object_list):
        self._print('You will {} the following {}:'.format(action, model))
        for budget in object_list if model == MODEL_BUDGETS else []:
            self._print_budget(budget)
        for credit in object_list if model == MODEL_CREDITS else []:
            self._print_credit(credit)

    def _print_budget(self, budget):
        self._print(' - #{} {}, {}, {} - {} (${}, freed ${})'.format(
            budget.pk,
            budget.campaign.account,
            budget.campaign,
            budget.start_date,
            budget.end_date,
            budget.amount,
            utils.converters.CC_TO_DECIMAL_DOLAR * budget.freed_cc
        ))

    def _print_credit(self, credit):
        self._print(' - #{} {}{}, {} - {} (${}, fee {}%, flat ${})'.format(
            credit.pk,
            credit.agency or credit.account,
            ' (agency)' if credit.agency else '',
            credit.start_date,
            credit.end_date,
            credit.amount,
            credit.license_fee,
            utils.converters.CC_TO_DECIMAL_DOLAR * credit.flat_fee_cc
        ))
