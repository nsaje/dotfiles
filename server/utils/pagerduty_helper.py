import json
import urllib2

from django.conf import settings


def trigger_event(ad_group_id, network_id):
    if not settings.PAGER_DUTY_ENABLED:
        return

    data = {
        'service_key': '0261faf28efa4fc8884ae0cffa768013',
        'incident_key': 'adgroup_stop_failed',
        'event_type': 'trigger',
        'description': 'Adgroup stop action failed',
        'client': 'Zemanta One',
        'details': {
            'ad_group_id': ad_group_id,
            'network_id': network_id
        }
    }

    urllib2.urlopen(settings.PAGER_DUTY_URL, json.dumps(data))
