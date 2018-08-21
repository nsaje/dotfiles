from utils.command_helpers import ExceptionCommand

from etl import maintenance
from etl import refresh

import influx


class Command(ExceptionCommand):
    @influx.timer("etl.vacuum_redshift_db")
    def handle(self, *args, **options):
        for table in refresh.get_all_views_table_names():
            maintenance.vacuum(table)
            maintenance.analyze(table)
