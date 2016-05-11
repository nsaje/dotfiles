class BaseError(Exception):
    '''
    Base error. If implementing custom errors, subclass this error.
    '''
    def __init__(self, message=None, pretty_message=None):
        super(BaseError, self).__init__(message)
        self.pretty_message = pretty_message
        self.error_code = self.__class__.__name__
        self.http_status_code = 500


class AuthError(BaseError):
    '''
    Error thrown when user cannot be identified.
    '''
    def __init__(self, message=None, pretty_message=None):
        super(AuthError, self).__init__(message, pretty_message)
        self.http_status_code = 401


class AuthorizationError(BaseError):
    '''
    Error thrown when user does not have appropriate rights.
    '''
    def __init__(self, message=None, pretty_message=None):
        super(AuthorizationError, self).__init__(message, pretty_message)
        self.http_status_code = 401


class ValidationError(BaseError):
    '''
    Error thrown by validation methods.
    '''
    def __init__(self, message=None, pretty_message=None, errors=None, data=None):
        super(ValidationError, self).__init__(message, pretty_message)
        self.http_status_code = 400
        self.errors = errors
        self.data = data


class MissingDataError(BaseError):
    '''
    Error thrown when the requested data is not available.
    '''
    def __init__(self, message=None, pretty_message=None):
        super(MissingDataError, self).__init__(message, pretty_message)
        self.http_status_code = 404


class ForbiddenError(BaseError):
    '''
    Error thrown when the requested operation cannot be completed.
    '''
    def __init__(self, message=None, pretty_message=None):
        super(ForbiddenError, self).__init__(message, pretty_message)
        self.http_status_code = 403


class InvalidBreakdownError(BaseError):
    pass


custom_errors = (
    AuthError,
    AuthorizationError,
    ValidationError,
    MissingDataError,
    ForbiddenError
)
