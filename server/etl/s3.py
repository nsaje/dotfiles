import csv
import io
import logging
import os.path
from functools import partial

from django.conf import settings

from utils import s3helpers
from utils import threads
from . import constants

logger = logging.getLogger(__name__)

MATERIALIZED_VIEWS_S3_PREFIX = "materialized_views"
MATERIALIZED_VIEWS_FILENAME = "{}_{}.csv"


def _do_upload_csv(s3_path, generator, bucket_name=None):
    bucket = s3helpers.S3Helper(bucket_name=bucket_name or settings.S3_BUCKET_STATS)

    with io.StringIO() as csvfile:
        writer = csv.writer(csvfile, dialect="excel", delimiter=constants.CSV_DELIMITER)

        for line in generator():
            writer.writerow(line)

        bucket.put(s3_path, csvfile.getvalue())


def upload_csv_async(table_name, date, job_id, generator):
    logger.info('Create async CSV for table "%s", job %s', table_name, job_id)
    s3_path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        table_name,
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME.format(table_name, job_id),
    )

    t = threads.AsyncFunction(partial(_do_upload_csv, s3_path, generator))
    t.start()

    return t, s3_path


def upload_csv(table_name, date, job_id, generator):
    logger.info('Create CSV for table "%s", job %s', table_name, job_id)
    s3_path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        table_name,
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME.format(table_name, job_id),
    )

    _do_upload_csv(s3_path, generator)
    logger.info('CSV for table "%s", job %s uploaded', table_name, job_id)

    return s3_path


def upload_csv_without_job(table_name, generator, s3_path, bucket_name):
    logger.info('Create CSV for table "%s"', table_name)
    _do_upload_csv(s3_path, generator, bucket_name=bucket_name)
    logger.info('CSV for table "%s" uploaded', table_name)
    return s3_path
