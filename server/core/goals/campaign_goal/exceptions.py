from utils.exc import ValidationError


class ConversionGoalLimitExceeded(ValidationError):
    pass


class MultipleSameTypeGoals(ValidationError):
    pass
