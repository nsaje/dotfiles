from utils.exc import ValidationError


class EditingAgencyNotAllowed(ValidationError):
    pass


class EditingSourcesNotAllowed(ValidationError):
    pass
