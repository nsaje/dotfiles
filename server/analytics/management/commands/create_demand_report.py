import logging

from django.core.management.base import BaseCommand

from analytics import demand_report

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Create demant report and upload it to Big Query"

    def handle(self, *args, **options):
        demand_report.create_report()
