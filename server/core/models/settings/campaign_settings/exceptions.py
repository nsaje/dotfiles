from utils.exc import ValidationError


class CannotChangeLanguage(ValidationError):
    pass


class PublisherWhitelistInvalid(ValidationError):
    pass


class PublisherBlacklistInvalid(ValidationError):
    pass
