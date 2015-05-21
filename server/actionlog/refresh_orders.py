from datetime import datetime

from actionlog import sync
from utils import statsd_helper

import dash.models


def refresh_fetch_all_orders():
    last_success_times = sync.GlobalSync(
        sources=dash.models.Source.objects.all()
    ).get_latest_success_by_child(recompute=False).values()

    last_sync = None
    if len(last_success_times) and None not in last_success_times:
        last_sync = min(last_success_times)

    _hours_since_statsd_ping(last_sync)


def _hours_since_statsd_ping(last_success_dt):
    if last_success_dt is not None:
        hours_since = (datetime.utcnow() - last_success_dt).total_seconds() // 3600
        statsd_helper.statsd_gauge('actionlog.hours_since_last_sync', hours_since)
