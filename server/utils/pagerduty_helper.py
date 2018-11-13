import logging

import requests
from django.conf import settings

from utils.constant_base import ConstantBase

logger = logging.getLogger(__name__)


class PagerDutyEventType(ConstantBase):
    SYSOPS = "sysops"  # DEPRECATED (12/27/16)
    ADOPS = "adops"  # DEPRECATED (12/27/16)
    ENGINEERS = "engineers"
    Z1 = "Z1"

    _VALUES = {SYSOPS: "SysOps", ADOPS: "AdOps", ENGINEERS: "Engineers"}


def trigger(event_type, incident_key, description, details=None, **kwargs):
    _post_event("trigger", event_type, incident_key, description, details=details, **kwargs)


def resolve(event_type, incident_key, description, details=None, **kwargs):
    _post_event("resolve", event_type, incident_key, description, details=details, **kwargs)


def _post_event(command, event_type, incident_key, description, details=None, **kwargs):
    timeout = kwargs.get("timeout", 60)

    if not settings.PAGER_DUTY_ENABLED:
        return
    if event_type == PagerDutyEventType.SYSOPS:
        service_key = settings.PAGER_DUTY_SYSOPS_SERVICE_KEY
    elif event_type == PagerDutyEventType.ADOPS:
        service_key = settings.PAGER_DUTY_ADOPS_SERVICE_KEY
    elif event_type == PagerDutyEventType.ENGINEERS:
        service_key = settings.PAGER_DUTY_ENGINEERS_SERVICE_KEY
    elif event_type == PagerDutyEventType.Z1:
        service_key = settings.PAGER_DUTY_Z1_SERVICE_KEY
    else:
        raise AttributeError("Invalid event type")

    data = {
        "service_key": service_key,
        "incident_key": incident_key,
        "event_type": command,
        "description": description,
        "client": "Zemanta One - {0}".format(settings.HOSTNAME),
        "details": details,
    }

    try:
        response = requests.post(settings.PAGER_DUTY_URL, json=data, timeout=timeout)

        if not response.ok:
            logger.error("PagerDuty %s event failed due to status code: %s", command, response.status_code)

        else:
            logger.info("PagerDuty %s event succeeded", command)

    except requests.exceptions.Timeout:
        logger.error("PagerDuty %s event failed due to timeout", command)
