from django.db.models.signals import pre_save
from django.core import urlresolvers
from utils import pagerduty_helper, url_helper

from actionlog import constants
from actionlog import models


def trigger_alert_pre_save_signal_handler(sender, instance, **kwargs):
    if (instance.state == constants.ActionState.FAILED and
           instance.action_type == constants.ActionType.AUTOMATIC and
           instance.action == constants.Action.SET_CAMPAIGN_STATE):

        event_type = pagerduty_helper.PagerDutyEventType.ADOPS
        if not instance.ad_group_source.source.has_3rd_party_dashboard():
            event_type = pagerduty_helper.PagerDutyEventType.ENGINEERS

        _trigger_stop_campaign_alert(instance.id, event_type)


def _trigger_stop_campaign_alert(action_log_id, event_type):
    admin_url = url_helper.get_full_z1_url(
        urlresolvers.reverse('admin:actionlog_actionlog_change',
                             args=(action_log_id,)))

    pagerduty_helper.trigger(
        event_type=event_type,
        incident_key='adgroup_stop_failed',
        description='Adgroup stop action failed',
        details={
            'action_log_admin_url': admin_url,
        }
    )

pre_save.connect(trigger_alert_pre_save_signal_handler, sender=models.ActionLog)
