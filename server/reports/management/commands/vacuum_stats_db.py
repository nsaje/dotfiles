from django.core.management.base import BaseCommand

from reports import redshift

from utils.statsd_helper import statsd_gauge


class Command(BaseCommand):

    def handle(self, *args, **options):
        redshift.vacuum_contentadstats()
        redshift.vacuum_touchpoint_conversions()
        statsd_gauge('reports.redshift.vacuum_stats', 1)
