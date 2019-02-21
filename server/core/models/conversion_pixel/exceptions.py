from utils.exc import ValidationError


class DuplicatePixelName(ValidationError):
    pass


class MutuallyExclusivePixelFlagsEnabled(ValidationError):
    pass


class AudiencePixelAlreadyExists(ValidationError):
    pass


class AudiencePixelNotSet(ValidationError):
    pass


class AudiencePixelCanNotBeArchived(ValidationError):
    pass
