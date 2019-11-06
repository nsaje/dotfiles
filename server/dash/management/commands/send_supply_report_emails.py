import datetime
from decimal import Decimal

import pytz
from django.conf import settings
from django.db import connections

import dash.models
import utils.email_helper
import utils.pagerduty_helper as pgdh
from etl import helpers
from utils import converters
from utils import csv_utils
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    @pgdh.catch_and_report_exception(pgdh.PagerDutyEventType.PRODOPS)
    def handle(self, *args, **options):
        today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
        today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
        today = datetime.datetime(today.year, today.month, today.day)
        yesterday = today - datetime.timedelta(days=1)

        recipients = dash.models.SupplyReportRecipient.objects.all().prefetch_related("source")
        if len(recipients) == 0:
            logger.info("No recipients.")
            return

        source_stats = {}
        publisher_stats = {}

        sources = dash.models.Source.objects.all()
        sources_by_slug = {x.bidder_slug: x for x in sources}

        query = """
            select media_source, sum(impressions), sum(spend)
            from (SELECT * FROM stats_diff UNION ALL SELECT * FROM stats) AS stats
            where {date_query}
            group by media_source
        """.format(
            date_query=helpers.get_local_date_query(yesterday.date())
        )

        with connections[settings.STATS_DB_NAME].cursor() as c:
            c.execute(query)

            for media_source, impressions, spend in c:
                source_stats[sources_by_slug[media_source].pk] = {
                    "impressions": impressions,
                    "cost": Decimal(spend) / converters.CURRENCY_TO_MICRO,
                }

        for recipient in recipients:
            impressions = 0
            cost = 0
            if recipient.source.pk in source_stats:
                impressions = source_stats[recipient.source.pk]["impressions"]
                cost = source_stats[recipient.source.pk]["cost"]

            if recipient.publishers_report and recipient.source.pk not in publisher_stats:
                publisher_stats[recipient.source.pk] = self.get_publisher_stats(recipient, yesterday)

            publisher_report = None
            if recipient.source.pk in publisher_stats and publisher_stats[recipient.source.pk]:
                publisher_report = self.create_csv(
                    ["Date", "Publisher", "Impressions", "Clicks", "Spend"], publisher_stats[recipient.source.pk]
                )

            utils.email_helper.send_supply_report_email(
                recipient.email,
                yesterday,
                impressions,
                cost,
                recipient.custom_subject,
                publisher_report=publisher_report,
            )

    def get_publisher_stats(self, recipient, date):
        query = """
            select to_char(date, 'YYYY-MM-DD') as date, publisher, sum(coalesce(impressions, 0)), sum(coalesce(clicks, 0)), sum(coalesce(cost_nano, 0))
            from mv_master
            where source_id=%s and date=%s
            group by date, publisher
        """

        result = []

        params = [recipient.source.pk, date.date().isoformat()]

        with connections[settings.STATS_DB_NAME].cursor() as c:
            c.execute(query, params)
            for date, domain, impressions, clicks, cost_nano in c:
                cost_formatted = Decimal(cost_nano if cost_nano else 0) / converters.CURRENCY_TO_NANO
                result.append([date, domain, impressions, clicks, cost_formatted])

        return result

    def create_csv(self, columns, data):
        return csv_utils.tuplelist_to_csv([columns] + data)
