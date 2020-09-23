from utils.exc import ValidationError


class InvalidTargetType(ValidationError):
    pass


class InvalidActionType(ValidationError):
    pass


class InvalidCooldown(ValidationError):
    pass


class InvalidWindow(ValidationError):
    pass


class InvalidChangeStep(ValidationError):
    pass


class InvalidChangeLimit(ValidationError):
    pass


class InvalidSendEmailSubject(ValidationError):
    pass


class InvalidSendEmailBody(ValidationError):
    pass


class InvalidSendEmailRecipients(ValidationError):
    pass


class InvalidMacros(ValidationError):
    pass


class InvalidNotificationType(ValidationError):
    pass


class InvalidNotificationRecipients(ValidationError):
    pass


class InvalidPublisherGroup(ValidationError):
    pass


class InvalidParents(ValidationError):
    pass


class InvalidAgency(ValidationError):
    pass


class InvalidAccount(ValidationError):
    pass


class InvalidIncludedAccounts(ValidationError):
    pass


class InvalidIncludedCampaigns(ValidationError):
    pass


class InvalidIncludedAdGroups(ValidationError):
    pass


class MissingIncludedEntities(ValidationError):
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


class InvalidConversionPixel(ValidationError):
    pass


class InvalidConversionPixelWindow(ValidationError):
    pass


class InvalidConversionPixelAttribution(ValidationError):
    pass
