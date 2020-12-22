from django.db import connection


def get_count_estimate(table: str) -> int:
    with connection.cursor() as c:
        c.execute(f"SELECT reltuples as approximate_row_count FROM pg_class WHERE relname = '{table}';")
        return int(c.fetchall()[0][0])
