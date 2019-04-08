from utils.exc import ValidationError


class DisablingAgencyNotAllowed(ValidationError):
    pass


class EditingAgencyNotAllowed(ValidationError):
    pass
