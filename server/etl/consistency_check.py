import logging

from django.conf import settings

from etl import materialize
from redshiftapi import db
from utils import pagerduty_helper

logger = logging.getLogger(__name__)


def consistency_check(date_from, date_to):
    logger.info("Consistency check started")

    mv_master = materialize.mv_master.MasterView
    derived_views = [
        view
        for view in materialize.MATERIALIZED_VIEWS
        if not view.IS_TEMPORARY_TABLE and view.SOURCE_VIEW == mv_master.TABLE_NAME
    ]

    master_counts = get_counts(mv_master, date_from, date_to, db_name=settings.STATS_DB_NAME)

    for view in derived_views:
        for db_name in (
            [settings.STATS_DB_NAME] + settings.STATS_DB_WRITE_REPLICAS + settings.STATS_DB_WRITE_REPLICAS_POSTGRES
        ):
            check_counts(master_counts, view, date_from, date_to, db_name)

    logger.info("Consistency check finished")


def check_counts(master_counts, view, date_from, date_to, db_name=None):
    counts = get_counts(view, date_from, date_to, db_name)
    if counts != master_counts:
        description = f"table {view.TABLE_NAME} in db {db_name} is not consistent with mv_master"
        logger.warning(description)
        pagerduty_helper.trigger(
            pagerduty_helper.PagerDutyEventType.Z1,
            "consistency_check",
            description,
            event_severity=pagerduty_helper.PagerDutyEventSeverity.WARNING,
        )


def get_counts(view, date_from, date_to, db_name=None):
    with db.get_stats_cursor(db_name) as c:
        c.execute(
            f"SELECT SUM(clicks), SUM(pageviews) FROM {view.TABLE_NAME} WHERE date >= '{date_from}' AND date < '{date_to}'"
        )
        rows = c.fetchone()
        return rows