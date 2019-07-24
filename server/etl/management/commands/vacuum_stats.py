from etl import maintenance
from utils import metrics_compat
from utils.command_helpers import Z1Command


class Command(Z1Command):
    @metrics_compat.timer("etl.vacuum_other_tables")
    def handle(self, *args, **options):
        tables = ["stats", "conversions", "postclickstats", "outbrainpublisherstats", "audience_report", "pixie_sample"]

        for table in tables:
            maintenance.vacuum(table)
            maintenance.analyze(table)

        table = "supply_stats"
        maintenance.vacuum(table, delete_only=True)
        maintenance.analyze(table)
