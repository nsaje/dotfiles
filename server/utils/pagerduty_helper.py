import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from utils.constant_base import ConstantBase


class PagerDutyEventType(ConstantBase):
    SYSOPS = "sysops"  # DEPRECATED (12/27/16)
    ADOPS = "adops"  # DEPRECATED (12/27/16)
    ENGINEERS = "engineers"

    _VALUES = {SYSOPS: "SysOps", ADOPS: "AdOps", ENGINEERS: "Engineers"}


def trigger(event_type, incident_key, description, details=None):
    if not settings.PAGER_DUTY_ENABLED:
        return
    if event_type == PagerDutyEventType.SYSOPS:
        service_key = settings.PAGER_DUTY_SYSOPS_SERVICE_KEY
    elif event_type == PagerDutyEventType.ADOPS:
        service_key = settings.PAGER_DUTY_ADOPS_SERVICE_KEY
    elif event_type == PagerDutyEventType.ENGINEERS:
        service_key = settings.PAGER_DUTY_ENGINEERS_SERVICE_KEY
    else:
        raise AttributeError("Invalid event type")

    data = {
        "service_key": service_key,
        "incident_key": incident_key,
        "event_type": "trigger",
        "description": description,
        "client": "Zemanta One - {0}".format(settings.HOSTNAME),
        "details": details,
    }
    urllib.request.urlopen(settings.PAGER_DUTY_URL, json.dumps(data))
