from utils.exc import ValidationError


class SourceAlreadyReleased(ValidationError):
    pass


class SourceAlreadyUnreleased(ValidationError):
    pass
