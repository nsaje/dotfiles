from django.core.management.base import BaseCommand

from reports import redshift

from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_gauge

from etl import redshift

class Command(ExceptionCommand):

    def handle(self, *args, **options):
        redshift.vacuum_and_analyze('publishers_1')
        redshift.vacuum_and_analyze('contentadstats')
        redshift.vacuum_and_analyze('touchpointconversions')








