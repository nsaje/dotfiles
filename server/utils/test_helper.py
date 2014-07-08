import datetime


class MockDateTime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)
