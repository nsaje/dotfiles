# -*- coding: utf-8 -*-

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import model_to_dict
from django.db.models import Q

import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from utils import converters
from utils import dates_helper
from utils import lc_helper

import core.common
import core.history


class CreditLineItemManager(core.common.QuerySetManager):

    def create(self, request, start_date, end_date, amount, **kwargs):
        cli = CreditLineItem(
            start_date=start_date,
            end_date=end_date,
            amount=amount,
            **kwargs
        )
        cli.created_by = request.user
        cli.save()
        return cli


class CreditLineItem(core.common.FootprintModel, core.history.HistoryMixinOld):

    class Meta:
        app_label = 'dash'

    history_fields = [
        'start_date',
        'end_date',
        'amount',
        'license_fee',
        'flat_fee_cc',
        'flat_fee_start_date',
        'flat_fee_end_date',
        'status',
        'comment'
    ]

    _demo_fields = {
        'comment': utils.demo_anonymizer.fake_io,
    }
    account = models.ForeignKey('Account', related_name='credits', on_delete=models.PROTECT, blank=True, null=True)
    agency = models.ForeignKey('Agency', related_name='credits', on_delete=models.PROTECT, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()

    amount = models.IntegerField()
    license_fee = models.DecimalField(
        decimal_places=4,
        max_digits=5,
        default=Decimal('0.2000'),
    )

    flat_fee_cc = models.IntegerField(default=0, verbose_name='Flat fee (cc)')
    flat_fee_start_date = models.DateField(blank=True, null=True)
    flat_fee_end_date = models.DateField(blank=True, null=True)

    # Salesforce integration
    contract_id = models.CharField(max_length=256, blank=True, null=True, verbose_name='SalesForce Contract ID')
    contract_number = models.CharField(max_length=256, blank=True, null=True, verbose_name='SalesForce Contract Number')

    status = models.IntegerField(
        default=constants.CreditLineItemStatus.PENDING,
        choices=constants.CreditLineItemStatus.get_choices()
    )
    refund = models.BooleanField(null=False, blank=False, default=False)
    comment = models.CharField(max_length=256, blank=True, null=True)
    special_terms = models.CharField(max_length=256, blank=True, null=True)

    currency = models.CharField(
        max_length=3,
        default=constants.Currency.USD,
        choices=constants.Currency.get_choices(),
    )

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)

    def is_active(self, date=None):
        if date is None:
            date = dates_helper.local_today()
        return self.status == constants.CreditLineItemStatus.SIGNED and \
            (self.start_date <= date <= self.end_date)

    def is_past(self, date=None):
        if date is None:
            date = dates_helper.local_today()
        return self.end_date < date

    def get_allocated_amount(self):
        return Decimal(sum(b.allocated_amount() for b in self.budgets.all()))

    def get_overlap(self, start_date, end_date):
        return dates_helper.get_overlap(self.start_date, self.end_date, start_date, end_date)

    def get_monthly_flat_fee(self):
        months = dates_helper.count_months(
            self.flat_fee_start_date,
            self.flat_fee_end_date
        ) + 1
        return self.flat_fee() / Decimal(months)

    def get_flat_fee_on_date_range(self, start_date, end_date):
        if not (self.flat_fee_start_date and self.flat_fee_end_date):
            return Decimal('0.0')
        overlap = dates_helper.get_overlap(
            self.flat_fee_start_date, self.flat_fee_end_date,
            start_date, end_date
        )
        if not all(overlap):
            return Decimal('0.0')
        effective_months = dates_helper.count_months(*overlap) + 1
        return min(
            self.get_monthly_flat_fee() * effective_months,
            self.flat_fee()
        )

    def cancel(self):
        self.status = constants.CreditLineItemStatus.CANCELED
        self.save()

    def delete(self):
        if self.status != constants.CreditLineItemStatus.PENDING:
            raise AssertionError('Credit item is not pending')
        super(CreditLineItem, self).delete()

    def get_salesforce_url(self):
        if not self.contract_id:
            return None
        return 'https://eu6.salesforce.com/{}'.format(self.contract_id)

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'amount': 'Amount',
            'license_fee': 'License Fee',
            'flat_fee_cc': 'Flat Fee (cc)',
            'flat_fee_start_date': 'Flat Fee Start Date',
            'flat_fee_end_date': 'Flat Fee End Date',
            'status': 'Status',
            'comment': 'Comment'
        }
        return NAMES.get(prop_name)

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'amount' and value is not None:
            value = lc_helper.default_currency(Decimal(value))
        elif prop_name == 'license_fee' and value is not None:
            value = '{}%'.format(utils.string_helper.format_decimal(
                Decimal(value) * 100, 2, 3))
        elif prop_name == 'flat_fee_cc':
            value = lc_helper.default_currency(
                Decimal(value) * converters.CC_TO_DECIMAL_CURRENCY)
        elif prop_name == 'status':
            value = constants.CreditLineItemStatus.get_text(value)
        elif prop_name == 'comment':
            value = value or ''
        elif prop_name == 'flat_fee_start_date':
            value = value or ''
        elif prop_name == 'flat_fee_end_date':
            value = value or ''
        return value

    def get_settings_dict(self):
        return {history_key: getattr(self, history_key) for history_key in self.history_fields}

    def save(self, request=None, action_type=None, *args, **kwargs):
        self.full_clean()
        if request and not self.pk:
            self.created_by = request.user
        super(CreditLineItem, self).save(*args, **kwargs)
        core.bcm.CreditHistory.objects.create(
            created_by=request.user if request else None,
            snapshot=model_to_dict(self),
            credit=self,
        )
        self.add_to_history(
            request and request.user,
            action_type)

    def add_to_history(self, user, action_type):
        changes = self.get_model_state_changes(
            model_to_dict(self)
        )
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return None, ''

        if self.post_init_newly_created:
            changes = model_to_dict(self)

        changes, changes_text = self.construct_changes(
            'Created credit.',
            'Credit: #{}.'.format(self.id) if self.id else None,
            changes
        )

        if self.account is not None:
            self.account.write_history(
                changes_text,
                changes=changes,
                action_type=action_type,
                user=user)
        elif self.agency is not None:
            self.agency.write_history(
                changes_text,
                changes=changes,
                action_type=action_type,
                user=user)

    def __str__(self):
        parent = self.agency or self.account
        return '{} - {} - ${} - from {} to {}'.format(
            parent.id, str(parent), self.amount,
            self.start_date, self.end_date)

    def is_editable(self):
        return self.status == constants.CreditLineItemStatus.PENDING

    def flat_fee(self):
        return Decimal(self.flat_fee_cc) * converters.CC_TO_DECIMAL_CURRENCY

    def effective_amount(self):
        return Decimal(self.amount) - self.flat_fee()

    def is_available(self):
        return not self.is_past() and self.status == constants.CreditLineItemStatus.SIGNED\
            and (self.effective_amount() - self.get_allocated_amount()) > 0

    def is_agency(self):
        return self.agency_id is not None

    def clean(self):
        if self.account is not None and self.agency is not None:
            raise ValidationError({
                'account': ['Only one of either account or agency must be set.'],
                'agency': ['Only one of either account or agency must be set.'],
            })

        if self.account is None and self.agency is None:
            raise ValidationError({
                'account': ['One of either account or agency must be set.'],
                'agency': ['One of either account or agency must be set.'],
            })

        has_changed = any((
            self.has_changed('start_date'),
            self.has_changed('license_fee'),
        ))

        if has_changed and not self.is_editable():
            raise ValidationError({
                '__all__': ['Nonpending credit line item cannot change.'],
            })

        core.bcm.helpers.validate(
            self.validate_end_date,
            self.validate_license_fee,
            self.validate_status,
            self.validate_amount,
            self.validate_flat_fee_cc
        )

        if not self.pk or self.previous_value('status') != constants.CreditLineItemStatus.SIGNED:
            return

        budgets = self.budgets.all()
        if not budgets:
            return

        min_end_date = min(b.end_date for b in budgets)

        if self.has_changed('end_date') and self.end_date < min_end_date:
            raise ValidationError({
                'end_date': ['End date minimum is depending on budgets.'],
            })

    def validate_flat_fee_cc(self):
        if not self.flat_fee_cc:
            return
        delta = self.effective_amount() - self.get_allocated_amount()
        if delta < 0:
            raise ValidationError(
                'Flat fee exceeds the available credit amount by ${}.'.format(
                    -delta.quantize(Decimal('1.00'))
                )
            )

    def validate_amount(self):
        if not self.amount:
            return
        if self.amount < 0:
            raise ValidationError('Amount cannot be negative.')
        if not self.pk or not self.has_changed('amount'):
            return
        prev_amount = self.previous_value('amount')
        budgets = self.budgets.all()

        if prev_amount < self.amount or not budgets:
            return
        if self.effective_amount() < sum(b.allocated_amount() for b in budgets):
            raise ValidationError(
                'Credit line item amount needs to be larger than the sum of budgets.'
            )

    def validate_status(self):
        s = constants.CreditLineItemStatus
        if not self.has_changed('status'):
            return
        if self.status == s.PENDING:
            raise ValidationError(
                'Credit line item status cannot change to PENDING.')

    def validate_end_date(self):
        if not self.end_date:
            return
        if self.has_changed('end_date') and self.previous_value('end_date') > self.end_date:
            raise ValidationError(
                'New end date cannot be before than the previous.')
        if self.start_date and self.start_date > self.end_date:
            raise ValidationError(
                'Start date cannot be greater than the end date.')

    def validate_license_fee(self):
        if self.license_fee and not (0 <= self.license_fee < 1):
            raise ValidationError('License fee must be between 0 and 100%.')

        if not self.start_date or not self.end_date:
            return

    @classmethod
    def get_defaults_dict(cls):
        return {}

    class QuerySet(models.QuerySet):

        def filter_active(self, date=None):
            if date is None:
                date = dates_helper.local_today()
            return self.filter(
                start_date__lte=date,
                end_date__gte=date,
                status=constants.CreditLineItemStatus.SIGNED
            )

        def filter_overlapping(self, start_date, end_date):
            return self.filter(
                (Q(start_date__gte=start_date) & Q(start_date__lte=end_date)) |
                (Q(end_date__gte=start_date) & Q(end_date__lte=end_date)) |
                (Q(start_date__lte=start_date) & Q(end_date__gte=end_date)))

        def delete(self):
            if self.exclude(status=constants.CreditLineItemStatus.PENDING).count() != 0:
                raise AssertionError('Some credit items are not pending')
            super(CreditLineItem.QuerySet, self).delete()

        def filter_by_account(self, account):
            credit_items = CreditLineItem.objects.filter(account=account)
            if account.agency is not None:
                credit_items |= CreditLineItem.objects.filter(agency=account.agency)
            return credit_items

        def get_any_for_budget_creation(self, account):
            credit_items = self.filter_by_account(account).filter_active()
            return credit_items.prefetch_related('budgets').order_by('-start_date', '-end_date', '-created_dt').first()

    objects = CreditLineItemManager.from_queryset(QuerySet)()
