from utils.exc import ValidationError


class MixedPermissionLevels(ValidationError):
    pass


class MissingReadPermission(ValidationError):
    pass


class MissingRequiredPermission(ValidationError):
    pass


class EntityPermissionChangeNotAllowed(ValidationError):
    pass
