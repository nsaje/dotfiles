import concurrent.futures

from django.conf import settings

from etl import maintenance
from etl import refresh
from utils import metrics_compat
from utils.command_helpers import Z1Command

STATS_DB_CLUSTERS = [settings.STATS_DB_HOT_CLUSTER] + settings.STATS_DB_COLD_CLUSTERS
VACUUM_TO_99 = []

TABLE_STATS = "stats"
TABLE_STATS_PLACEMENT = "stats_placement"
TABLE_STATS_DIFF = "stats_diff"
TABLE_CONVERSIONS = "conversions"
TABLE_POSTCLICKSTATS = "postclickstats"
TABLE_OUTBRAINPUBLISHERSTATS = "outbrainpublisherstats"
TABLE_AUDIENCE_REPORT = "audience_report"
TABLE_PIXIE_SAMPLE = "pixie_sample"
TABLE_SUPPLY_STATS = "supply_stats"

STATS_DB_HOT_CLUSTER_RAW_TABLES = [
    TABLE_STATS,
    TABLE_STATS_PLACEMENT,
    TABLE_STATS_DIFF,
    TABLE_CONVERSIONS,
    TABLE_POSTCLICKSTATS,
    TABLE_OUTBRAINPUBLISHERSTATS,
    TABLE_AUDIENCE_REPORT,
    TABLE_PIXIE_SAMPLE,
]


class Command(Z1Command):
    @metrics_compat.timer("etl.vacuum_redshift_db")
    def handle(self, *args, **options):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(STATS_DB_CLUSTERS)) as executor:
            futures = [executor.submit(self._vacuum, db_name) for db_name in STATS_DB_CLUSTERS]
            concurrent.futures.wait(futures)

    @staticmethod
    def _vacuum(db_name):
        for table in refresh.get_all_views_table_names():
            vacuum_to = 99 if table in VACUUM_TO_99 else 95
            if table == "mv_master" and db_name == settings.STATS_DB_COLD_CLUSTERS[0]:
                continue  # HACK(nsaje): dont vacuum mv_master in cold cluster until we vacuum it manually, it just gets stuck
            maintenance.vacuum(table, to=vacuum_to, db_name=db_name)
            maintenance.analyze(table, db_name=db_name)

        if db_name != settings.STATS_DB_HOT_CLUSTER:
            return

        for table in STATS_DB_HOT_CLUSTER_RAW_TABLES:
            maintenance.vacuum(table, db_name=db_name)
            maintenance.analyze(table, db_name=db_name)

        maintenance.vacuum(TABLE_SUPPLY_STATS, delete_only=True, db_name=db_name)
        maintenance.analyze(TABLE_SUPPLY_STATS, db_name=db_name)
