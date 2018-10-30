import datetime
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

import dash.constants
import dash.models
import redshiftapi.db
import utils.csv_utils
from redshiftapi.models import MVMaster
from utils import s3helpers

DOWNLOAD_URL = "https://one.zemanta.com/api/custom_report_download/"
INVENTORY_REPORT_QUERY = """SELECT {breakdown}, SUM(bid_reqs)
FROM supply_stats
WHERE date >= '{from_date}' AND date < current_date AND blacklisted = {bl}
GROUP BY {breakdown};"""

SOURCE_PERFORMANCE_REPORT_QUERY = """SELECT source_id, {metrics}
FROM mv_master
WHERE date >= '{from_date}' AND date < '{till_date}'
GROUP BY source_id;"""

BIDDER_DEVICE_TYPES = {
    0: "unknown",
    1: "mobile",
    2: "PC",
    3: "TV",
    4: "phone",
    5: "tablet",
    6: "connected",
    7: "settopbox",
}


def get_media_source_performance_report(from_date, till_date):
    sources = {s.pk: s for s in dash.models.Source.objects.all()}
    query = SOURCE_PERFORMANCE_REPORT_QUERY.format(
        metrics=", ".join(
            [
                col.only_column()
                for col in [
                    MVMaster.ctr,
                    MVMaster.cpc,
                    MVMaster.cpm,
                    MVMaster.pv_per_visit,
                    MVMaster.bounce_rate,
                    MVMaster.avg_tos,
                ]
            ]
        ),
        from_date=format(from_date),
        till_date=format(till_date),
    )
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(query)
        return [(sources[row[0]].name,) + row[1:] for row in c.fetchall()]


def get_inventory_report(days=30, blacklisted=False):
    sources = {s.get_clean_slug(): s for s in dash.models.Source.objects.all()}
    from_date = datetime.date.today() - datetime.timedelta(days)
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(
            INVENTORY_REPORT_QUERY.format(
                breakdown="exchange, country, device_type", from_date=from_date, days=days, bl=1 if blacklisted else 0
            )
        )
        return [
            (sources[row[0]], row[1], BIDDER_DEVICE_TYPES.get(row[2], "undefined"), row[3], float(row[3]) / days)
            for row in c.fetchall()
        ]


def inventory_report_csv(days=30, blacklisted=False):
    return utils.csv_utils.tuplelist_to_csv(
        [("Exchange", "Country", "Device", "Impressions on offer", "Avg. impressions on offer per day")]
        + get_inventory_report(days=days, blacklisted=blacklisted)
    )


def media_source_performance_report_csv(from_date, till_date):
    return utils.csv_utils.tuplelist_to_csv(
        [("Media source", "CTR", "Avg. CPC", "Avg. CPM", "Pageviews per Visit", "Bounce Rate", "Time on Site")]
        + get_media_source_performance_report(from_date, till_date)
    )


def get_url(path):
    return DOWNLOAD_URL + "?" + urllib.parse.urlencode({"path": path})


def generate_csv(path, report, *args, **kwargs):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    s3.put(
        path, report if type(report) == str else report(*args, **kwargs), human_readable_filename=path.split("/")[-1]
    )
    return get_url(path)
