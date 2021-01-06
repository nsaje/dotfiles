import datetime
import random
import string
from functools import partial

import newrelic.agent
from django.conf import settings
from django.core.cache import caches

import dash.models
import utils.slack
from etl import daily_statements
from etl import maintenance
from etl import materialization_run
from etl import materialize
from etl import redshift
from utils import dates_helper
from utils import metrics_compat
from utils import threads
from utils import zlogging

logger = zlogging.getLogger(__name__)


SLACK_MIN_DAYS_TO_PROCESS = 7


def _post_to_slack(status, update_since, account_id=None):
    utils.slack.publish(
        "Materialization since {}{} *{}*.".format(
            str(update_since.date()), account_id and " for *account {}*".format(account_id) or "", status
        ),
        msg_type=utils.slack.MESSAGE_TYPE_INFO,
        username=utils.slack.USER_REFRESH_K1,
    )


@metrics_compat.timer("etl.refresh_k1.refresh_k1_timer", type="all")
def refresh(update_since, account_id=None, skip_daily_statements=False, dump_and_abort=None, update_to=None):
    do_post_to_slack = (datetime.datetime.today() - update_since).days > SLACK_MIN_DAYS_TO_PROCESS
    if do_post_to_slack or account_id:
        _post_to_slack("started", update_since, account_id)
    etl_books_closed, date_books_closed_date = _check_if_yesterdays_data_exists()
    _refresh(
        update_since,
        materialize.MATERIALIZED_VIEWS,
        account_id=account_id,
        skip_daily_statements=skip_daily_statements,
        dump_and_abort=dump_and_abort,
        update_to=update_to,
    )
    if do_post_to_slack or account_id:
        _post_to_slack("finished", update_since, account_id)
    materialization_run.write_etl_books_status(etl_books_closed, date_books_closed_date)
    materialization_run.create_done()


@newrelic.agent.function_trace()
def _refresh(update_since, views, account_id=None, skip_daily_statements=False, dump_and_abort=None, update_to=None):
    metrics_compat.incr("etl.refresh_k1.refresh_k1_reports", 1)
    validate_update_since_date(update_since)

    if account_id:
        validate_can_reprocess_account(account_id)

    total_spend = {}
    if not skip_daily_statements:
        total_spend = daily_statements.reprocess_daily_statements(update_since.date(), account_id)
    effective_spend_factors = daily_statements.get_effective_spend(total_spend, update_since.date(), account_id)

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], (update_to or dates[-1])
    job_id = generate_job_id(account_id)

    logger.info("Starting refresh job", job_id=job_id, date_from=date_from, date_to=date_to, update_since=update_since)

    extra_dayspan = (update_since.date() - date_from).days
    metrics_compat.gauge("etl.refresh_k1.extra_dayspan", extra_dayspan)
    if extra_dayspan:
        logger.warning(
            "Refresh is processing older statements than requested",
            update_since=update_since,
            date_from=date_from,
            job_id=job_id,
        )

    replication_threads = []

    for mv_class in views:
        _materialize_view(mv_class, job_id, date_from, date_to, dump_and_abort, effective_spend_factors, account_id)

        repl_func = partial(mv_unload_and_copy_into_replicas, mv_class, job_id, date_from, date_to, account_id)
        repl_thread = threads.AsyncFunction(repl_func)
        repl_thread.start()
        replication_threads.append(repl_thread)

    for thread in replication_threads:
        thread.join_and_get_result()

    # while everything is being updated data is not consistent among tables
    # so might as well leave cache until refresh finishes
    invalidate_breakdowns_rs_cache()

    metrics_compat.incr("etl.refresh_k1.refresh_k1_reports_finished", 1)


def _materialize_view(mv_class, job_id, date_from, date_to, dump_and_abort, effective_spend_factors, account_id):
    logger.info("Materializing view", job_id=job_id, table=mv_class.TABLE_NAME)
    mv = mv_class(job_id, date_from, date_to, account_id=account_id)
    with metrics_compat.block_timer("etl.refresh_k1.generate_table", table=mv_class.TABLE_NAME):
        mv.generate(campaign_factors=effective_spend_factors)

        if mv_class.TABLE_NAME == dump_and_abort:
            logger.info("Dumping table", table=dump_and_abort)
            s3_path = redshift.unload_table(
                job_id, mv_class.TABLE_NAME, date_from, date_to, prefix=redshift.DUMP_S3_PREFIX
            )
            logger.info("Dumped table", table=dump_and_abort, s3_path=s3_path)
            logger.info("Aborting after table", table=dump_and_abort)
            exit()
    logger.info("Finished materializing view", job_id=job_id, table=mv_class.TABLE_NAME)


def unload_and_copy_into_replicas(views, job_id, date_from, date_to, account_id=None):
    for mv_class in views:
        mv_unload_and_copy_into_replicas(mv_class, job_id, date_from, date_to, account_id)


def mv_unload_and_copy_into_replicas(mv_class, job_id, date_from, date_to, account_id=None):
    if mv_class.IS_TEMPORARY_TABLE:
        return
    s3_path = redshift.unload_table(job_id, mv_class.TABLE_NAME, date_from, date_to, account_id=account_id)
    update_threads = []
    # for db_name in settings.STATS_DB_COLD_CLUSTERS:
    #     async_func = partial(update_table, db_name, s3_path, mv_class.TABLE_NAME, date_from, date_to, account_id)
    #     async_thread = threads.AsyncFunction(async_func)
    #     async_thread.start()
    #     update_threads.append(async_thread)
    if mv_class not in (materialize.MasterView, materialize.MVAdGroupPlacement) and mv_class.TABLE_NAME not in (
        "mv_campaign_placement",
        "mv_account_placement",
    ):
        # do not copy into postgres, too large
        for db_name in settings.STATS_DB_POSTGRES:
            async_func = partial(
                update_table_postgres, db_name, s3_path, mv_class.TABLE_NAME, date_from, date_to, account_id
            )
            async_thread = threads.AsyncFunction(async_func)
            async_thread.start()
            update_threads.append(async_thread)

    for thread in update_threads:
        thread.join_and_get_result()


def update_table(db_name, s3_path, table_name, date_from, date_to, account_id):
    redshift.update_table_from_s3(db_name, s3_path, table_name, date_from, date_to, account_id=account_id)


def update_table_postgres(db_name, s3_path, table_name, date_from, date_to, account_id):
    redshift.update_table_from_s3_postgres(db_name, s3_path, table_name, date_from, date_to, account_id=account_id)


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


def validate_update_since_date(update_since):
    min_date = maintenance.stats_min_date()
    if update_since.date() < min_date:
        raise Exception("Missing raw data in stats table for selected date range")


def _check_if_yesterdays_data_exists():
    yesterday = dates_helper.local_yesterday()
    number_of_hours_with_data = maintenance.check_existing_data_by_hours(yesterday)
    return number_of_hours_with_data == 24, yesterday
