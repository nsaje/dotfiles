import StringIO

import unicodecsv as csv
from django.conf import settings

from utils import s3helpers
import analytics.statements


def upload_report_from_fs(path, filepath):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    with open(filepath) as fd:
        s3.put(path, fd.read(),
               human_readable_filename=filepath.split('/')[-1])
    return analytics.statements.get_url(path)


def generate_report(name, data):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    out = StringIO.StringIO()
    csv_file = csv.writer(out, delimiter='\t')
    for row in data:
        csv_file.writerow(row)
    path = '/custom-csv/{}.csv'.format(name)
    s3.put(path, out.getvalue())
    return analytics.statements.get_url(path)
