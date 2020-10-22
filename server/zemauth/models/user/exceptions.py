from utils.exc import ValidationError


class MixedPermissionLevels(ValidationError):
    pass


class MissingReadPermission(ValidationError):
    pass


class MissingRequiredPermission(ValidationError):
    pass


class EmailAlreadyExists(ValidationError):
    pass


class InvalidCountry(ValidationError):
    pass


class InvalidCompanyType(ValidationError):
    pass


class InvalidStartYearOfExperience(ValidationError):
    pass


class InvalidUser(ValidationError):
    pass
