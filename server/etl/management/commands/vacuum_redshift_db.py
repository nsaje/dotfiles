from utils.command_helpers import ExceptionCommand

from etl import maintenance
from etl import refresh_k1

import influx


class Command(ExceptionCommand):
    @influx.timer('etl.vacuum_redshift_db')
    def handle(self, *args, **options):
        views = refresh_k1.MATERIALIZED_VIEWS + refresh_k1.NEW_MATERIALIZED_VIEWS
        tables = [x.TABLE_NAME for x in views if not x.IS_TEMPORARY_TABLE]

        for table in tables:
            maintenance.vacuum_and_analyze(table)
