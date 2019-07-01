import influx

from etl import maintenance
from etl import refresh
from utils.command_helpers import Z1Command


class Command(Z1Command):
    @influx.timer("etl.vacuum_redshift_db")
    def handle(self, *args, **options):
        for table in refresh.get_all_views_table_names():
            maintenance.vacuum(table)
            maintenance.analyze(table)
