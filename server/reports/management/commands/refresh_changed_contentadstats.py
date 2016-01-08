from django.core.management.base import BaseCommand

import reports.refresh
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    help = "Refreshes data in Redshift for all campaigns marked as changed"

    def handle(self, *args, **options):
        reports.refresh.refresh_changed_contentadstats()
