from django.core.management.base import BaseCommand

import reports.refresh


class Command(BaseCommand):

    help = "Refreshes data in Redshift for all campaigns marked as changed"

    def handle(self, *args, **options):
        reports.refresh.refresh_changed_campaign_data()
