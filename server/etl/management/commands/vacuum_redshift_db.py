from utils.command_helpers import ExceptionCommand

from etl import maintenance


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        tables = [
            'publishers_1',
            'contentadstats',
            'touchpointconversions',
            'mv_account',
            'mv_account_delivery',
            'mv_campaign',
            'mv_campaign_delivery',
            'mv_master',
            'mvh_adgroup_structure',
            'mvh_campaign_factors',
            'mvh_clean_stats',
            'mvh_source',
        ]

        for table in tables:
            maintenance.vacuum_and_analyze(table)
