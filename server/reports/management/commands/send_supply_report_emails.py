import datetime
import logging
from decimal import Decimal
import cStringIO

import pytz
import unicodecsv

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

        recipients = reports.models.SupplyReportRecipient.objects.all().prefetch_related('source')
        if len(recipients) == 0:
            logger.info('No recipients.')
            return

        source_stats = {}
        publisher_stats = {}

        sources = dash.models.Source.objects.all()
        sources_by_slug = {x.bidder_slug: x for x in sources}

        query = """
            select media_source, sum(impressions), sum(spend)
            from stats
            where {date_query}
            group by media_source
        """.format(date_query=helpers.get_local_date_query(yesterday.date()))

        with connections[settings.STATS_DB_NAME].cursor() as c:
            c.execute(query)

            for media_source, impressions, spend in c:
                source_stats[sources_by_slug[media_source].pk] = {
                    'impressions': impressions,
                    'cost': Decimal(spend) / converters.DOLAR_TO_MICRO,
                }

        for recipient in recipients:
            impressions = 0
            cost = 0
            if recipient.source.pk in source_stats:
                impressions = source_stats[recipient.source.pk]['impressions']
                cost = source_stats[recipient.source.pk]['cost']

            if recipient.publishers_report and recipient.source.pk not in publisher_stats:
                start_dt = yesterday - datetime.timedelta(days=7)
                publisher_stats[recipient.source.pk] = self.get_publisher_stats(recipient, start_dt, today)

            publisher_report = None
            if recipient.source.pk in publisher_stats and publisher_stats[recipient.source.pk]:
                publisher_report = self.create_csv(
                    ["Date", "Publisher", "Impressions", "Clicks", "Spend"],
                    publisher_stats[recipient.source.pk]
                )

            utils.email_helper.send_supply_report_email(
                recipient.email,
                yesterday,
                impressions,
                cost,
                publisher_report=publisher_report
            )

    def get_publisher_stats(self, recipient, start_dt, end_dt):
        query = """
            select to_char(date, 'YYYY-MM-DD') as date, domain, sum(impressions), sum(clicks), sum(cost_nano)
            from publishers_1
            where exchange=%s and date>=%s and date<%s
            group by date, domain
            order by date
        """

        result = []

        params = [recipient.source.bidder_slug, start_dt.date().isoformat(), end_dt.date().isoformat()]

        with connections[settings.STATS_DB_NAME].cursor() as c:
            c.execute(query, params)
            for date, domain, impressions, clicks, cost_nano in c:
                cost_formatted = Decimal(cost_nano) / converters.DOLAR_TO_NANO
                result.append([date, domain, impressions, clicks, cost_formatted])

        return result

    def create_csv(self, columns, data):
        output = cStringIO.StringIO()
        writer = unicodecsv.writer(output, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
        writer.writerow(columns)
        for row in data:
            writer.writerow(row)

        return output.getvalue()
