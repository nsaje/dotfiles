from models import RSQuery as RSQuery, RSBreakdownQuery


def dictfetchall(cursor):
    desc = cursor.description

    return [
        dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()
    ]


class RSCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute(self, statement, params):
        self.cursor.execute(statement, params)

    def fetchall(self):
        return self.cursor.fetchall()

    def dictfetchall(self):
        return dictfetchall(self.cursor)

    def close(self):
        self.cursor.close()

    def mogrify(self, *args, **kwargs):
        return self.cursor.mogrify(*args, **kwargs)
