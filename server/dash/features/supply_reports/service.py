import datetime
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import connections

import backtosql
import dash.models
import utils.dates_helper
from utils import csv_utils
from utils import metrics_compat
from utils import zlogging
from utils.email_helper import send_supply_report_email

logger = zlogging.getLogger(__name__)

ALL_SOURCES_QUERY = backtosql.generate_sql("sql/all_sources_stats_query.sql", None)
TIMEZONE = "EST"


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

    all_sources_stats = _get_source_stats_from_query(month_start_str, yesterday_str)

    for recipient in recipients:
        with metrics_compat.block_timer(
            "supply_reports_timer",
            exchange=recipient.source.bidder_slug,
            mtd=str(recipient.mtd_report),
            publishers=str(recipient.publishers_report),
            daily=str(recipient.daily_breakdown_report),
            obpubs=str(bool(recipient.outbrain_publisher_ids)),
        ):
            stats_id = (recipient.source.pk,) + tuple(sorted(recipient.outbrain_publisher_ids or []))
            source_stats = {yesterday_str: _get_stats_obj()}
            if stats_id in all_sources_stats:
                source_stats = all_sources_stats[stats_id]
            elif recipient.outbrain_publisher_ids:
                source_stats = _get_source_stats_for_outbrain_publishers(recipient, month_start_str, yesterday_str)
                all_sources_stats[stats_id] = source_stats

            dates = source_stats.keys()
            mtd_impressions = None
            mtd_cost = None

            impressions = source_stats.get(yesterday_str, {"impressions": 0})["impressions"]
            cost = source_stats.get(yesterday_str, {"cost": 0})["cost"]

            if recipient.mtd_report:
                if stats_id not in mtd_stats:
                    mtd_stats[stats_id] = _get_stats_obj(
                        impressions=sum(map(lambda date: source_stats[date]["impressions"], dates)),
                        cost=sum(map(lambda date: source_stats[date]["cost"], dates)),
                    )

                if mtd_stats[stats_id]:
                    mtd_impressions = mtd_stats[stats_id]["impressions"]
                    mtd_cost = mtd_stats[stats_id]["cost"]

            publisher_report = None
            if recipient.publishers_report:
                if stats_id not in publisher_stats:
                    publisher_stats[stats_id] = _get_publisher_stats(recipient, yesterday)

                if publisher_stats[stats_id]:
                    publisher_report = _create_csv(
                        ["Date", "Publisher", "Impressions", "Clicks", "Spend"], publisher_stats[stats_id]
                    )

            daily_breakdown_report = None
            if recipient.daily_breakdown_report:
                if stats_id not in daily_breakdown_stats:
                    daily_breakdown_stats[stats_id] = list(
                        map(
                            lambda date: [date, source_stats[date]["impressions"], source_stats[date]["cost"]],
                            sorted(dates),
                        )
                    )

                if daily_breakdown_stats[stats_id]:
                    daily_breakdown_report = _create_csv(
                        ["Date", "Impressions", "Spend"], daily_breakdown_stats[stats_id]
                    )

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
            metrics_compat.incr("supply_reports_counter", 1, exchange=recipient.source.bidder_slug)
            if not overwrite_recipients_email:
                recipient.last_sent_dt = datetime.datetime.now()
                recipient.save()


def _get_source_stats_from_query(date_from_str, date_to_str):
    query = ALL_SOURCES_QUERY.format(date_from=date_from_str, date_to=date_to_str)
    source_stats = defaultdict(dict)

    with connections[settings.STATS_DB_HOT_CLUSTER].cursor() as c:
        c.execute(query)
        for date, source_id, impressions, spend in c:
            stats_id = (source_id,)
            source_stats[stats_id][date] = _get_stats_obj(impressions, spend)
    return source_stats


def _get_source_stats_for_outbrain_publishers(recipient, start_date, end_date):
    query = _get_custom_stats_query(recipient, "date", start_date, end_date)
    out = {}
    with connections[settings.STATS_DB_HOT_CLUSTER].cursor() as c:
        c.execute(query)
        for date, impressions, _, spend in c.fetchall():
            out[str(date)] = _get_stats_obj(impressions, spend)
        return out
    return []


def _get_publisher_stats(recipient, date):
    query = (
        _get_custom_stats_query(recipient, "date,publisher", date, date)
        if recipient.outbrain_publisher_ids
        else backtosql.generate_sql(
            "sql/publisher_stats_query.sql", dict(source_id=recipient.source.pk, date=date.isoformat())
        )
    )
    result = []

    with connections[settings.STATS_DB_HOT_CLUSTER].cursor() as c:
        c.execute(query)
        for date, domain, impressions, clicks, cost in c.fetchall():
            result.append([date, domain, impressions, clicks, cost])

    return result


def _get_custom_stats_query(recipient, breakdown, start_date, end_date):
    return backtosql.generate_sql(
        "sql/custom_stats_query.sql",
        dict(
            bidder_slug=recipient.source.bidder_slug,
            breakdown=breakdown,
            outbrain_publisher_ids=",".join("'{}'".format(pubid) for pubid in recipient.outbrain_publisher_ids),
            timezone=TIMEZONE,
            start_date=start_date,
            end_date=end_date,
        ),
    )


def _get_stats_obj(impressions=None, cost=None):
    return {"impressions": int(impressions or 0), "cost": Decimal(cost or 0)}


def _create_csv(columns, data):
    return csv_utils.tuplelist_to_csv([columns] + data)
