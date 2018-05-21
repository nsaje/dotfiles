from rest_framework.serializers import ValidationError


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
