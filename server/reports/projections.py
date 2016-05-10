import datetime
import collections

from decimal import Decimal

from django.db.models import Prefetch

import dash.models
import reports.models
import utils.dates_helper


class BudgetProjections:
    PRECISION = 2
    CONFIDENCE_OFFSET_DAYS = 7
    BREAKDOWN_PREFIX = {
        'account': 'campaign__'
    }

    def __init__(self, start_date, end_date, breakdown, projection_date=None, **constraints):
        assert breakdown in ('account', 'campaign', )

        self.breakdown = breakdown
        self.projection_date = projection_date or (datetime.date.today() - datetime.timedelta(1))
        self.start_date = start_date
        self.confidence_date = start_date - datetime.timedelta(
            BudgetProjections.CONFIDENCE_OFFSET_DAYS
        )
        self.end_date = end_date
        self.forecast_days = (self.end_date - self.start_date).days + 1
        self.past_days = (self.projection_date - self.start_date).days + 1

        self._prepare_budgets(constraints)

        self.calculation_groups = {}
        self.projections = {}

        self._prepare_data_by_breakdown()
        self._calculate_rows()
        self._calculate_totals()

    def row(self, breakdown_value, field=None):
        row = self.projections[breakdown_value]
        return field and row.get(field) or row

    def total(self, breakdown_value):
        return self.totals[breakdown_value]

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
                queryset=reports.models.BudgetDailyStatement.objects.filter(
                    date__gte=self.confidence_date,
                    date__lte=self.projection_date
                ).order_by('date')
            )
        )

    def _breakdown_field(self, budget):
        if self.breakdown == 'account':
            return budget.campaign.account.pk
        if self.breakdown == 'campaign':
            return budget.campaign.pk

    def _prepare_data_by_breakdown(self):
        for budget in self.budgets:
            self.calculation_groups.setdefault(self._breakdown_field(budget), []).append(budget)

    def _calculate_totals(self):
        self.totals = collections.defaultdict(int)
        rows = self.projections.values()
        for row in rows:
            for key, value in row.iteritems():
                self.totals[key] += value or Decimal(0)
        self.totals['pacing'] = self.totals['pacing'] / Decimal(len(rows))

    def _calculate_rows(self):
        for key, budgets in self.calculation_groups.iteritems():
            row = {}
            statements_on_date = {}
            for budget in budgets:
                for statement in budget.statements.all():
                    statements_on_date.setdefault(statement.date, []).append(statement)

            num_of_positive_statements = len(filter(lambda x: x, [
                s.media_spend_nano + s.data_spend_nano
                for slist in statements_on_date.values() for s in slist
            ]))

            self._calculate_allocated_budgets(row, budgets)
            self._calculate_pacing(row, budgets)
            self._calculate_media_spend_projection(row, budgets, statements_on_date,
                                                   num_of_positive_statements)
            self._calculate_license_fee_projection(row, budgets, statements_on_date,
                                                   num_of_positive_statements)
            if self.breakdown == 'account':
                self._calculate_recognized_fees(row, budgets)
                self._calculate_total_license_fee_projection(row, budgets)
            self.projections[key] = row

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
        row['ideal_media_spend'] = row['allocated_media_budget'] / Decimal(self.forecast_days) \
            * Decimal(self.past_days)

        row['attributed_media_spend'] = dash.models.nano_to_dec(sum(
            statement.media_spend_nano + statement.data_spend_nano
            for budget in budgets
            for statement in budget.statements.all()
            if statement.date >= self.start_date and statement.date <= self.projection_date
        ))

        row['pacing'] = None
        if row['ideal_media_spend']:
            row['pacing'] = row['attributed_media_spend'] / row['ideal_media_spend']

    def _calculate_media_spend_projection(self, row, budgets, statements_on_date,
                                          num_of_positive_statements):
        assert 'allocated_media_budget' in row
        # IMPORTANT: media here includes data

        if num_of_positive_statements <= BudgetProjections.CONFIDENCE_OFFSET_DAYS:
            # skip projection if it's less than the OFFSET, assume allocated budget
            row['media_spend_projection'] = row['allocated_media_budget']
            return

        media_nano = 0
        for date in utils.dates_helper.date_range(self.start_date,
                                                  self.projection_date + datetime.timedelta(1)):
            media_nano += sum(
                s.media_spend_nano + s.data_spend_nano for s in statements_on_date.get(date, [])
            )
        row['media_spend_projection'] = min(
            dash.models.nano_to_dec(float(media_nano) / self.past_days) * Decimal(self.forecast_days),
            row['allocated_media_budget']
        )

    def _calculate_recognized_fees(self, row, budgets):
        row['attributed_license_fee'] = sum(
            dash.models.nano_to_dec(statement.license_fee_nano)
            for budget in budgets
            for statement in budget.statements.all()
            if statement.date >= self.start_date and statement.date <= self.projection_date
        )
        row['flat_fee'] = sum(
            credit.get_flat_fee_on_date_range(self.start_date, self.end_date)
            for credit in set(budget.credit for budget in budgets)
        )
        row['total_fee'] = row['attributed_license_fee'] + row['flat_fee']

    def _calculate_license_fee_projection(self, row, budgets, statements_on_date,
                                          num_of_positive_statements):
        assert 'allocated_total_budget' in row and 'allocated_media_budget' in row
        # always skip first OFFSET days for calculation
        # unless it's less than the OFFSET, then assume
        # allocated budget
        maximum_fee = row['allocated_total_budget'] - row['allocated_media_budget']
        if num_of_positive_statements <= BudgetProjections.CONFIDENCE_OFFSET_DAYS:
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
            dash.models.nano_to_dec(float(fee_nano) / self.past_days) * Decimal(self.forecast_days),
            maximum_fee
        )

    def _calculate_total_license_fee_projection(self, row, budgets):
        assert 'license_fee_projection' in row
        assert 'flat_fee' in row
        row['total_fee_projection'] = row['license_fee_projection'] + row['flat_fee']
