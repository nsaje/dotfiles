from utils.exc import ValidationError


class SourceNotAllowed(ValidationError):
    pass


class SourceAlreadyExists(ValidationError):
    pass


class RetargetingNotSupported(ValidationError):
    pass


class VideoNotSupported(ValidationError):
    pass


class DisplayNotSupported(ValidationError):
    pass
