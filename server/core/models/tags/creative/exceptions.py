from utils.exc import ValidationError


class InvalidAgency(ValidationError):
    pass


class InvalidAccount(ValidationError):
    pass
