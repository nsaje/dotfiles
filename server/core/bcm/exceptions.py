from utils.exc import ValidationError


class CanNotSetMargin(ValidationError):
    pass


class CanNotChangeStartDate(ValidationError):
    pass


class CanNotChangeBudget(ValidationError):
    pass


class CreditCanceled(ValidationError):
    pass


class CampaignHasNoCredit(ValidationError):
    pass


class CanNotChangeCredit(ValidationError):
    pass


class CreditPending(ValidationError):
    pass


class CurrencyInconsistent(ValidationError):
    pass


class StartDateInThePast(ValidationError):
    pass


class EndDateInThePast(ValidationError):
    pass


class StartDateInvalid(ValidationError):
    pass


class EndDateInvalid(ValidationError):
    pass


class StartDateBiggerThanEndDate(ValidationError):
    pass


class MarginRangeInvalid(ValidationError):
    pass


class OverlappingBudgetMarginInvalid(ValidationError):
    pass


class OverlappingBudgets(ValidationError):
    pass


class BudgetAmountCannotChange(ValidationError):
    pass


class BudgetAmountNegative(ValidationError):
    pass


class BudgetAmountExceededCreditAmount(ValidationError):
    pass


class BudgetAmountTooLow(ValidationError):
    pass


class CampaignStopDisabled(ValidationError):
    pass
