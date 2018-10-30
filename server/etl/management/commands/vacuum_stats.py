import influx

from etl import maintenance
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    @influx.timer("etl.vacuum_other_tables")
    def handle(self, *args, **options):
        tables = ["stats", "conversions", "postclickstats", "outbrainpublisherstats", "audience_report", "pixie_sample"]

        for table in tables:
            maintenance.vacuum(table)
            maintenance.analyze(table)

        table = "supply_stats"
        maintenance.vacuum(table, delete_only=True)
        maintenance.analyze(table)
