import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

import dash.models
import reports.refresh

from utils import dates_helper
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    help = "Marks all non-archived campaigns' Redshift data to be updated in the next batch"

    def handle(self, *args, **options):
        today = dates_helper.local_today()
        for campaign in dash.models.Campaign.objects.all().exclude_archived():
            for days in range(1, settings.LAST_N_DAY_REPORTS + 1):
                reports.refresh.notify_contentadstats_change(today - datetime.timedelta(days=days), campaign.id)
