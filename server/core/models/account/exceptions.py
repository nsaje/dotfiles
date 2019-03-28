from utils.exc import ValidationError


class AccountDoesNotMatch(ValidationError):
    pass


class DisablingAccountNotAllowed(ValidationError):
    pass
