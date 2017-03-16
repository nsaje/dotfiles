import datetime
import urllib

from django.conf import settings

import dash.models
import dash.constants
from redshiftapi.models import MVMaster
import redshiftapi.db
from utils import s3helpers
import utils.csv_utils

DOWNLOAD_URL = 'https://one.zemanta.com/api/custom_report_download/'
INVENTORY_REPORT_QUERY = """SELECT source_id, publisher, country, device_type,
  SUM(impressions)
FROM mv_pubs_master
WHERE date >= '{from_date}' AND date < current_date AND source_id not in (3, 4)
GROUP BY source_id, publisher, country, device_type;"""

SOURCE_PERFORMANCE_REPORT_QUERY = """SELECT source_id, {metrics}
FROM mv_master
WHERE date >= '{from_date}' AND date < '{till_date}'
GROUP BY source_id;"""


def get_media_source_performance_report(from_date, till_date):
    sources = {s.pk: s for s in dash.models.Source.objects.all()}
    query = SOURCE_PERFORMANCE_REPORT_QUERY.format(
        metrics=', '.join(map(lambda col: col.only_column(), [
            MVMaster.ctr, MVMaster.cpc, MVMaster.cpm,
            MVMaster.pv_per_visit, MVMaster.bounce_rate, MVMaster.avg_tos,
        ])),
        from_date=format(from_date),
        till_date=format(till_date),
    )
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(query)
        return [
            (sources[row[0]].name, ) + row[1:]
            for row in c.fetchall()
        ]


def get_inventory_report(days=30):
    sources = {s.pk: s for s in dash.models.Source.objects.all()}
    from_date = datetime.date.today() - datetime.timedelta(days)
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(INVENTORY_REPORT_QUERY.format(
            from_date=from_date,
            days=days
        ))
        return [
            (sources[row[0]], row[1], row[2], dash.constants.DeviceType.get_text(row[3]),
             row[4], float(row[4]) / days)
            for row in c.fetchall()
        ]


def inventory_report_csv(days=30):
    return utils.csv_utils.tuplelist_to_csv([
        ('Exchange', 'Publisher', 'Country', 'Device', 'Impressions', 'Avg. impressions per day')
    ] + get_inventory_report(days=days))


def media_source_performance_report_csv(from_date, till_date):
    return utils.csv_utils.tuplelist_to_csv([
        ('Media source', 'CTR', 'Avg. CPC', 'Avg. CPM',
         'Pageviews per Visit', 'Bounce Rate', 'Time on Site', )
    ] + get_media_source_performance_report(from_date, till_date))


def get_url(path):
    return DOWNLOAD_URL + '?' + urllib.urlencode({
        'path': path
    })


def generate_csv(path, report, *args, **kwargs):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    s3.put(path, report if type(report) == str else report(*args, **kwargs),
           human_readable_filename=path.split('/')[-1])
    return get_url(path)
