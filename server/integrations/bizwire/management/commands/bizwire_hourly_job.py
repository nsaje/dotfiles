import logging

from integrations.bizwire.internal import actions
from utils.command_helpers import ExceptionCommand
from utils import pagerduty_helper

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        try:
            # actions.check_pacific_noon_and_stop_ads()
            actions.check_time_and_create_new_ad_groups()
            # actions.check_date_and_stop_old_ad_groups()
            actions.check_local_midnight_and_recalculate_daily_budgets()
            actions.reprocess_missing_articles()
        except:
            logger.exception('Exception raised in bizwire hourly job')
            pagerduty_helper.trigger(
                event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
                incident_key='bizwire_hourly_job_exception',
                description='Exception in bizwire hourly job',
            )
