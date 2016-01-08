from django.core.management.base import BaseCommand

import reports.refresh


class Command(BaseCommand):

    help = "Refreshes dialy statements for all campaigns marked as changed"

    def handle(self, *args, **options):
        reports.refresh.refresh_changed_contentadstats()
