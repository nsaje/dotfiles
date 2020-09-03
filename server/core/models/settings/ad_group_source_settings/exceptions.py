from utils.exc import MulticurrencyValidationError
from utils.exc import ValidationError


class DailyBudgetNegative(ValidationError):
    pass


class MinimalDailyBudgetTooLow(MulticurrencyValidationError):
    pass


class MaximalDailyBudgetTooHigh(MulticurrencyValidationError):
    pass


class CPCNegative(ValidationError):
    pass


class CPMNegative(ValidationError):
    pass


class CPCPrecisionExceeded(MulticurrencyValidationError):
    pass


class CPMPrecisionExceeded(MulticurrencyValidationError):
    pass


class MinimalCPCTooLow(MulticurrencyValidationError):
    pass


class MaximalCPCTooHigh(MulticurrencyValidationError):
    pass


class MinimalCPMTooLow(MulticurrencyValidationError):
    pass


class MaximalCPMTooHigh(MulticurrencyValidationError):
    pass


class CannotSetCPC(ValidationError):
    pass


class CannotSetCPM(ValidationError):
    pass


class B1SourcesCPCNegative(ValidationError):
    pass


class B1SourcesCPMNegative(ValidationError):
    pass


class CPCInvalid(ValidationError):
    pass


class MediaSourceNotConnectedToFacebook(ValidationError):
    pass


class AutopilotDailySpendCapTooLow(ValidationError):
    pass


class BudgetUpdateWhileSourcesGroupEnabled(ValidationError):
    pass
