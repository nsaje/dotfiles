from rest_framework.serializers import ValidationError


class CannotChangeAdGroupState(ValidationError):
    pass


class AutopilotB1SourcesNotEnabled(ValidationError):
    pass


class DailyBudgetAutopilotNotDisabled(ValidationError):
    pass


class CPCAutopilotNotDisabled(ValidationError):
    pass


class AutopilotDailyBudgetTooLow(ValidationError):
    pass


class AutopilotDailyBudgetTooHigh(ValidationError):
    pass


class AdGroupNotPaused(ValidationError):
    pass


class B1DailyBudgetTooHigh(ValidationError):
    pass


class CantEnableB1SourcesGroup(ValidationError):
    pass


class BluekaiCategoryInvalid(ValidationError):
    pass


class YahooDesktopCPCTooLow(ValidationError):
    pass


class MaxCPCTooLow(ValidationError):
    pass


class MaxCPCTooHigh(ValidationError):
    pass


class MaxCPMTooLow(ValidationError):
    pass


class MaxCPMTooHigh(ValidationError):
    pass


class EndDateBeforeStartDate(ValidationError):
    pass


class EndDateInThePast(ValidationError):
    pass


class TrackingCodeInvalid(ValidationError):
    pass
