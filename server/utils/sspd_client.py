import datetime
import logging

import jwt
import requests

from django.conf import settings

from dash import constants
from dash import models
from utils import dates_helper

logger = logging.getLogger(__name__)

APPROVAL_STATUS_URL = "/service/approvalstatus"
CONTENT_AD_STATUS_URL = "/service/contentadstatus"


class SSPDApiException(Exception):
    pass


def get_approval_status(content_ad_source_ids):
    url = settings.SSPD_BASE_URL + APPROVAL_STATUS_URL
    logger.info("Requesting SSPD approval statuses for %s content ad sources", len(content_ad_source_ids))
    if not content_ad_source_ids:
        raise SSPDApiException("Request not allowed")
    approval_statuses = _make_request(
        "get", url, params={"contentAdSourceIds": ",".join(str(id_) for id_ in content_ad_source_ids)}
    )
    return _map_approval_statuses(approval_statuses)


def _map_approval_statuses(approval_statuses):
    return {int(id_): getattr(constants.ContentAdSspdStatus, status) for id_, status in approval_statuses.items()}


def get_content_ad_status(content_ad_ids):
    url = settings.SSPD_BASE_URL + CONTENT_AD_STATUS_URL
    logger.info("Requesting SSPD statuses for %s content ads", len(content_ad_ids))
    if not content_ad_ids:
        raise SSPDApiException("Request not allowed")
    content_ad_statuses = _make_request(
        "get", url, params={"contentAdIds": ",".join(str(id_) for id_ in content_ad_ids)}
    )
    return _map_content_ad_statuses(content_ad_statuses)


def _map_content_ad_statuses(content_ad_statuses):
    source_map = {source.id: source for source in models.Source.objects.all()}
    return {
        int(id_): {
            source_map[source_status["sourceId"]].id: {
                "reason": source_status["reason"],
                "status": getattr(constants.ContentAdSspdStatus, source_status["status"]),
            }
            for source_status in per_source_statuses
        }
        for id_, per_source_statuses in content_ad_statuses.items()
    }


def _make_request(method, url, data=None, params=None, headers=None):
    if not headers:
        headers = {}
    _augment_with_auth_headers(headers)
    response = requests.request(
        method, url, data=data if data else {}, params=params if params else {}, headers=headers
    )
    if not response.ok:
        raise SSPDApiException("Request failed")
    return response.json()


def _augment_with_auth_headers(headers):
    payload = {"iss": "Z1", "exp": dates_helper.utc_now() + datetime.timedelta(seconds=60)}
    token = jwt.encode(payload, settings.SSPD_AUTH_SECRET, algorithm="HS256")
    auth_header = "Bearer " + token.decode("utf-8")
    headers.update({"Authorization": auth_header})
