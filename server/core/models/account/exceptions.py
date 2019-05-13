from utils.exc import ValidationError


class AccountDoesNotMatch(ValidationError):
    pass


class CreatingAccountNotAllowed(ValidationError):
    pass


class EditingAccountNotAllowed(ValidationError):
    pass
