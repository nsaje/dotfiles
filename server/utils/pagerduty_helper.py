import datetime
import traceback
from dataclasses import dataclass
from functools import wraps

import requests
from django.conf import settings

from utils import dates_helper
from utils import zlogging
from utils.constant_base import ConstantBase

logger = zlogging.getLogger(__name__)


REST_API_URL = settings.PAGER_DUTY_REST_API_URL
REST_API_KEY = settings.PAGER_DUTY_REST_API_KEY
Z1_TEAM_ID = settings.PAGER_DUTY_Z1_TEAM_ID
Z1_TEAM_SCHEDULE_ID = settings.PAGER_DUTY_Z1_TEAM_SCHEDULE_ID


@dataclass
class PagerDutyIncident:
    title: str
    url: str
    assignee_id: str
    created_at: datetime.datetime


@dataclass(eq=True, frozen=True)
class PagerDutyUser:
    name: str
    email: str


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


def catch_and_report_exception(event_type, event_severity=None, summary="", links=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as ex:
                func_name = func.__qualname__
                incident_key = "exc:{}".format(func_name)
                description = " ".join(
                    [summary, "Exception in function {}\n{}".format(func_name, traceback.format_exc())]
                )
                trigger(event_type, incident_key, description, event_severity=event_severity, links=links)
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
    links = kwargs.get("links")
    if links:
        data["links"] = [{"href": url, "text": text} for url, text in links.items()]

    try:
        response = requests.post(settings.PAGER_DUTY_URL, json=data, timeout=timeout)

        if not response.ok:
            logger.error("PagerDuty event failed due to status code", command=command, status_code=response.status_code)

        else:
            logger.info("PagerDuty event succeeded", command=command)

    except requests.exceptions.Timeout:
        logger.error("PagerDuty event failed due to timeout", command=command)


def list_active_incidents():
    incidents = _call_api(
        "GET", REST_API_URL + "/incidents", {"statuses[]": ["triggered", "acknowledged"], "team_ids[]": [Z1_TEAM_ID]}
    )
    ret = []
    for incident in incidents["incidents"]:
        assignee_id = incident["assignments"][0]["assignee"]["id"] if incident["assignments"] else None
        created_at = datetime.datetime.strptime(incident["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        ret.append(
            PagerDutyIncident(
                title=incident["title"], url=incident["html_url"], assignee_id=assignee_id, created_at=created_at
            )
        )
    return ret


def get_on_call_user():
    today = dates_helper.utc_today()
    users = _call_api(
        "GET",
        REST_API_URL + f"/schedules/{Z1_TEAM_SCHEDULE_ID}/users",
        {"since": today.isoformat(), "until": (today + datetime.timedelta(days=1)).isoformat()},
    )
    if not users.get("users"):
        return None
    return PagerDutyUser(name=users["users"][0]["name"], email=users["users"][0]["email"])


def get_user(id):
    user = _call_api("GET", REST_API_URL + f"/users/{id}", {})
    return PagerDutyUser(name=user["user"]["name"], email=user["user"]["email"])


def _call_api(method, url, params):
    pagerduty_session = requests.Session()
    pagerduty_session.headers.update(
        {"Authorization": "Token token=" + REST_API_KEY, "Accept": "application/vnd.pagerduty+json;version=2"}
    )
    r = pagerduty_session.request(method, url, params)
    return r.json()
