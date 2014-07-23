from datetime import datetime

from actionlog import sync
from utils import statsd_helper


def refresh_fetch_all_orders():
    last_success_dt = sync.GlobalSync().get_latest_success()
    _hours_since_statsd_ping(last_success_dt)


def _hours_since_statsd_ping(last_success_dt):
    if last_success_dt is not None:
        hours_since = (datetime.utcnow() - last_success_dt).total_seconds() // 3600
        statsd_helper.statsd_gauge('actionlog.hours_since_last_sync', hours_since)
