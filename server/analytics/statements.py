import datetime
import unicodecsv as csv
import StringIO
import urllib

from django.conf import settings

import dash.models
import dash.constants
import redshiftapi.db
from utils import s3helpers

DOWNLOAD_URL = 'https://one.zemanta.com/api/custom_report_download/'
INVENTORY_REPORT_QUERY = """SELECT source_id, publisher, country, device_type,
  SUM(impressions)
FROM mv_pubs_master
WHERE date >= '{from_date}' AND date < current_date AND source_id not in (3, 4)
GROUP BY source_id, publisher, country, device_type;"""


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
    report = get_inventory_report(days=days)
    out = StringIO.StringIO()
    csv_file = csv.writer(out, delimiter='\t')
    csv_file.writerow((
        'Exchange', 'Publisher', 'Country', 'Device', 'Impressions', 'Avg. impressions per day'
    ))
    for row in report:
        csv_file.writerow(row)
    return out.getvalue()


def get_url(path):
    return DOWNLOAD_URL + '?' + urllib.urlencode({
        'path': path
    })


def generate_csv(path, report, *args, **kwargs):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    s3.put(path, report(*args, **kwargs))
    return get_url(path)
