import backtosql
import logging
import os.path
import io
import unicodecsv as csv
import boto
import boto.s3

from django.conf import settings
from django.db import connections, transaction

from utils import s3helpers

from etl import daily_statements_k1


logger = logging.getLogger(__name__)


MATERIALIZED_VIEWS_S3_PREFIX = 'materialized_views'
MATERIALIZED_VIEWS_FILENAME = 'view.csv'

S3_FILE_URI = 's3://{bucket_name}/{key}'
CSV_DELIMITER = '\t'


class Materialize(object):
    def table_name(self):
        raise NotImplementedError()

    def generate(self, date, *args, **kwargs):
        del_sql, del_params = self.prepare_delete_query(date)
        ins_sql, ins_params = self.prepare_insert_query(date)

        logger.info("Materializing table %s for date %s", self.table_name(), date)
        with transaction.atomic(using=settings.K1_VIEWS_DB_NAME):
            with connections[settings.K1_VIEWS_DB_NAME].cursor() as c:
                c.execute(del_sql, del_params)
                c.execute(ins_sql, ins_params)

        logger.info("Done materializing table %s for date %s", self.table_name(), date)

    def prepare_delete_query(self, date):
        sql = backtosql.generate_sql('etl_delete_simple_one_day.sql', {
            'table': self.table_name(),
        })

        return sql, {'date': date}

    def prepare_insert_query(self, date):
        raise NotImplementedError()


class TransformAndMaterialize(Materialize):
    def generate(self, date, daily_campaign_spend_factors, *args, **kwargs):
        logger.info("Materializing table %s for date %s", self.table_name(), date)

        s3_path = os.path.join(
            MATERIALIZED_VIEWS_S3_PREFIX,
            self.table_name(),
            date.strftime("%Y/%m/%d/"),
            MATERIALIZED_VIEWS_FILENAME,
        )

        bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

        with io.BytesIO() as csvfile:
            writer = csv.writer(csvfile, dialect='excel', delimiter=CSV_DELIMITER)

            for line in self.generate_rows(date, campaign_factors):
                writer.writerow(line)

            bucket.put(s3_path, csvfile.getvalue())

        del_sql, del_params = self.prepare_delete_query(date)
        ins_sql, ins_params = self.prepare_insert_query(date, s3_path)

        with transaction.atomic(using=settings.K1_VIEWS_DB_NAME):
            with connections[settings.K1_VIEWS_DB_NAME].cursor() as c:
                c.execute(del_sql, del_params)
                c.execute(ins_sql, ins_params)

    def prepare_insert_query(self, date, s3_path):
        sql = backtosql.generate_sql('etl_copy_csv.sql', {
            'table': self.table_name(),
        })

        s3_url = S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_path)

        if settings.AWS_ACCESS_KEY_ID is not None and settings.AWS_ACCESS_KEY_ID != '':
            credentials = _get_aws_credentials_string(
                settings.AWS_ACCESS_KEY_ID,
                settings.AWS_SECRET_ACCESS_KEY,
            )
        else:
            credentials = _get_aws_credentials_from_role()

        return sql, {
            's3_url': s3_url,
            'credentials': credentials,
            'delimiter': CSV_DELIMITER,
        }

    def generate_rows(self):
        raise NotImplementedError()


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
