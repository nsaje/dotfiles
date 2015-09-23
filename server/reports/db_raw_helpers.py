
def dictfetchall(cursor):
    desc = cursor.description

    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


class MyCursor(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, statement, params):
        self.cursor.execute(statement, params)

    def dictfetchall(self):
        return dictfetchall()

    def close(self):
        self.cursor.close()
