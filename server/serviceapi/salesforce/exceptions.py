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
