from utils.command_helpers import ExceptionCommand

from etl import maintenance


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        maintenance.vacuum_and_analyze('publishers_1')
        maintenance.vacuum_and_analyze('contentadstats')
        maintenance.vacuum_and_analyze('touchpointconversions')
