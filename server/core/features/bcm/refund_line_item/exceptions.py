from utils.exc import ValidationError


class StartDateInvalid(ValidationError):
    pass


class RefundAmountExceededTotalSpend(ValidationError):
    pass


class CreditAvailableAmountNegative(ValidationError):
    pass


class EffectiveMarginAmountOutOfBounds(ValidationError):
    pass


class AccountInvalid(ValidationError):
    pass
