import datetime
import logging
from decimal import Decimal

import pytz

from django.conf import settings
from django.db import connections

import dash.models
import reports.models
import reports.api
from etl import helpers

import utils.email_helper
from utils.command_helpers import ExceptionCommand
from utils import converters

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

        source_stats = {}

        query = """
            select media_source, sum(impressions), sum(spend)
            from stats
            where {date_query}
            group by media_source
        """.format(date_query=helpers.get_local_date_query(yesterday.date()))

        with connections[settings.STATS_DB_NAME].cursor() as c:
            c.execute(query)

            for media_source, impressions, spend in c:
                source = dash.models.Source.objects.get(bidder_slug=media_source)
                source_stats[source.pk] = {
                    'impressions': impressions,
                    'cost': Decimal(spend) / converters.DOLAR_TO_MICRO,
                }

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
