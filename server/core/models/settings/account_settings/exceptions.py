from utils.exc import ValidationError


class PublisherWhitelistInvalid(ValidationError):
    pass


class PublisherBlacklistInvalid(ValidationError):
    pass


class DefaultIconNotSquare(ValidationError):
    pass


class DefaultIconTooSmall(ValidationError):
    pass


class DefaultIconTooBig(ValidationError):
    pass
