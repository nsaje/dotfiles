import datetime
import logging

import pytz

from django.conf import settings
from django.core.management.base import BaseCommand

import dash.models
import reports.models
import reports.api
import utils.email_helper
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
        today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
        today = datetime.datetime(today.year, today.month, today.day)
        yesterday = today - datetime.timedelta(days=1)

        recipients = reports.models.SupplyReportRecipient.objects.all()
        if len(recipients) == 0:
            logger.info('No recipients.')
            return

        source_ids = [recipient.source.pk for recipient in recipients]
        ad_groups = dash.models.AdGroup.objects.filter(is_demo=False)
        stats = reports.api.query(yesterday, yesterday, ['source'], source=source_ids, ad_group=ad_groups)

        source_stats = {stat['source']: {'impressions': stat['impressions'], 'cost': stat['cost']} for stat in stats}

        for recipient in recipients:
            impressions = 0
            cost = 0
            if recipient.source.pk in source_stats:
                impressions = source_stats[recipient.source.pk]['impressions']
                cost = source_stats[recipient.source.pk]['cost']

            utils.email_helper.send_supply_report_email(
                    recipient.email,
                    yesterday,
                    impressions,
                    cost
            )
