
class ReportsQueryError(Exception):
    pass


class ReportsUnknownAggregator(Exception):
    pass


class S3FileNotFoundError(Exception):
    pass


class S3FileEmpty(Exception):
    pass