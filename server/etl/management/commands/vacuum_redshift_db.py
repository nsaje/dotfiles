from etl import maintenance
from etl import refresh
from utils import metrics_compat
from utils.command_helpers import Z1Command


class Command(Z1Command):
    @metrics_compat.timer("etl.vacuum_redshift_db")
    def handle(self, *args, **options):
        for table in refresh.get_all_views_table_names():
            maintenance.vacuum(table)
            maintenance.analyze(table)
