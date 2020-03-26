import datetime
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import connections

import backtosql
import dash.models
import utils.dates_helper
from utils import converters
from utils import csv_utils
from utils import zlogging
from utils.email_helper import send_supply_report_email

logger = zlogging.getLogger(__name__)

all_sources_query = backtosql.generate_sql("sql/all_sources_stats_query.sql", None)
publisher_stats_query = backtosql.generate_sql("sql/publisher_stats_query.sql", None)


def send_supply_reports(recipient_ids=[], dry_run=False, skip_already_sent=False, overwrite_recipients_email=None):
    today = utils.dates_helper.local_today()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    month_start = datetime.datetime(yesterday.year, yesterday.month, 1)
    month_start_str = month_start.strftime("%Y-%m-%d")

    recipients = dash.models.SupplyReportRecipient.objects.all().prefetch_related("source")
    if recipient_ids:
        recipients = recipients.filter(id__in=recipient_ids)

    if skip_already_sent:
        recipients = recipients.filter(last_sent_dt__lt=datetime.date.today())

    if len(recipients) == 0:
        logger.info("No recipients.")
        return

    publisher_stats = {}
    mtd_stats = {}
    daily_breakdown_stats = {}

    all_sources_stats = _get_source_stats_from_query(
        all_sources_query.format(date_from=month_start_str, date_to=yesterday_str)
    )

    for recipient in recipients:
        source_id = recipient.source.pk
        source_stats = all_sources_stats.get(source_id, {yesterday_str: {"impressions": 0, "cost": 0}})
        dates = source_stats.keys()
        mtd_impressions = None
        mtd_cost = None

        impressions = source_stats.get(yesterday_str, {"impressions": 0})["impressions"]
        cost = source_stats.get(yesterday_str, {"cost": 0})["cost"]

        if recipient.mtd_report:
            if source_id not in mtd_stats:
                mtd_stats[source_id] = {
                    "impressions": sum(map(lambda date: source_stats[date]["impressions"], dates)),
                    "cost": sum(map(lambda date: source_stats[date]["cost"], dates)),
                }

            if mtd_stats[source_id]:
                mtd_impressions = mtd_stats[source_id]["impressions"]
                mtd_cost = mtd_stats[source_id]["cost"]

        publisher_report = None
        if recipient.publishers_report:
            if source_id not in publisher_stats:
                publisher_stats[source_id] = _get_publisher_stats(recipient, yesterday)

            if publisher_stats[source_id]:
                publisher_report = _create_csv(
                    ["Date", "Publisher", "Impressions", "Clicks", "Spend"], publisher_stats[source_id]
                )

        daily_breakdown_report = None
        if recipient.daily_breakdown_report:
            if source_id not in daily_breakdown_stats:
                daily_breakdown_stats[source_id] = list(
                    map(lambda date: [date, source_stats[date]["impressions"], source_stats[date]["cost"]], dates)
                )

            if daily_breakdown_stats[source_id]:
                daily_breakdown_report = _create_csv(["Date", "Impressions", "Spend"], daily_breakdown_stats[source_id])

        if dry_run:
            continue

        send_supply_report_email(
            overwrite_recipients_email or recipient.email,
            yesterday,
            impressions,
            cost,
            recipient.custom_subject,
            publisher_report=publisher_report,
            mtd_impressions=mtd_impressions,
            mtd_cost=mtd_cost,
            daily_breakdown_report=daily_breakdown_report,
        )
        if not overwrite_recipients_email:
            recipient.last_sent_dt = datetime.datetime.now()
            recipient.save()


def _get_source_stats_from_query(query):
    source_stats = defaultdict(dict)

    with connections[settings.STATS_DB_HOT_CLUSTER].cursor() as c:
        c.execute(query)
        for date, source_id_str, impressions, spend in c:
            source_id = int(source_id_str)
            source_stats[source_id][date] = {
                "impressions": int(impressions if impressions else 0),
                "cost": Decimal(spend if spend else 0) / converters.CURRENCY_TO_NANO,
            }
    return source_stats


def _get_publisher_stats(recipient, date):
    result = []
    params = [recipient.source.pk, date.isoformat()]

    with connections[settings.STATS_DB_HOT_CLUSTER].cursor() as c:
        c.execute(publisher_stats_query, params)
        for date, domain, impressions, clicks, cost_nano in c:
            cost_formatted = Decimal(cost_nano if cost_nano else 0) / converters.CURRENCY_TO_NANO
            result.append([date, domain, impressions, clicks, cost_formatted])

    return result


def _create_csv(columns, data):
    return csv_utils.tuplelist_to_csv([columns] + data)
