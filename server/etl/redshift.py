import gzip
import os.path

from django.conf import settings

import backtosql
from redshiftapi import db
from utils import s3helpers
from utils import zlogging

from . import constants
from . import helpers

MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX = "materialized_views_replication"
DUMP_S3_PREFIX = "debug_dumps"
S3_FILE_URI = "s3://{bucket_name}/{key}"

logger = zlogging.getLogger(__name__)


def unload_table(
    job_id,
    table_name,
    date_from,
    date_to,
    account_id=None,
    prefix=MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX,
    db_name=None,
):
    s3_path = os.path.join(
        prefix,
        job_id,
        table_name,
        "{}-{}-{}-{}".format(table_name, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"), account_id or 0),
    )
    with db.get_write_stats_cursor(db_name) as c:
        logger.info("Unloading table to S3 path", table=table_name, s3_path=s3_path)
        sql, params = prepare_unload_csv_query(s3_path, table_name, date_from, date_to, account_id)
        c.execute(sql, params)
        logger.info("Unloaded table to S3 path", table=table_name, s3_path=s3_path)
    return s3_path + "manifest"


def refresh_materialized_rds_table(s3_path, table_name, bucket_name):
    for db_name in [settings.STATS_DB_HOT_CLUSTER] + settings.STATS_DB_COLD_CLUSTERS:
        with db.get_write_stats_transaction(db_alias=db_name):
            with db.get_write_stats_cursor(db_alias=db_name) as c:
                delete_from_table(table_name, db_alias=db_name)
                logger.info("Unloading table to S3 path", table=table_name, s3_path=s3_path)
                sql, params = prepare_copy_query(
                    s3_path, table_name, null_as="$NA$", bucket_name=bucket_name, truncate_columns=True
                )
                c.execute(sql, params)
                logger.info("Unloaded table to S3 path", table=table_name, s3_path=s3_path)


def unload_table_tz(
    job_id, table_name, date_from, date_to, account_id=None, prefix=MATERIALIZED_VIEWS_REPLICATION_S3_PREFIX
):
    s3_path = os.path.join(
        prefix,
        job_id,
        table_name,
        "{}-{}-{}-{}".format(table_name, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"), account_id or 0),
    )
    with db.get_write_stats_cursor() as c:
        logger.info("Unloading table to S3 path", table=table_name, s3_path=s3_path)
        sql, params = prepare_unload_tz_query(s3_path, table_name, date_from, date_to, account_id)
        c.execute(sql, params)
        logger.info("Unloaded table to S3 path", table=table_name, s3_path=s3_path)
    return s3_path + "manifest"


def update_table_from_s3(db_name, s3_manifest_path, table_name, date_from, date_to, account_id=None):
    with db.get_write_stats_transaction(db_name):
        with db.get_write_stats_cursor(db_name) as c:
            logger.info(
                "Loading table into replica from S3 path", table=table_name, db_name=db_name, s3_path=s3_manifest_path
            )
            sql, params = prepare_date_range_delete_query(table_name, date_from, date_to, account_id)
            c.execute(sql, params)

            sql, params = prepare_copy_query(
                s3_manifest_path,
                table_name,
                format=None,
                removequotes=False,
                escape=True,
                is_manifest=True,
                null_as="$NA$",
                gzip=True,
            )
            c.execute(sql, params)

            logger.info(
                "Loaded table into replica from S3 path", table=table_name, db_name=db_name, s3_path=s3_manifest_path
            )


def update_table_from_s3_postgres(
    db_name, s3_manifest_path, table_name, date_from, date_to, account_id=None, bucket_name=None
):
    with db.get_write_stats_transaction(db_name):
        with db.get_write_stats_cursor(db_name) as c:
            logger.info("Loading table into Postgres replica", table=table_name, db=db_name, s3_path=s3_manifest_path)

            sql, params = prepare_date_range_delete_query(table_name, date_from, date_to, account_id)
            c.execute(sql, params)

            bucket = s3helpers.S3Helper(bucket_name=bucket_name or settings.S3_BUCKET_STATS)
            keys = bucket.list_manifest(s3_manifest_path)
            for f in bucket.open_keys_async(keys):
                with gzip.GzipFile(fileobj=f, mode="rb") as gunzipped:
                    c.copy_expert("COPY %s FROM STDIN NULL '$NA$'" % table_name, gunzipped)

            logger.info("Loaded table into Postgres replica", table=table_name, db=db_name, s3_path=s3_manifest_path)


def prepare_unload_csv_query(s3_path, table_name, date_from, date_to, account_id=None, bucket_name=None):
    sql = backtosql.generate_sql(
        "etl_unload_csv.sql",
        {
            "table": table_name,
            "date_from_str": date_from.strftime("%Y-%m-%d"),
            "date_to_str": date_to.strftime("%Y-%m-%d"),
            "account_id_str": str(account_id) if account_id else None,
        },
    )

    s3_url = S3_FILE_URI.format(bucket_name=bucket_name or settings.S3_BUCKET_STATS, key=s3_path)
    credentials = _get_aws_credentials()

    return sql, {"s3_url": s3_url, "credentials": credentials, "delimiter": constants.CSV_DELIMITER}


def prepare_unload_tz_query(s3_path, table_name, date_from, date_to, account_id=None):
    params = helpers.get_local_multiday_date_context(date_from, date_to)
    params["table"] = table_name
    params["account_id_str"] = str(account_id) if account_id else None
    if account_id:
        ad_group_ids = helpers.get_ad_group_ids_or_none(account_id) or []
        params["ad_group_id"] = map(str, ad_group_ids)
    sql = backtosql.generate_sql("etl_unload_tz.sql", params)
    s3_url = S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_path)
    credentials = _get_aws_credentials()
    return sql, {"s3_url": s3_url, "credentials": credentials, "delimiter": constants.CSV_DELIMITER}


def prepare_copy_query(
    s3_path,
    table_name,
    format="csv",
    removequotes=False,
    escape=False,
    is_manifest=False,
    null_as=None,
    gzip=False,
    bucket_name=None,
    truncate_columns=False,
    delimiter=constants.CSV_DELIMITER,
    maxerror=0,
):
    sql = backtosql.generate_sql(
        "etl_copy.sql",
        {
            "table": table_name,
            "is_manifest": is_manifest,
            "format": format,
            "removequotes": removequotes,
            "escape": escape,
            "null_as": null_as,
            "gzip": gzip,
            "truncate_columns": truncate_columns,
            "maxerror": maxerror,
        },
    )

    s3_url = S3_FILE_URI.format(bucket_name=bucket_name or settings.S3_BUCKET_STATS, key=s3_path)
    credentials = _get_aws_credentials()

    return sql, {"s3_url": s3_url, "credentials": credentials, "delimiter": delimiter}


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


def delete_from_table(table_name, db_alias=None):
    sql = backtosql.generate_sql("etl_delete_table_mv_rds.sql", {"table": table_name})
    with db.get_write_stats_cursor(db_alias=db_alias) as c:
        logger.info("Will truncate table", table=table_name)
        c.execute(sql)
        logger.info("Table truncated", table=table_name)


def get_last_stl_load_error():
    sql = backtosql.generate_sql("etl_last_st_error_message.sql", {"table": "st_load_errors"})
    with db.get_write_stats_cursor() as c:
        c.execute(sql)
        msg = db.dictfetchall(c)[0]
        return {k: str(v).strip() for k, v in msg.items()}
