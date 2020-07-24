import datetime

from django.conf import settings

from etl import materialize
from redshiftapi import db
from utils import pagerduty_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)


def consistency_check(date_from, date_to):
    logger.info("Consistency check started")

    mv_master = materialize.mv_master.MasterView
    derived_views = [
        view
        for view in materialize.MATERIALIZED_VIEWS
        if not view.IS_TEMPORARY_TABLE and view.SOURCE_VIEW == mv_master.TABLE_NAME
    ]

    master_counts = get_counts(mv_master, date_from, date_to, db_name=settings.STATS_DB_HOT_CLUSTER)

    for view in derived_views:
        if date_from.date() <= datetime.date(2020, 7, 7) and view.TABLE_NAME.endswith("_pubs"):
            continue  # HACK(nsaje): dont check pubs tables before that date since they werent consistent with mv_master before mv_master_pubs removal
        for db_name in [settings.STATS_DB_HOT_CLUSTER] + settings.STATS_DB_COLD_CLUSTERS + settings.STATS_DB_POSTGRES:
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
