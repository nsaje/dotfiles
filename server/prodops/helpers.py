from django.conf import settings

from utils import s3helpers
import analytics.statements
import utils.csv_utils


def upload_report_from_fs(path, filepath):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    with open(filepath) as fd:
        s3.put(path, fd.read(),
               human_readable_filename=filepath.split('/')[-1])
    return analytics.statements.get_url(path)


def generate_report(name, data):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    path = '/custom-csv/{}.csv'.format(name)
    s3.put(path, utils.csv_utils.tuplelist_to_csv(data))
    return analytics.statements.get_url(path)
