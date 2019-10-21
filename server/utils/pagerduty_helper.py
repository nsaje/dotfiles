import traceback
from functools import wraps

import requests
import structlog
from django.conf import settings

from utils.constant_base import ConstantBase

logger = structlog.get_logger(__name__)


class PagerDutyEventType(ConstantBase):
    SYSOPS = "sysops"  # DEPRECATED (12/27/16)
    ADOPS = "adops"  # DEPRECATED (12/27/16)
    ENGINEERS = "engineers"
    Z1 = "Z1"
    PRODOPS = "prodops"

    _VALUES = {SYSOPS: "SysOps", ADOPS: "AdOps", ENGINEERS: "Engineers", PRODOPS: "ProdOps"}


class PagerDutyEventSeverity(ConstantBase):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    _VALUES = {CRITICAL: CRITICAL, ERROR: ERROR, WARNING: WARNING, INFO: INFO}


def trigger(event_type, incident_key, description, event_severity=None, details=None, **kwargs):
    _post_event(
        "trigger", event_type, incident_key, description, event_severity=event_severity, details=details, **kwargs
    )


def resolve(event_type, incident_key, description, event_severity=None, details=None, **kwargs):
    _post_event(
        "resolve", event_type, incident_key, description, event_severity=event_severity, details=details, **kwargs
    )


def catch_and_report_exception(event_type, event_severity=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as ex:
                func_name = func.__qualname__
                incident_key = "exc:{}".format(func_name)
                description = "Exception in function {}\n{}".format(func_name, traceback.format_exc())
                trigger(event_type, incident_key, description, event_severity=event_severity)
                raise ex

        return wrapper

    return decorator


def _post_event(command, event_type, incident_key, description, event_severity=None, details=None, **kwargs):
    event_severity = event_severity or PagerDutyEventSeverity.CRITICAL
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
    elif event_type == PagerDutyEventType.PRODOPS:
        service_key = settings.PAGER_DUTY_PRODOPS_SERVICE_KEY
    else:
        raise AttributeError("Invalid event type")

    data = {
        "routing_key": service_key,
        "event_action": command,
        "dedup_key": incident_key,
        "payload": {
            "summary": description,
            "source": "Zemanta One - {0}".format(settings.HOSTNAME),
            "severity": event_severity,
            "custom_details": details,
        },
    }

    try:
        response = requests.post(settings.PAGER_DUTY_URL, json=data, timeout=timeout)

        if not response.ok:
            logger.error("PagerDuty event failed due to status code", command=command, status_code=response.status_code)

        else:
            logger.info("PagerDuty event succeeded", command=command)

    except requests.exceptions.Timeout:
        logger.error("PagerDuty event failed due to timeout", command=command)
