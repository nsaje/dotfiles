from datetime import datetime

from actionlog import api
from utils import statsd_helper


def refresh_fetch_all_orders():
    last_successful_order = api.get_last_successful_fetch_all_order()
    _hours_since_statsd_ping(last_successful_order)


def _hours_since_statsd_ping(last_successful_order):
    if last_successful_order is not None:
        hours_since = (datetime.utcnow() - last_successful_order.created_dt).seconds // 3600
        statsd_helper.statsd_gauge('hours_since_last_successful_fetch_all', hours_since)
