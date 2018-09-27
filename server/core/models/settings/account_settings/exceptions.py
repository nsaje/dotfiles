from utils.exc import ValidationError


class PublisherWhitelistInvalid(ValidationError):
    pass


class PublisherBlacklistInvalid(ValidationError):
    pass
