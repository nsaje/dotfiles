import logging
import traceback

from django.core import urlresolvers
from gadjo.requestprovider.signals import get_request

from zemauth.models import User

from actionlog import constants
from actionlog.models import ActionLog
from utils import pagerduty_helper

logger = logging.getLogger(__name__)

LOG_ACTION_TYPES = [
    constants.Action.SET_CAMPAIGN_STATE,
    constants.Action.SET_PROPERTY,
    constants.Action.CREATE_CAMPAIGN
]


def _should_log(instance):
    # only logs if instance is an action with mandatory created_by and modified_by
    return isinstance(instance, ActionLog) and instance.action in LOG_ACTION_TYPES


def _log_user_instance(func_name, instance, request):
    if not _should_log(instance):
        return

    logger.warn(
        '{}: request.user is not an instance of User. Instance: {}, request.user: {}, request: {}'.format(
            func_name, repr(instance), repr(request.user), request)
    )


def _log_index_error(func_name, instance):
    if not _should_log(instance):
        return

    logger.warn(
        '{}: IndexError occured. Instance: {}, {}'.format(
            func_name, repr(instance), traceback.format_exc())
    )


def modified_by_pre_save_signal_handler(sender, instance, **kwargs):
    try:
        raise IndexError
        request = get_request()
        if not isinstance(request.user, User):
            _log_user_instance('modified_by_pre_save_signal_handler', instance, request)
            return
        instance.modified_by = request.user
    except IndexError:
        _log_index_error('modified_by_pre_save_signal_handler', instance)


def created_by_pre_save_signal_handler(sender, instance, **kwargs):
    if instance.pk is not None:
        return

    try:
        request = get_request()
        if not isinstance(request.user, User):
            _log_user_instance('created_by_pre_save_signal_handler', instance, request)
            return
        instance.created_by = request.user
    except IndexError:
        _log_index_error('created_by_pre_save_signal_handler', instance)


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
