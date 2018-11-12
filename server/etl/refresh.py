import datetime
import logging
import random
import string
from functools import partial

import influx
from django.conf import settings
from django.core.cache import caches

import dash.models
import utils.slack
from etl import daily_statements
from etl import maintenance
from etl import materialization_run
from etl import materialize
from etl import redshift
from etl import spark
from utils import threads

logger = logging.getLogger(__name__)


SLACK_MIN_DAYS_TO_PROCESS = 7


def _post_to_slack(status, update_since, account_id=None):
    utils.slack.publish(
        "Materialization since {}{} *{}*.".format(
            str(update_since.date()), account_id and " for *account {}*".format(account_id) or "", status
        ),
        msg_type=utils.slack.MESSAGE_TYPE_INFO,
        username="Refresh k1",
    )


@influx.timer("etl.refresh_k1.refresh_k1_timer", type="all")
def refresh(
    update_since,
    account_id=None,
    skip_vacuum=False,
    skip_analyze=False,
    skip_daily_statements=False,
    dump_and_abort=None,
):
    do_post_to_slack = (datetime.datetime.today() - update_since).days > SLACK_MIN_DAYS_TO_PROCESS
    if do_post_to_slack or account_id:
        _post_to_slack("started", update_since, account_id)
    with spark.get_session() as spark_session:
        _refresh(
            update_since,
            materialize.MATERIALIZED_VIEWS,
            spark_session,
            account_id,
            skip_vacuum=skip_vacuum,
            skip_analyze=skip_analyze,
            skip_daily_statements=skip_daily_statements,
            dump_and_abort=dump_and_abort,
        )
    if do_post_to_slack or account_id:
        _post_to_slack("finished", update_since, account_id)
    materialization_run.create_done()


def _refresh(
    update_since,
    views,
    spark_session,
    account_id=None,
    skip_vacuum=False,
    skip_analyze=False,
    skip_daily_statements=False,
    dump_and_abort=None,
):
    influx.incr("etl.refresh_k1.refresh_k1_reports", 1)

    if account_id:
        validate_can_reprocess_account(account_id)

    total_spend = {}
    if not skip_daily_statements:
        total_spend = daily_statements.reprocess_daily_statements(update_since.date(), account_id)
    effective_spend_factors = daily_statements.get_effective_spend(total_spend, update_since.date(), account_id)

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]
    job_id = generate_job_id(account_id)

    logger.info(
        "Starting refresh job %s for date range %s - %s, requested update since %s, %s",
        job_id,
        date_from,
        date_to,
        update_since,
        "skip vacuum" if skip_vacuum else "vacuum each table",
    )

    extra_dayspan = (update_since.date() - date_from).days
    influx.gauge("etl.refresh_k1.extra_dayspan", extra_dayspan)
    if extra_dayspan:
        logger.warning(
            "Refresh is processing older statements than requested (requested update since %s,"
            "real update since %s), job %s",
            update_since,
            date_from,
            job_id,
        )

    replication_threads = []

    for mv_class in views:
        _materialize_view(
            mv_class,
            job_id,
            date_from,
            date_to,
            dump_and_abort,
            effective_spend_factors,
            skip_vacuum,
            skip_analyze,
            account_id,
            spark_session,
        )

        repl_func = partial(
            mv_unload_and_copy_into_replicas,
            mv_class,
            job_id,
            date_from,
            date_to,
            account_id,
            skip_vacuum,
            skip_analyze,
        )
        repl_thread = threads.AsyncFunction(repl_func)
        repl_thread.start()
        replication_threads.append(repl_thread)

    for thread in replication_threads:
        thread.join_and_get_result()

    # while everything is being updated data is not consistent among tables
    # so might as well leave cache until refresh finishes
    invalidate_breakdowns_rs_cache()

    influx.incr("etl.refresh_k1.refresh_k1_reports_finished", 1)


def _materialize_view(
    mv_class,
    job_id,
    date_from,
    date_to,
    dump_and_abort,
    effective_spend_factors,
    skip_vacuum,
    skip_analyze,
    account_id,
    spark_session,
):
    mv = mv_class(job_id, date_from, date_to, account_id=account_id, spark_session=spark_session)
    with influx.block_timer("etl.refresh_k1.generate_table", table=mv_class.TABLE_NAME):
        mv.generate(campaign_factors=effective_spend_factors)

        if mv_class.TABLE_NAME == dump_and_abort:
            logger.info("Dumping %s", dump_and_abort)
            s3_path = redshift.unload_table(
                job_id, mv_class.TABLE_NAME, date_from, date_to, prefix=redshift.DUMP_S3_PREFIX
            )
            logger.info("Dumped %s to %s", dump_and_abort, s3_path)
            logger.info("Aborting after %s", dump_and_abort)
            exit()

        try:
            if not skip_vacuum and not mv_class.IS_TEMPORARY_TABLE:
                maintenance.vacuum(mv_class.TABLE_NAME)
            if not skip_analyze:
                maintenance.analyze(mv_class.TABLE_NAME)
        except Exception:
            logger.exception("Vacuum and analyze skipped due to error")


def unload_and_copy_into_replicas(
    views, job_id, date_from, date_to, account_id=None, skip_vacuum=False, skip_analyze=False
):
    for mv_class in views:
        mv_unload_and_copy_into_replicas(mv_class, job_id, date_from, date_to, account_id, skip_vacuum, skip_analyze)


def mv_unload_and_copy_into_replicas(
    mv_class, job_id, date_from, date_to, account_id=None, skip_vacuum=False, skip_analyze=False
):
    if mv_class.IS_TEMPORARY_TABLE:
        return
    s3_path = redshift.unload_table(job_id, mv_class.TABLE_NAME, date_from, date_to, account_id=account_id)
    update_threads = []
    for db_name in settings.STATS_DB_WRITE_REPLICAS:
        async_func = partial(
            update_table,
            db_name,
            s3_path,
            mv_class.TABLE_NAME,
            date_from,
            date_to,
            account_id,
            skip_vacuum,
            skip_analyze,
        )
        async_thread = threads.AsyncFunction(async_func)
        async_thread.start()
        update_threads.append(async_thread)
    if mv_class not in (materialize.MasterView, materialize.MasterPublishersView):
        # do not copy mv_master and mv_master_pubs into postgres, too large
        for db_name in settings.STATS_DB_WRITE_REPLICAS_POSTGRES:
            async_func = partial(
                update_table,
                db_name,
                s3_path,
                mv_class.TABLE_NAME,
                date_from,
                date_to,
                account_id,
                skip_vacuum,
                skip_analyze,
            )
            async_thread = threads.AsyncFunction(async_func)
            async_thread.start()
            update_threads.append(async_thread)

    for thread in update_threads:
        thread.join_and_get_result()


def update_table(db_name, s3_path, table_name, date_from, date_to, account_id, skip_vacuum, skip_analyze):
    redshift.update_table_from_s3(db_name, s3_path, table_name, date_from, date_to, account_id=account_id)
    if not skip_vacuum:
        maintenance.vacuum(table_name, db_name=db_name)
    if not skip_analyze:
        maintenance.analyze(table_name, db_name=db_name)


def get_all_views_table_names(temporary=False):
    return [x.TABLE_NAME for x in materialize.MATERIALIZED_VIEWS if x.IS_TEMPORARY_TABLE is temporary]


def refresh_derived_views(refresh_days=3):
    """
    Refreshes derived views:
    - creates new tables for derived views that were newly added to materialized views list,
    - updates all of the derived views with data from master tables for the specified number of days.
    """

    for mv_class in materialize.MATERIALIZED_VIEWS:
        if not mv_class.IS_DERIVED_VIEW:
            continue

        mv = mv_class(
            "temp",
            datetime.date.today() - datetime.timedelta(days=refresh_days),
            datetime.date.today(),
            account_id=None,
        )
        mv.generate()


def generate_job_id(account_id):
    epoch = datetime.datetime.utcfromtimestamp(0)
    timestamp = int((datetime.datetime.now() - epoch).total_seconds() * 1000)

    rnd_str = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

    if account_id:
        return "{}_A{}_{}".format(timestamp, account_id, rnd_str)

    return "{}_{}".format(timestamp, rnd_str)


def invalidate_breakdowns_rs_cache():
    cache = caches["breakdowns_rs"]
    cache.clear()


def validate_can_reprocess_account(account_id):
    # check account exists
    dash.models.Account.objects.get(pk=account_id)

    if not dash.models.AdGroup.objects.filter(campaign__account_id=account_id).exists():
        raise Exception("No ad groups exist for the selected account (pk={})".format(account_id))
