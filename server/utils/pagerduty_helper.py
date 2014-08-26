import json
import urllib2

from django.conf import settings
from django.core import urlresolvers


def trigger_event(action_log_id):
    if not settings.PAGER_DUTY_ENABLED:
        return

    # Base URL is hardcoded for a lack of better alternatives
    admin_url = 'https://one.zemanta.com{0}'.format(
        urlresolvers.reverse('admin:actionlog_actionlog_change', args=(action_log_id,)))

    data = {
        'service_key': settings.PAGER_DUTY_SERVICE_KEY,
        'incident_key': 'adgroup_stop_failed',
        'event_type': 'trigger',
        'description': 'Adgroup stop action failed',
        'client': 'Zemanta One - {0}'.format(settings.HOSTNAME),
        'details': {
            'action_log_admin_url': admin_url,
        }
    }

    urllib2.urlopen(settings.PAGER_DUTY_URL, json.dumps(data))


def trigger(incident_key, description, details=None):
    if not settings.PAGER_DUTY_ENABLED:
        return

    data = {
        'service_key': settings.PAGER_DUTY_SERVICE_KEY,
        'incident_key': incident_key,
        'event_type': 'trigger',
        'description': description,
        'client': 'Zemanta One - {0}'.format(settings.HOSTNAME),
        'details': details
    }

    urllib2.urlopen(settings.PAGER_DUTY_URL, json.dumps(data))
