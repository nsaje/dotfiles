import datetime
import collections
import calendar
from decimal import Decimal, ROUND_HALF_UP

import newrelic.agent
from django.db.models import Prefetch

import dash.models
import dash.constants
import utils.dates_helper

from utils import converters


class BudgetProjections(object):
    PRECISION = Decimal('.0001')
    ROUNDING = ROUND_HALF_UP
    CONFIDENCE_OFFSET_DAYS = 7
    BREAKDOWN_PREFIX = {
        'account': 'campaign__'
    }
    FUTURE_METRICS = {
        'account': (
            'flat_fee',
            'total_fee',
            'allocated_total_budget',
            'allocated_media_budget',
        ),
        'campaign': (
            'allocated_total_budget',
            'allocated_media_budget',
        ),
    }
    MANAGED_ACCOUNT_TYPES = (
        dash.constants.AccountType.MANAGED,
    )

    @newrelic.agent.function_trace()
    def __init__(self, start_date, end_date, breakdown, projection_date=None, accounts=[], **constraints):
        assert breakdown in ('account', 'campaign', )
        self.today = utils.dates_helper.local_today()

        self.breakdown = breakdown
        self.projection_date = min(
            projection_date or (self.today - datetime.timedelta(1)),
            end_date,
        )
        self.start_date = start_date

        self.first_of_month = False
        if self.start_date == self.today and self.projection_date < self.start_date:
            self.first_of_month = True
            self.projection_date = self.start_date

        self.confidence_date = start_date - datetime.timedelta(
            BudgetProjections.CONFIDENCE_OFFSET_DAYS
        )
        self.end_date = end_date
        self.forecast_days = (self.end_date - self.start_date).days + 1
        self.past_days = (self.projection_date - self.start_date).days + 1
        self._prepare_budgets(constraints)

        self.calculation_groups = {}
        self.projections = {}
        self.accounts = {acc.id: acc for acc in (accounts or dash.models.Account.objects.all())}

        self.agency_credits = {}
        for cli in dash.models.CreditLineItem.objects.filter(agency_id__isnull=False):
            self.agency_credits.setdefault(cli.agency_id, []).append(cli)

        self._prepare_account_types()

        self._prepare_data_by_breakdown()
        self._calculate_rows()
        self._calculate_totals()

    def row(self, breakdown_value, field=None):
        row = self.projections.get(breakdown_value, {})
        return row.get(field) if field else row

    def total(self, field=None):
        return self.totals[field] if field else self.totals

    def keys(self):
        return self.projections.keys()

    @newrelic.agent.function_trace()
    def _prepare_budgets(self, constraints):
        self.budgets = dash.models.BudgetLineItem.objects.all().exclude(
            end_date__lt=self.confidence_date,
            start_date__gt=self.end_date,
        ).filter(
            **constraints
        ).select_related(
            'campaign', 'campaign__account', 'credit'
        ).prefetch_related(
            Prefetch(
                'statements',
                queryset=dash.models.BudgetDailyStatement.objects.filter(
                    date__gte=self.confidence_date,
                    date__lte=self.projection_date
                ).order_by('date')
            )
        )

    def _prepare_account_types(self):
        self.account_types = {
            sett['account_id']: sett['account_type']
            for sett in dash.models.AccountSettings.objects.all().group_current_settings().values(
                'account_id', 'account_type')
        }
        self.campaign_types = {
            c['pk']: self.account_types.get(c['account_id'], dash.constants.AccountType.UNKNOWN)
            for c in dash.models.Campaign.objects.all().values('pk', 'account_id')
        }

    def _is_managed(self, key):
        types_map = self.account_types
        if self.breakdown in 'campaign':
            types_map = self.campaign_types
        return types_map.get(key) in BudgetProjections.MANAGED_ACCOUNT_TYPES

    @newrelic.agent.function_trace()
    def _breakdown_field(self, budget):
        if self.breakdown == 'account':
            return budget.campaign.account.pk
        if self.breakdown == 'campaign':
            return budget.campaign.pk

    @newrelic.agent.function_trace()
    def _prepare_data_by_breakdown(self):
        for budget in self.budgets:
            self.calculation_groups.setdefault(self._breakdown_field(budget), []).append(budget)
        if self.breakdown == 'account':
            for account_id in self.accounts:
                self.calculation_groups.setdefault(account_id, [])

    @newrelic.agent.function_trace()
    def _calculate_totals(self):
        if self.past_days <= 0:
            self.totals = self._blank_projections()
            for field in BudgetProjections.FUTURE_METRICS[self.breakdown]:
                self.totals[field] = sum(row[field] for row in self.projections.values())
            return

        self.totals = collections.defaultdict(Decimal)
        for row in self.projections.values():
            for key, value in row.iteritems():
                self.totals[key] += (value or Decimal(0))

        self.totals['pacing'] = None
        if self.totals['ideal_media_spend']:
            self.totals['pacing'] = (self.totals['attributed_media_spend'] /
                                     self.totals['ideal_media_spend'] * Decimal(100)).quantize(BudgetProjections.PRECISION,
                                                                                               rounding=BudgetProjections.ROUNDING)

    def _get_credit_line_items_by_account(self):
        if self.breakdown != 'account':
            return {}
        credit_line_items = dash.models.CreditLineItem.objects.filter(account_id__in=self.accounts.keys())

        m = collections.defaultdict(list)
        for cli in credit_line_items:
            m[cli.account_id].append(cli)
        return m

    def _get_accounts_with_spend_by_agency(self):
        if self.breakdown != 'account':
            return {}

        agency_ids = dash.models.Account.objects.filter(pk__in=self.accounts).values_list('agency_id', flat=True)
        res = dash.models.BudgetDailyStatement.objects.filter(
            budget__campaign__account__agency_id__in=agency_ids).filter(
                media_spend_nano__gt=0
        ).values_list('budget__campaign__account_id', 'budget__campaign__account__agency_id')

        m = collections.defaultdict(set)
        for account_id, agency_id in res:
            m[agency_id].add(account_id)

        return m

    @newrelic.agent.function_trace()
    def _calculate_rows(self):
        credit_line_items_map = self._get_credit_line_items_by_account()
        accounts_with_spend_map = self._get_accounts_with_spend_by_agency()

        for key, budgets in self.calculation_groups.iteritems():
            if self.past_days <= 0:
                row = self._blank_projections()
                self._calculate_allocated_budgets(row, budgets)
                self._calculate_recognized_fees(row, budgets, key, credit_line_items_map, accounts_with_spend_map)
                self.projections[key] = {
                    metric: value and value.quantize(BudgetProjections.PRECISION, rounding=BudgetProjections.ROUNDING)
                    for metric, value in row.iteritems()
                }
                continue
            statements_on_date, row = {}, {}
            for budget in budgets:
                for statement in budget.statements.all():
                    statements_on_date.setdefault(statement.date, []).append(statement)

            num_of_positive_statements = len(filter(lambda x: x, [
                s.media_spend_nano + s.data_spend_nano
                for slist in statements_on_date.values() for s in slist
            ]))

            self._calculate_allocated_budgets(row, budgets)
            self._calculate_pacing(row, budgets)
            self._calculate_recognized_fees(row, budgets, key, credit_line_items_map, accounts_with_spend_map)
            self._calculate_media_spend_projection(key, row, budgets, statements_on_date,
                                                   num_of_positive_statements)
            self._calculate_license_fee_projection(key, row, budgets, statements_on_date,
                                                   num_of_positive_statements)
            self._calculate_total_license_fee_projection(row, budgets)

            self.projections[key] = {
                metric: value and value.quantize(BudgetProjections.PRECISION, rounding=BudgetProjections.ROUNDING)
                for metric, value in row.iteritems()
            }

    def _blank_projections(self):
        row = {
            'allocated_total_budget': None,
            'allocated_media_budget': None,
            'ideal_daily_media_spend': None,
            'ideal_media_spend': None,
            'pacing': None,
            'attributed_media_spend': None,
            'attributed_license_fee': None,
            'media_spend_projection': None,
            'license_fee_projection': None,
        }
        if self.breakdown == 'account':
            row['flat_fee'] = None
            row['total_fee'] = None
            row['total_fee_projection'] = None
        return row

    def _calculate_allocated_budgets(self, row, budgets):
        row['allocated_total_budget'] = Decimal('0')
        row['allocated_media_budget'] = Decimal('0')

        for budget in budgets:
            overlap_start_date, overlap_end_date = budget.get_overlap(self.start_date, self.end_date)
            if None in (overlap_start_date, overlap_end_date, ):
                continue
            budget_days = (budget.end_date - budget.start_date).days + 1
            overlap_days = (overlap_end_date - overlap_start_date).days + 1
            daily_amount = budget.allocated_amount() / Decimal(budget_days) * overlap_days
            row['allocated_total_budget'] += daily_amount
            row['allocated_media_budget'] += (daily_amount * (1 - budget.credit.license_fee))

    def _calculate_pacing(self, row, budgets):
        assert 'allocated_media_budget' in row

        row['ideal_daily_media_spend'] = row['allocated_media_budget'] / Decimal(self.forecast_days)
        row['ideal_media_spend'] = row['ideal_daily_media_spend'] * Decimal(self.past_days)

        row['attributed_media_spend'] = converters.nano_to_decimal(sum(
            statement.media_spend_nano + statement.data_spend_nano
            for budget in budgets
            for statement in budget.statements.all()
            if statement.date >= self.start_date and statement.date <= self.projection_date
        ))

        row['pacing'] = None
        if row['ideal_media_spend']:
            row['pacing'] = row['attributed_media_spend'] / row['ideal_media_spend'] * Decimal(100)

    def _calculate_media_spend_projection(self, key, row, budgets, statements_on_date,
                                          num_of_positive_statements):
        assert 'allocated_media_budget' in row
        assert 'attributed_media_spend' in row
        # IMPORTANT: media here includes data

        if self.end_date < self.today:
            row['media_spend_projection'] = row['attributed_media_spend']
            return

        if self._is_managed(key) and (self.first_of_month or num_of_positive_statements <= BudgetProjections.CONFIDENCE_OFFSET_DAYS):
            # skip projection if it's less than the OFFSET, assume allocated budget
            row['media_spend_projection'] = row['allocated_media_budget']
            return

        media_nano = 0
        for date in utils.dates_helper.date_range(self.start_date,
                                                  self.projection_date + datetime.timedelta(1)):
            media_nano += sum(
                s.media_spend_nano + s.data_spend_nano for s in statements_on_date.get(date, [])
            )

        row['media_spend_projection'] = max(
            row['attributed_media_spend'],
            min(
                converters.nano_to_decimal(float(media_nano) / self.past_days) * Decimal(self.forecast_days),
                row['allocated_media_budget']
            )
        )

    def _calculate_recognized_fees(self, row, budgets, account_id, credit_line_items_map, accounts_with_spend_map):
        if self.breakdown != 'account':
            return
        row['attributed_license_fee'] = sum(
            converters.nano_to_decimal(statement.license_fee_nano)
            for budget in budgets
            for statement in budget.statements.all()
            if statement.date >= self.start_date and statement.date <= self.projection_date
        )
        row['flat_fee'] = sum(
            credit.get_flat_fee_on_date_range(self.start_date, self.end_date)
            for credit in credit_line_items_map[account_id]
        ) + self._calculate_agency_credit_flat_fee_share(
            self.accounts.get(account_id),
            accounts_with_spend_map
        )
        row['total_fee'] = row['attributed_license_fee'] + row['flat_fee']

    def _calculate_agency_credit_flat_fee_share(self, account, accounts_with_spend_by_agency):
        if not account or not account.agency:
            return 0

        agency_account_count = len(accounts_with_spend_by_agency[account.agency_id])
        if agency_account_count == 0:
            return 0

        if account.pk not in accounts_with_spend_by_agency[account.agency_id]:
            # This account has no spend in this daterange,
            # Agency credit flat fee has to be excluded
            return 0

        agency_flat_fee_share = Decimal(sum(
            credit.get_flat_fee_on_date_range(self.start_date, self.end_date)
            for credit in self.agency_credits.get(account.agency_id, [])
        )) / Decimal(agency_account_count)
        return agency_flat_fee_share

    def _calculate_license_fee_projection(self, key, row, budgets, statements_on_date,
                                          num_of_positive_statements):
        assert 'allocated_total_budget' in row and 'allocated_media_budget' in row
        # always skip first OFFSET days for calculation
        # unless it's less than the OFFSET, then assume
        # allocated budget
        maximum_fee = row['allocated_total_budget'] - row['allocated_media_budget']

        if self.end_date < self.today or (self._is_managed(key) and (self.first_of_month or num_of_positive_statements <= BudgetProjections.CONFIDENCE_OFFSET_DAYS)):
            # skip projection if it's less than the OFFSET, assume allocated budget
            row['license_fee_projection'] = maximum_fee
            return

        fee_nano = 0
        for date in utils.dates_helper.date_range(self.start_date,
                                                  self.projection_date + datetime.timedelta(1)):
            fee_nano += sum(
                s.license_fee_nano for s in statements_on_date.get(date, [])
            )

        row['license_fee_projection'] = min(
            converters.nano_to_decimal(float(fee_nano) / self.past_days) * Decimal(self.forecast_days),
            maximum_fee
        )

    def _calculate_total_license_fee_projection(self, row, budgets):
        if self.breakdown != 'account':
            return
        assert 'license_fee_projection' in row
        assert 'flat_fee' in row
        row['total_fee_projection'] = row['license_fee_projection'] + row['flat_fee']


class CurrentMonthBudgetProjections(BudgetProjections):

    def __init__(self, breakdown, date=None, **constraints):
        today = date or datetime.date.today()
        _, end = calendar.monthrange(today.year, today.month)
        super(CurrentMonthBudgetProjections, self).__init__(
            datetime.date(today.year, today.month, 1),
            datetime.date(today.year, today.month, end),
            breakdown,
            **constraints
        )
