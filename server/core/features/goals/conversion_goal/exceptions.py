from utils.exc import ValidationError


class ConversionGoalLimitExceeded(ValidationError):
    pass


class ConversionWindowRequired(ValidationError):
    pass


class ConversionPixelInvalid(ValidationError):
    pass


class ConversionGoalNotUnique(ValidationError):
    pass


class GoalIDInvalid(ValidationError):
    pass
