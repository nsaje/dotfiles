import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

import dash.models
import reports.refresh

from utils import dates_helper


class Command(BaseCommand):

    help = "Marks all non-archived campaigns' Redshift data to be updated in the next batch"

    def handle(self, *args, **options):
        today = dates_helper.local_today()
        for campaign in dash.models.Campaign.objects.exclude_archived():
            for days in range(settings.LAST_N_DAY_REPORTS):
                reports.refresh.notify_contentadstats_change(today - datetime.timedelta(days=days), campaign.id)
