import csv
import io
import logging
from functools import partial

from django.conf import settings

from utils import s3helpers
from utils import threads
from . import constants

logger = logging.getLogger(__name__)


def _do_upload_csv(s3_path, generator, bucket_name=None):
    bucket = s3helpers.S3Helper(bucket_name=bucket_name or settings.S3_BUCKET_STATS)

    with io.StringIO() as csvfile:
        writer = csv.writer(csvfile, dialect="excel", delimiter=constants.CSV_DELIMITER)

        for line in generator():
            writer.writerow(line)

        bucket.put(s3_path, csvfile.getvalue())

    return s3_path


def upload_csv_async(s3_path, generator, bucket_name=None):
    logger.info("Create async CSV to: %s", s3_path)
    t = threads.AsyncFunction(partial(_do_upload_csv, s3_path, generator, bucket_name=bucket_name))
    t.start()

    return t, s3_path


def upload_csv(s3_path, generator, bucket_name=None):
    logger.info("Create CSV to: %s", s3_path)

    _do_upload_csv(s3_path, generator, bucket_name=bucket_name)

    logger.info("CSV to: %s uploaded", s3_path)
    return s3_path
