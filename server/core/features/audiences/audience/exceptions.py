from utils.exc import ValidationError


class PixelIsArchived(ValidationError):
    pass


class RuleTtlCombinationAlreadyExists(ValidationError):
    pass


class CanNotArchive(ValidationError):
    pass
