from utils.command_helpers import ExceptionCommand

from etl import maintenance

import influx


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        tables = [
            'stats',
            'conversions',
            'postclickstats',
            'outbrainpublisherstats',
            'supply_stats',
            'audience_report',
            'pixie_sample',
        ]

        for table in tables:
            with influx.timer('etl.vacuum', table=table):
                maintenance.vacuum_and_analyze(table)
