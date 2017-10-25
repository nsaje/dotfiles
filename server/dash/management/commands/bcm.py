import sys
import datetime
import math

from django.db import connection, transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

import utils.converters
import utils.command_helpers
import dash.models
import dash.constants

MODEL_CREDITS = 'credits'
MODEL_BUDGETS = 'budgets'
MODELS = (
    MODEL_CREDITS,
    MODEL_BUDGETS,
)

ACTION_DELETE = 'delete'
ACTION_UPDATE = 'update'
ACTION_RELEASE = 'release'
ACTION_LIST = 'list'
ACTION_TRANSFER = 'transfer'
ACTION_SQUEEZE = 'squeeze'
ACTIONS = (
    ACTION_DELETE,
    ACTION_UPDATE,
    ACTION_RELEASE,
    ACTION_LIST,
    ACTION_TRANSFER,
    ACTION_SQUEEZE,
)
VALID_ACTIONS = {
    MODEL_CREDITS: (ACTION_DELETE, ACTION_UPDATE, ACTION_LIST, ACTION_SQUEEZE),
    MODEL_BUDGETS: (ACTION_DELETE, ACTION_UPDATE, ACTION_RELEASE, ACTION_LIST, ACTION_TRANSFER, ACTION_SQUEEZE),
}

CONSTRAINTS = {
    'credits': 'credit_id__in',
    'agencies': 'agency_id__in',
    'accounts': 'account_id__in',
    'campaigns': 'campaign_id__in',
}


UPDATABLE_FIELDS = {
    # GENERAL
    'amount': int,
    'start_date': str,
    'end_date': str,

    # CREDIT ONLY
    'license_fee': str,
    'flat_fee_cc': int,

    # BUDGET ONLY
    'credit_id': int,
    'margin': str,
    'freed_cc': int,
}

INVALIDATE_DAILY_STATEMENTS_FIELDS = ('license_fee', 'margin', )


class CommandError(Exception):
    pass


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
    cursor.execute("DELETE FROM dash_budgetdailystatement WHERE budget_id = %s;", [budget.pk])
    cursor.execute("DELETE FROM dash_budgetlineitem WHERE id = %s;", [budget.pk])


def _updates_to_sql(updates):
    sql, args = [], []
    for field, value in updates.iteritems():
        sql.append(field + ' = %s')
        args.append(value)
    return ', '.join(sql), args


class Command(BaseCommand):
    help = """Manage credits and budgets
    Usage: ./manage.py bcm list|update|delete|release|transfer budgets|credits ids [options]

    Options can be any fields that have to be updated.

    Special options (constraints):
      --credits - update budgets that belong to specified credits
      --campaigns - update budgets that belong to specified campaigns
      --accounts - update credits that belong to specified accounts
      --agency - update credits that belong to specified agencies
    All constraint values have to be comma separated list of ids.
    Example: --campaigns 1,2,3

    When transfering amounts from one credit to another, additional options are mandatory:
      --transfer-credit
      --transfer-amount
    """

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('action', nargs=1, choices=ACTIONS, type=str)
        parser.add_argument('model', nargs=1, choices=MODELS, type=str)
        parser.add_argument('ids', nargs='*', type=int)

        parser.add_argument('--credits', dest='credits', nargs='?', type=str)
        parser.add_argument('--campaigns', dest='campaigns', nargs='?', type=str)
        parser.add_argument('--accounts', dest='accounts', nargs='?', type=str)
        parser.add_argument('--agencies', dest='agencies', nargs='?', type=str)

        parser.add_argument('--transfer-credit', dest='transfer_credit', nargs='?',
                            type=int, help='Credit to which a transfer is made')
        parser.add_argument('--transfer-amount', dest='transfer_amount', nargs='?', type=int, help='Amount to transfer')

        parser.add_argument('--no-confirm', dest='no_confirm', action='store_true')
        parser.add_argument('--skip-spend-validation', dest='skip_spend_validation',
                            action='store_true')

        for field, field_type in UPDATABLE_FIELDS.iteritems():
            parser.add_argument('--' + field, dest=field, nargs='?', type=field_type)

    def _get_updates(self, options):
        updates = {}
        for field in UPDATABLE_FIELDS:
            value = options.get(field)
            if value is not None:
                updates[field] = value
        return updates

    def _validate(self, model, object_list, options):
        self._validate_dates(model, object_list)
        if model == MODEL_CREDITS:
            self._validate_credit_amounts(object_list)
        else:
            if not options.get('skip_spend_validation'):
                self._validate_budget_amounts(object_list)
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

    def _validate_budget_amounts(self, budget_list):
        for budget in budget_list:
            if budget.get_available_amount() < 0:
                raise ValidationError('Budget amount is lower than spend')

    def handle(self, **options):
        action = options['action'][0]
        model = options['model'][0]
        ids = options['ids']

        try:
            self._handle(action, model, ids, options)
        except CommandError as err:
            self.stderr.write('{}\n'.format(err))
            sys.exit(1)

    def _handle(self, action, model, ids, options):
        if action not in VALID_ACTIONS[model]:
            raise CommandError('Cannot manage {} with action {}'.format(model, action))

        object_list = self._get_objects(model, ids, options)
        if not object_list:
            raise CommandError('No matching {}'.format(model))

        self._print_object_list(action, model, object_list, list_only=action == ACTION_LIST)

        if action == ACTION_LIST:
            return

        if not options.get('no_confirm') and not self._confirm('Are you sure?'):
            self._print('Canceled.')
            return

        try:
            with transaction.atomic():
                self._handle_action(action, model, object_list, options)
        except ValidationError:
            raise CommandError('Validation failed.')
        except DatabaseError:
            raise CommandError('Wrong fields.')

    def _handle_action(self, action, model, object_list, options):
        need_confirm = not options.get('no_confirm')
        if action == ACTION_UPDATE:
            updates = self._get_updates(options)
            if not updates:
                raise CommandError('Nothing to change')
            if model == MODEL_CREDITS:
                update_credits(object_list, updates)
            else:
                update_budgets(object_list, updates)

            object_list = [type(obj).objects.get(pk=obj.pk) for obj in object_list]
            self._validate(model, object_list, options)

            for obj in object_list:
                obj.save()

            if set(updates.keys()) & set(INVALIDATE_DAILY_STATEMENTS_FIELDS):
                self._print('WARNING: Daily statements should be reprocessed')

        elif action == ACTION_DELETE:
            for obj in object_list:
                if model == MODEL_CREDITS:
                    delete_credit(obj)
                else:
                    delete_budget(obj)

        elif action == ACTION_RELEASE:
            for obj in object_list:
                if obj.freed_cc:
                    if need_confirm and self._confirm('Budget was already released. Do you want to clear it?'):
                        obj.freed_cc = 0
                try:
                    obj.free_inactive_allocated_assets()
                    self._print(
                        'Released {} from budget {}'.format(
                            obj.freed_cc * utils.converters.CC_TO_DECIMAL_DOLAR,
                            str(obj)
                        )
                    )
                except AssertionError:
                    raise CommandError('Could not free assets. Budget status is {}'.format(
                        obj.state_text()
                    ))

        elif action == ACTION_TRANSFER:
            if len(object_list) != 1:
                raise CommandError('You can transfer assets from one budget at a time only.')
            delta = options['transfer_amount']
            credit = dash.models.CreditLineItem.objects.get(pk=options['transfer_credit'])
            confirm_msg = 'You are transfering ${} from selected budget to credit item {}. Are you sure?'.format(
                delta, credit)
            if need_confirm and not self._confirm(confirm_msg):
                return
            new_budgets = []
            obj = object_list[0]
            with transaction.atomic():
                new_budgets.append(dash.models.BudgetLineItem.objects.create_unsafe(
                    amount=delta,
                    credit=credit,
                    start_date=obj.start_date,
                    end_date=obj.end_date,
                    campaign=obj.campaign,
                ))
                update_budgets([obj], {'amount': (obj.amount - delta)})
            self._print('New budget: ')
            self._print_object_list(action, model, new_budgets, list_only=True)
            self._print('WARNING: Daily statements have to be reprocessed')

        elif action == ACTION_SQUEEZE:
            with transaction.atomic():
                if model == MODEL_CREDITS:
                    for obj in object_list:
                        if obj.end_date >= datetime.date.today():
                            raise ValidationError('Not all credits are depleted')
                        update_credits([obj], {
                            'amount': int(math.ceil(obj.get_allocated_amount()))
                        })
                elif model == MODEL_BUDGETS:
                    for obj in object_list:
                        if obj.state() not in (dash.constants.BudgetLineItemState.DEPLETED,
                                               dash.constants.BudgetLineItemState.INACTIVE):
                            raise ValidationError('Not all budgets are depleted/inactive.')
                        update_budgets([obj], {
                            'amount': int(math.ceil(obj.allocated_amount())),
                            'freed_cc': 0,
                        })

    def _get_objects(self, model, ids, options):
        constraints = {}
        for opt in CONSTRAINTS:
            if opt not in options:
                continue
            value = utils.command_helpers.parse_id_list(options, opt)
            if value:
                constraints[CONSTRAINTS[opt]] = value
        if not constraints:
            constraints = {'pk__in': ids}
        objects = None
        if model == MODEL_CREDITS:
            objects = dash.models.CreditLineItem.objects
        elif model == MODEL_BUDGETS:
            objects = dash.models.BudgetLineItem.objects
        else:
            return None
        try:
            return objects.filter(**constraints).order_by('id')
        except Exception:
            raise CommandError('Invalid constraints')
            return None

    def _confirm(self, message):
        return raw_input('{} [yN] '.format(message)).lower() == 'y'

    def _print(self, msg):
        self.stdout.write('{}\n'.format(msg))

    def _print_object_list(self, action, model, object_list, list_only=False):
        if not list_only:
            self._print('You will {} the following {}:'.format(action, model))
        for budget in object_list if model == MODEL_BUDGETS else []:
            self._print_budget(budget)
        for credit in object_list if model == MODEL_CREDITS else []:
            self._print_credit(credit)

    def _print_budget(self, budget):
        self._print(' - #{} {}, {}, {} - {} (${}, freed ${}, margin {})'.format(
            budget.pk,
            budget.campaign.account,
            budget.campaign,
            budget.start_date,
            budget.end_date,
            budget.amount,
            utils.converters.CC_TO_DECIMAL_DOLAR * budget.freed_cc,
            budget.margin,
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
