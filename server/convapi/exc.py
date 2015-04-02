class IncompleteReportException(Exception):
    pass


class EmptyReportException(Exception):
    pass


class CsvParseException(Exception):
    pass


class AuthException(Exception):
    pass


class LandingPageUrlParseError(Exception):
    pass

class TooManyMissingSourcesException(Exception):
    pass
