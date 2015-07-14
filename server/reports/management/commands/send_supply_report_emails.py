import datetime
import logging

import pytz

from django.conf import settings
from django.core.management.base import BaseCommand

import reports.models
import reports.api
import utils.email_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):
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
        stats = reports.api.query(yesterday, yesterday, ['source'], source=source_ids)

        source_stats = {stat['source']: {'impressions': stat['impressions'], 'cost': stat['cost']} for stat in stats}

        for recipient in recipients:
            if recipient.source.pk not in source_stats:
                continue

            utils.email_helper.send_supply_report_email(
                    recipient.email,
                    yesterday,
                    source_stats[recipient.source.pk]['impressions'],
                    source_stats[recipient.source.pk]['cost']
            )
