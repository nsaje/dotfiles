from utils.exc import ValidationError
from utils.exc import MulticurrencyValidationError


class DailyBudgetNegative(ValidationError):
    pass


class MinimalDailyBudgetTooLow(MulticurrencyValidationError):
    pass


class MaximalDailyBudgetTooHigh(MulticurrencyValidationError):
    pass


class CPCNegative(ValidationError):
    pass


class CPCPrecisionExceeded(MulticurrencyValidationError):
    pass


class MinimalCPCTooLow(MulticurrencyValidationError):
    pass


class MaximalCPCTooHigh(MulticurrencyValidationError):
    pass


class RTBSourcesCPCNegative(ValidationError):
    pass


class CPCInvalid(ValidationError):
    pass


class RetargetingNotSupported(ValidationError):
    pass


class MediaSourceNotConnectedToFacebook(ValidationError):
    pass


class YahooCPCTooLow(ValidationError):
    pass


class AutopilotDailySpendCapTooLow(ValidationError):
    pass
