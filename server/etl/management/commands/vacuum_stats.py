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
            'audience_report',
            'pixie_sample',
            'statsnew',
        ]

        for table in tables:
            with influx.block_timer('etl.vacuum', table=table):
                maintenance.vacuum(table)
                maintenance.analyze(table)

        table = 'supply_stats'
        with influx.block_timer('etl.vacuum', table=table):
            maintenance.vacuum(table, delete_only=True)
            maintenance.analyze(table)
