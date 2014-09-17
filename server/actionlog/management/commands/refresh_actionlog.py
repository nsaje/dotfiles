import logging

from django.core.management.base import BaseCommand

from actionlog import api
from actionlog import refresh_orders
from utils import statsd_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Refreshing actionlog entries.')

        api.cancel_expired_actionlogs()
        refresh_orders.refresh_fetch_all_orders()

        # monitor the state of manual actions
        n_cmd_waiting = api.count_waiting_stats_actions()
        statsd_helper.statsd_gauge('n_cmd_waiting', n_cmd_waiting)
        n_cmd_failed = api.count_failed_stats_actions()
        statsd_helper.statsd_gauge('n_cmd_failed', n_cmd_failed)
        hours_oldest_cmd_waiting = api.age_oldest_waiting_stats_action()
        statsd_helper.statsd_gauge('hours_oldest_cmd_waiting', hours_oldest_cmd_waiting)
