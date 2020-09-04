import urllib.error
import urllib.parse
import urllib.request

import dash.constants
import dash.models
import redshiftapi.db
import utils.csv_utils
from redshiftapi.models import MVMaster

DOWNLOAD_URL = "https://one.zemanta.com/api/custom_report_download/"

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


def media_source_performance_report_csv(from_date, till_date):
    return utils.csv_utils.tuplelist_to_csv(
        [("Media source", "CTR", "Avg. CPC", "Avg. CPM", "Pageviews per Visit", "Bounce Rate", "Time on Site")]
        + get_media_source_performance_report(from_date, till_date)
    )


def get_url(path):
    return DOWNLOAD_URL + "?" + urllib.parse.urlencode({"path": path})
