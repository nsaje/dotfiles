import logging
import os.path
import io
import csv
import boto
import boto.s3

from django.conf import settings
from django.db import connections, transaction

from utils import s3helpers

from reports import daily_statements_k1
from reports import materialize_k1

logger = logging.getLogger(__name__)


MATERIALIZED_VIEWS = [
    materialize_k1.ContentAdStats(),
    materialize_k1.Publishers(),
]

MATERIALIZED_VIEWS_S3_PREFIX = 'materialized_views'
MATERIALIZED_VIEWS_FILENAME = 'view.csv'

S3_FILE_URI = 's3://{bucket_name}/{key}'
CSV_DELIMITER = '\t'


def refresh_k1_reports(update_since):
    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())
    generate_views(effective_spend_factors)


def generate_views(effective_spend_factors):
    for date, campaigns in sorted(effective_spend_factors.iteritems(), key=lambda x: x[0]):
        for mv in MATERIALIZED_VIEWS:
            _generate_table(date, mv, campaigns)


def _generate_table(date, materialized_view, campaign_factors):
    logger.info("Materializing table %s for date %s", materialized_view.table_name(), date)

    s3_path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        materialized_view.table_name(),
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME,
    )

    bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

    with io.BytesIO() as csvfile:
        writer = csv.writer(csvfile, dialect='excel', delimiter=CSV_DELIMITER)

        for line in materialized_view.generate_rows(date, campaign_factors):
            writer.writerow(line)

        bucket.put(s3_path, csvfile.getvalue())

    _load_to_redshift(date, materialized_view.table_name(), s3_path)


def _load_to_redshift(date, table_name, s3_path):
    with transaction.atomic(using=settings.K1_VIEWS_DB_NAME):
        _delete_from_redshift_table(table_name, date)
        _load_to_redshift_table(table_name, s3_path)


def _delete_from_redshift_table(table, date):
    logger.info("Deleting from redshift %s, %s", table, date)

    query = 'DELETE FROM {table} WHERE date = %s'.format(table=table)
    with connections[settings.K1_VIEWS_DB_NAME].cursor() as c:
        c.execute(query, [date.isoformat()])


def _load_to_redshift_table(table, s3_path):
    logger.info("Loading to redshift %s, %s", table, s3_path)

    query = """
        COPY {table}
        FROM %s
        FORMAT CSV
        DELIMITER AS %s
        CREDENTIALS %s
        MAXERROR 0
    """.format(table=table)

    s3_url = S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_path)

    if settings.AWS_ACCESS_KEY_ID is not None and settings.AWS_ACCESS_KEY_ID != '':
        credentials = _get_aws_credentials_string(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
        )
    else:
        credentials = _get_aws_credentials_from_role()

    with connections[settings.K1_VIEWS_DB_NAME].cursor() as c:
        c.execute(query, [s3_url, CSV_DELIMITER, credentials])


def _get_aws_credentials_string(aws_access_key_id, aws_secret_access_key):
    return 'aws_access_key_id={key};aws_secret_access_key={secret}'.format(
        key=aws_access_key_id,
        secret=aws_secret_access_key,
    )


def _get_aws_credentials_from_role():
    s3_client = boto.s3.connect_to_region('us-east-1')

    access_key = s3_client.aws_access_key_id
    access_secret = s3_client.aws_secret_access_key

    security_token_param = ''
    if s3_client.provider.security_token:
        security_token_param = ';token=%s' % s3_client.provider.security_token

    return 'aws_access_key_id=%s;aws_secret_access_key=%s%s' % (
        access_key, access_secret, security_token_param)
