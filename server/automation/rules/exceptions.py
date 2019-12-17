from utils.exc import ValidationError


class InvalidTargetType(ValidationError):
    pass


class InvalidActionType(ValidationError):
    pass


class InvalidChangeStep(ValidationError):
    pass


class InvalidChangeLimit(ValidationError):
    pass


class InvalidNotificationRecipients(ValidationError):
    pass


class InvalidRuleConditions(ValidationError):
    def __init__(self, *args, conditions_errors=None, **kwargs):
        if not conditions_errors:
            conditions_errors = {}
        self.conditions_errors = conditions_errors
        super().__init__(*args, **kwargs)


class InvalidRuleState(ValidationError):
    pass


class InvalidOperator(ValidationError):
    pass


class InvalidLeftOperandType(ValidationError):
    pass


class InvalidLeftOperandModifier(ValidationError):
    pass


class InvalidLeftOperandWindow(ValidationError):
    pass


class InvalidRightOperandType(ValidationError):
    pass


class InvalidRightOperandWindow(ValidationError):
    pass


class InvalidRightOperandValue(ValidationError):
    pass
