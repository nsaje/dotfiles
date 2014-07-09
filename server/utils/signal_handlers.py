from zemauth.models import User

from gadjo.requestprovider.signals import get_request

from actionlog import constants
from utils import pagerduty_helper


def modified_by_pre_save_signal_handler(sender, instance, **kwargs):
    try:
        request = get_request()
        if not isinstance(request.user, User):
            return
        instance.modified_by = request.user
    except IndexError:
        pass


def created_by_pre_save_signal_handler(sender, instance, **kwargs):
    if instance.pk is not None:
        return

    try:
        request = get_request()
        if not isinstance(request.user, User):
            return
        instance.created_by = request.user
    except IndexError:
        pass


def trigger_alert_pre_save_signal_handler(sender, instance, **kwargs):
    if (instance.state == constants.ActionState.FAILED and
           instance.action_type == constants.ActionType.AUTOMATIC and
           instance.action == constants.Action.SET_CAMPAIGN_STATE and
           instance.order.order_type == constants.ActionLogOrderType.STOP_ALL):
        pagerduty_helper.trigger_event(
            instance.ad_group_network.ad_group.id,
            instance.ad_group.network.network.id
        )
