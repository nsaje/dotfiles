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


class RTBSourcesCPCNegative(ValidationError):
    pass


class RTBSourcesCPMNegative(ValidationError):
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
