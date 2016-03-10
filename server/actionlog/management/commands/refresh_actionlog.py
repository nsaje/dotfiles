import logging

from django.core.management.base import BaseCommand

from actionlog import api
from actionlog import refresh_orders
from utils import statsd_helper
import influx
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        logger.info('Refreshing actionlog entries.')

        api.cancel_expired_actionlogs()

        try:
            api.send_delayed_actionlogs()
        except Exception, e:
            logger.exception("Failed to execute periodical sent to zwei of delayed actionlogs.")

        refresh_orders.refresh_fetch_all_orders()

        # monitor the state of manual actions
        n_cmd_waiting = api.count_waiting_stats_actions()
        statsd_helper.statsd_gauge('actionlog.n_cmd_waiting', n_cmd_waiting)
        influx.gauge('actionlog.n_cmd', n_cmd_waiting, status='waiting')

        n_cmd_failed = api.count_failed_stats_actions()
        statsd_helper.statsd_gauge('actionlog.n_cmd_failed', n_cmd_failed)
        influx.gauge('actionlog.n_cmd', n_cmd_failed, status='failed')

        n_cmd_delayed = api.count_delayed_stats_actions()
        statsd_helper.statsd_gauge('actionlog.n_cmd_delayed', n_cmd_delayed)
        influx.gauge('actionlog.n_cmd', n_cmd_delayed, status='delayed')

        hours_oldest_manual_cmd_waiting = api.age_oldest_waiting_action(manual_action=True)
        statsd_helper.statsd_gauge('actionlog.hours_oldest_cmd_waiting', hours_oldest_manual_cmd_waiting)
        influx.gauge('actionlog.hours_oldest_cmd', hours_oldest_manual_cmd_waiting, status='waiting')

        # Consumes a lot of resources when there are many waiting automatic actions (during sync)
        # hours_oldest_auto_cmd_waiting = api.age_oldest_waiting_action(manual_action=False)
        # statsd_helper.statsd_gauge('actionlog.hours_oldest_auto_cmd_waiting', hours_oldest_auto_cmd_waiting)
