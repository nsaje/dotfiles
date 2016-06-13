import backtosql
import logging
import os.path
import io
import unicodecsv as csv
import boto
import boto.s3

from django.conf import settings

from utils import s3helpers
from redshiftapi.db import get_write_stats_cursor, get_write_stats_transaction


logger = logging.getLogger(__name__)


MATERIALIZED_VIEWS_S3_PREFIX = 'materialized_views'
MATERIALIZED_VIEWS_FILENAME = 'view.csv'

S3_FILE_URI = 's3://{bucket_name}/{key}'
CSV_DELIMITER = '\t'


class TempTableMixin(object):
    def clear_data(self, cursor, date_from, date_to, **kwargs):
        sql, params = self.prepare_drop_query()
        cursor.execute(sql, params)

        sql, params = self.prepare_create_table_query()
        cursor.execute(sql, params)

    def prepare_drop_query(self):
        sql = backtosql.generate_sql('etl_drop_table.sql', {
            'table': self.table_name(),
        })

        return sql, {}

    def prepare_create_table_query(self):
        return backtosql.generate_sql(self.create_table_template_name(), None), {}

    def create_table_template_name(self):
        raise NotImplementedError()


class Materialize(object):
    def table_name(self):
        raise NotImplementedError()

    def generate(self, date_from, date_to, **kwargs):
        logger.info("Materializing table %s for dates %s - %s", self.table_name(), date_from, date_to)
        with get_write_stats_transaction():
            with get_write_stats_cursor() as c:
                self.clear_data(c, date_from, date_to)
                self.insert_data(c, date_from, date_to, **kwargs)

        logger.info("Done materializing table %s for dates %s - %s", self.table_name(), date_from, date_to)

    def clear_data(self, cursor, date_from, date_to):
        del_sql, del_params = self.prepare_delete_query(date_from, date_to)
        cursor.execute(del_sql, del_params)

    def insert_data(self, cursor, date_from, date_to, **kwargs):
        sql, params = self.prepare_insert_query(date_from, date_to, **kwargs)
        cursor.execute(sql, params)

    def prepare_delete_query(self, date_from, date_to):
        sql = backtosql.generate_sql('etl_delete.sql', {
            'table': self.table_name(),
        })

        return sql, {
            'date_from': date_from,
            'date_to': date_to,
        }

    def prepare_insert_query(self, date_from, date_to, **kwargs):
        raise NotImplementedError()


class MaterializeViaCSV(Materialize):

    def generate(self, date_from, date_to, **kwargs):
        s3_paths = self.generate_csvs(date_from, date_to, **kwargs)

        super(MaterializeViaCSV, self).generate(date_from, date_to, s3_paths=s3_paths)

    def generate_csvs(self, date_from, date_to, **kwargs):
        s3_path = os.path.join(
            MATERIALIZED_VIEWS_S3_PREFIX,
            self.table_name(),
            date_to.strftime("%Y/%m/%d/"),
            MATERIALIZED_VIEWS_FILENAME,
        )

        bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

        with io.BytesIO() as csvfile:
            writer = csv.writer(csvfile, dialect='excel', delimiter=CSV_DELIMITER)

            for line in self.generate_rows(date_from, date_to, **kwargs):
                writer.writerow(line)

            bucket.put(s3_path, csvfile.getvalue())

        return [s3_path]

    def insert_data(self, cursor, date_from, date_to, s3_paths):
        for s3_path in s3_paths:
            sql, params = self.prepare_insert_query(s3_path)
            cursor.execute(sql, params)

    def prepare_insert_query(self, s3_path):
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

    def generate_rows(self, date_from, date_to, **kwargs):
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
