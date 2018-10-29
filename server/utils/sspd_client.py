import datetime
import json
import logging
import copy

import jwt
import requests

from django.conf import settings

from dash import constants
from dash import models
from utils import dates_helper

logger = logging.getLogger(__name__)

APPROVAL_STATUS_URL = "/service/approvalstatus"
CONTENT_AD_STATUS_URL = "/service/contentadstatus"

MAX_REQUEST_IDS = 500
TIMEOUT = (10, 10)  # TIMEOUT IN SECONDS (CONNECT TIME, READ TIME)


class SSPDApiException(Exception):
    pass


def get_approval_status(
    ad_group_ids=None, content_ad_ids=None, source_types=None, slugs=None, content_ad_source_ids=None
):
    url = settings.SSPD_BASE_URL + APPROVAL_STATUS_URL
    approval_status_dict = {
        "adGroupIds": ad_group_ids,
        "contentAdIds": content_ad_ids,
        "sourceTypes": source_types,
        "slugs": slugs,
        "contentAdSourceIds": content_ad_source_ids,
    }
    approval_statuses = _make_request("post", url, data=json.dumps(approval_status_dict))
    return _map_approval_statuses(approval_statuses)


def _map_approval_statuses(approval_statuses):
    return {int(id_): getattr(constants.ContentAdSspdStatus, status) for id_, status in approval_statuses.items()}


def get_content_ad_status(content_ad_ids):
    url = settings.SSPD_BASE_URL + CONTENT_AD_STATUS_URL
    if not content_ad_ids:
        raise SSPDApiException("Request not allowed")
    content_ad_statuses = _paginate_request(
        "get", url, params={"contentAdIds": content_ad_ids}, paginate_key="contentAdIds", timeout=TIMEOUT
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


def _paginate_request(method, url, params, *, paginate_key, timeout=None):
    start = 0
    result = {}
    paginate_list = params.pop(paginate_key)
    while start < len(paginate_list):
        page_params = copy.copy(params)
        page_params[paginate_key] = ",".join(str(el) for el in paginate_list[start : start + MAX_REQUEST_IDS])
        result.update(_make_request(method, url, params=page_params, timeout=timeout))
        start += MAX_REQUEST_IDS
    return result


def _make_request(method, url, data=None, params=None, headers=None, timeout=None):
    if not headers:
        headers = {}
    _augment_with_auth_headers(headers)
    if method == "post":
        headers.update({"Content-type": "application/json"})
    try:
        response = requests.request(
            method, url, data=data if data else {}, params=params if params else {}, headers=headers, timeout=timeout
        )
    except requests.exceptions.RequestException as exception:
        logger.exception(exception)
        raise SSPDApiException(exception) from exception
    if not response.ok:
        raise SSPDApiException("Request failed")
    return response.json()


def _augment_with_auth_headers(headers):
    payload = {"iss": "Z1", "exp": dates_helper.utc_now() + datetime.timedelta(seconds=60)}
    token = jwt.encode(payload, settings.SSPD_AUTH_SECRET, algorithm="HS256")
    auth_header = "Bearer " + token.decode("utf-8")
    headers.update({"Authorization": auth_header})
