from django.core import exceptions


class MultipleFilterEntitiesException(exceptions.ValidationError):
    pass


class SourcePolicyException(exceptions.ValidationError):
    pass


class SubmissionFilterExistsException(exceptions.ValidationError):
    pass
