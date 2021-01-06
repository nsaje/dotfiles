from rest_framework.serializers import ValidationError


class AgencyNotExternallyManaged(ValidationError):
    pass


class SalesRepresentativeNotFound(ValidationError):
    pass


class AccountManagerNotFound(ValidationError):
    pass


class AgencyNameAlreadyExists(ValidationError):
    pass


class CreatingAccountOnDisabledAgency(ValidationError):
    pass


class ListAllAndDateFilters(ValidationError):
    pass


class ListNoParametersProvided(ValidationError):
    pass


class UserAlreadyExists(ValidationError):
    pass
