from etl import maintenance
from etl import refresh
from utils import metrics_compat
from utils.command_helpers import Z1Command

VACUUM_TO_99 = []


class Command(Z1Command):
    @metrics_compat.timer("etl.vacuum_redshift_db")
    def handle(self, *args, **options):
        for table in refresh.get_all_views_table_names():
            vacuum_to = 99 if table in VACUUM_TO_99 else 95
            maintenance.vacuum(table, to=vacuum_to)
            maintenance.analyze(table)

        raw_tables = [
            "stats",
            "stats_diff",
            "conversions",
            "postclickstats",
            "outbrainpublisherstats",
            "audience_report",
            "pixie_sample",
        ]
        for table in raw_tables:
            maintenance.vacuum(table)
            maintenance.analyze(table)

        table = "supply_stats"
        maintenance.vacuum(table, delete_only=True)
        maintenance.analyze(table)
