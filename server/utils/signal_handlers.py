import logging
import traceback

from django.core import urlresolvers
from utils.request_provider import get_request

from zemauth.models import User

from actionlog import constants
from utils import pagerduty_helper

logger = logging.getLogger(__name__)


def modified_by_pre_save_signal_handler(sender, instance, **kwargs):
    try:
        request = get_request()
        if not isinstance(request.user, User):
            return
        instance.modified_by = request.user
    except Exception:
        logger.info(
            'modified_by_pre_save_signal_handler: exception while getting request: %s sender: %s',
            traceback.format_exc,
            sender)


def created_by_pre_save_signal_handler(sender, instance, **kwargs):
    if instance.pk is not None:
        return

    try:
        request = get_request()
        if not isinstance(request.user, User):
            return
        instance.created_by = request.user
    except Exception:
        logger.info(
            'created_by_pre_save_signal_handler: exception while getting request: %s sender: %s',
            traceback.format_exc,
            sender)


def trigger_alert_pre_save_signal_handler(sender, instance, **kwargs):
    if (instance.state == constants.ActionState.FAILED and
           instance.action_type == constants.ActionType.AUTOMATIC and
           instance.action == constants.Action.SET_CAMPAIGN_STATE):
        trigger_stop_campaign_alert(instance.id)


def trigger_stop_campaign_alert(action_log_id):
    # Base URL is hardcoded for a lack of better alternatives
    admin_url = 'https://one.zemanta.com{0}'.format(
        urlresolvers.reverse('admin:actionlog_actionlog_change', args=(action_log_id,)))

    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
        incident_key='adgroup_stop_failed',
        description='Adgroup stop action failed',
        details={
            'action_log_admin_url': admin_url,
        }
    )
