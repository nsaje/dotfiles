from django.core.management.base import BaseCommand

import reports.refresh


class Command(BaseCommand):

    def handle(self, *args, **options):
        reports.refresh.refresh_changed_campaign_data()
