import backtosql
import gzip
import logging
import os.path

from django.conf import settings

from redshiftapi import db
from utils import s3helpers

from . import constants

MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX = "materialized_views_replication"
DUMP_S3_PREFIX = "debug_dumps"
S3_FILE_URI = "s3://{bucket_name}/{key}"

logger = logging.getLogger(__name__)


def unload_table(
    job_id, table_name, date_from, date_to, account_id=None, prefix=MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX
):
    s3_path = os.path.join(
        prefix,
        job_id,
        table_name,
        "{}-{}-{}-{}".format(table_name, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"), account_id or 0),
    )
    with db.get_write_stats_cursor() as c:
        logger.info('Unloading table "%s" to S3 path "%s"', table_name, s3_path)
        sql, params = prepare_unload_csv_query(s3_path, table_name, date_from, date_to, account_id)
        c.execute(sql, params)
        logger.info('Unloaded table "%s" to S3 path "%s"', table_name, s3_path)
    return s3_path + "manifest"


def update_table_from_s3(db_name, s3_manifest_path, table_name, date_from, date_to, account_id=None):
    with db.get_write_stats_transaction(db_name):
        with db.get_write_stats_cursor(db_name) as c:
            logger.info('Loading table "%s" into replica "%s" from S3 path "%s"', table_name, db_name, s3_manifest_path)

            sql, params = prepare_date_range_delete_query(table_name, date_from, date_to, account_id)
            c.execute(sql, params)

            sql, params = prepare_copy_csv_query(
                s3_manifest_path,
                table_name,
                format_csv=False,
                removequotes=False,
                escape=True,
                is_manifest=True,
                null_as="$NA$",
                gzip=True,
            )
            c.execute(sql, params)

            logger.info('Loaded table "%s" into replica "%s" from S3 path "%s"', table_name, db_name, s3_manifest_path)


def update_table_from_s3_postgres(db_name, s3_manifest_path, table_name, date_from, date_to, account_id=None):
    with db.get_write_stats_transaction(db_name):
        with db.get_write_stats_cursor(db_name) as c:
            logger.info(
                'Loading table "%s" into Postgres replica "%s" from S3 path "%s"', table_name, db_name, s3_manifest_path
            )

            sql, params = prepare_date_range_delete_query(table_name, date_from, date_to, account_id)
            c.execute(sql, params)

            bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)
            keys = bucket.list_manifest(s3_manifest_path)
            for f in bucket.open_keys_async(keys):
                with gzip.GzipFile(fileobj=f, mode="rb") as gunzipped:
                    c.copy_expert("COPY %s FROM STDIN NULL '$NA$'" % table_name, gunzipped)

            logger.info(
                'Loaded table "%s" into Postgres replica "%s" from S3 path "%s"', table_name, db_name, s3_manifest_path
            )


def prepare_unload_csv_query(s3_path, table_name, date_from, date_to, account_id=None):
    sql = backtosql.generate_sql(
        "etl_unload_csv.sql",
        {
            "table": table_name,
            "date_from_str": date_from.strftime("%Y-%m-%d"),
            "date_to_str": date_to.strftime("%Y-%m-%d"),
            "account_id_str": str(account_id) if account_id else None,
        },
    )

    s3_url = S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_path)
    credentials = _get_aws_credentials()

    return sql, {"s3_url": s3_url, "credentials": credentials, "delimiter": constants.CSV_DELIMITER}


def prepare_copy_csv_query(
    s3_path, table_name, format_csv=True, removequotes=False, escape=False, is_manifest=False, null_as=None, gzip=False
):
    sql = backtosql.generate_sql(
        "etl_copy_csv.sql",
        {
            "table": table_name,
            "is_manifest": is_manifest,
            "format_csv": format_csv,
            "removequotes": removequotes,
            "escape": escape,
            "null_as": null_as,
            "gzip": gzip,
        },
    )

    s3_url = S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_path)
    credentials = _get_aws_credentials()

    return sql, {"s3_url": s3_url, "credentials": credentials, "delimiter": constants.CSV_DELIMITER}


def _get_aws_credentials():
    return s3helpers.get_credentials_string()


def prepare_daily_delete_query(table_name, date, account_id):
    sql = backtosql.generate_sql("etl_daily_delete.sql", {"table": table_name, "account_id": account_id})

    params = {"date": date}

    if account_id:
        params["account_id"] = account_id

    return sql, params


def prepare_date_range_delete_query(table_name, date_from, date_to, account_id):
    sql = backtosql.generate_sql("etl_delete.sql", {"table": table_name, "account_id": account_id})

    params = {"date_from": date_from, "date_to": date_to}

    if account_id:
        params["account_id"] = account_id

    return sql, params
