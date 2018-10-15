import datetime

import jwt
import requests

from django.conf import settings

from dash import constants
from utils import dates_helper

APPROVAL_STATUS_URL = "/service/status"


def get_approval_status(content_ad_source_ids):
    url = settings.SSPD_BASE_URL + APPROVAL_STATUS_URL
    approval_statuses = _make_request(
        "get", url, params={"contentAdSourceIds": ",".join(str(id_) for id_ in content_ad_source_ids)}
    )
    return _map_statuses(approval_statuses)


def _map_statuses(approval_statuses):
    return {int(id_): getattr(constants.ContentAdSspdStatus, status) for id_, status in approval_statuses.items()}


def _make_request(method, url, data=None, params=None, headers=None):
    if not headers:
        headers = {}
    _augment_with_auth_headers(headers)
    response = requests.request(
        method, url, data=data if data else {}, params=params if params else {}, headers=headers
    )
    if not response.ok:
        raise Exception("Failed sspd request")
    return response.json()


def _augment_with_auth_headers(headers):
    payload = {"iss": "Z1", "exp": dates_helper.utc_now() + datetime.timedelta(seconds=60)}
    token = jwt.encode(payload, settings.SSPD_AUTH_SECRET, algorithm="HS256")
    auth_header = "Bearer " + token.decode("utf-8")
    headers.update({"Authorization": auth_header})
