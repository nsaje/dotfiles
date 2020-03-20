from . import exceptions


class RefundLineItemValidatorMixin(object):
    def clean(self):
        self._validate_account()
        self._validate_start_date()
        self._validate_amount()
        self._validate_effective_margin()

    def _validate_account(self):
        if self.credit.account is not None and self.credit.account.id != self.account.id:
            raise exceptions.AccountInvalid(
                "Refund account {account_name} is not the same as credit account.".format(
                    account_name=self.account.name
                )
            )
        elif self.credit.agency is not None and self.credit.agency.id != self.account.agency.id:
            raise exceptions.AccountInvalid(
                "Refund account {account_name} is not part of credit agency.".format(account_name=self.account.name)
            )

    def _validate_start_date(self):
        is_valid = self.start_date >= self.credit.start_date.replace(day=1) and self.start_date <= self.credit.end_date

        if self.start_date.day != 1:
            raise exceptions.StartDateInvalid("Start date has to be set on the first day of the month.")
        if not is_valid:
            raise exceptions.StartDateInvalid("Refund start date is bound by credit start and end month.")

    def _validate_amount(self):
        total_spend = 0
        for budget in self.credit.budgets.all():
            total_spend += budget.get_local_spend_data(from_date=self.start_date, to_date=self.end_date)["etfm_total"]

        if self.amount > total_spend:
            raise exceptions.RefundAmountExceededTotalSpend("Total refunded amount exceeded total spend.")

        delta = self.amount - (self.previous_value("amount") or 0)
        if self.credit.get_available_amount() + delta < 0:
            raise exceptions.CreditAvailableAmountNegative(
                "Total refunded amount would cause the credit's available amount to be negative."
            )

    def _validate_effective_margin(self):
        if self.effective_margin and not (0 <= self.effective_margin < 1):
            raise exceptions.EffectiveMarginAmountOutOfBounds("Effective margin must be between 0 and 100%.")
