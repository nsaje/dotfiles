from utils.exc import ValidationError


class CannotChangeType(ValidationError):
    pass


class AccountIsArchived(ValidationError):
    pass
