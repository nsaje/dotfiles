from datetime import datetime

from actionlog import sync
import influx

def refresh_fetch_all_orders():
    last_success_times = sync.GlobalSync().get_latest_success_by_child().values()
    last_success_times_not_none = filter(lambda x: x is not None, last_success_times)

    last_sync = None
    if len(last_success_times_not_none):
        last_sync = min(last_success_times_not_none)

    _hours_since_statsd_ping(last_sync)
    num_ags_not_synced = len(filter(lambda x: x is None, last_success_times))
    influx.gauge('actionlog.num_ags', num_ags_not_synced, status='not_synced')


def _hours_since_statsd_ping(last_success_dt):
    if last_success_dt is not None:
        hours_since = (datetime.utcnow() - last_success_dt).total_seconds() // 3600
        influx.gauge('actionlog.hours_since', hours_since, status='last_synced')
