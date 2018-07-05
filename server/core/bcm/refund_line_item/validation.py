from . import exceptions


class RefundLineItemValidatorMixin(object):

    def clean(self):
        self._validate_start_date()
        self._validate_amount()

    def _validate_start_date(self):
        is_valid = (self.start_date >= self.credit.start_date.replace(day=1) and
                    self.start_date <= self.credit.end_date)

        if self.start_date.day != 1:
            raise exceptions.StartDateInvalid(
                'Start date has to be set on the first day of the month.'
            )
        if not is_valid:
            raise exceptions.StartDateInvalid(
                'Refund start date is bound by credit start and end month.'
            )

    def _validate_amount(self):
        total_spend = 0
        for budget in self.credit.budgets.all():
            total_spend += budget.get_local_spend_data()['etfm_total']

        if self.amount > total_spend:
            raise exceptions.RefundAmountExceededTotalSpend(
                'Refund amount exceeded total spend.'
            )

        delta = self.amount - (self.previous_value('amount') or 0)
        if self.credit.get_available_amount() + delta < 0:
            raise exceptions.CreditAvailableAmountNegative(
                'Refund amount change would cause the credit\'s available amount to be negative.'
            )
