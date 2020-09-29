from utils.exc import ValidationError


class DuplicatePixelName(ValidationError):
    pass


class PixelNameNotEditable(ValidationError):
    pass


class AudiencePixelCanNotBeArchived(ValidationError):
    pass
