import base64
import json

import requests
from django.conf import settings

from utils import zlogging

logger = zlogging.getLogger(__name__)

NUM_RETRIES = 1
TIMEOUT = 2

URL_IDS_TO_INTERNAL = "/ids/{external_ids}/toInternal"
URL_LOGIN = "/login"

api_token = None


class OutbrainInternalAPIException(Exception):
    pass


class OutbrainInternalAPITimeoutException(OutbrainInternalAPIException):
    pass


def to_internal_ids(external_ids):
    if not external_ids:
        return []

    url = settings.AMELIA_BASE_URL + URL_IDS_TO_INTERNAL.format(external_ids=",".join(external_ids))
    return _call_api_retry(url, "GET")


def _call_api_retry(url, method="GET", **kwargs):
    last_error = None
    for _ in range(NUM_RETRIES):
        try:
            return _call_api(url, method, **kwargs)
        except Exception as error:
            last_error = error

    raise OutbrainInternalAPIException(last_error)


def _call_api(url, method="GET", **kwargs):
    if settings.K1_DEMO_MODE:
        return {}
    headers = kwargs.pop("headers", {})
    headers["OB-TOKEN-V1"] = _get_api_token()
    try:
        r = requests.request(method=method, url=url, headers=headers, **kwargs, timeout=TIMEOUT)
    except requests.exceptions.Timeout as e:
        logger.exception("Outbrain Internal API timing out!")
        raise OutbrainInternalAPITimeoutException(e)

    if r.status_code != 200:
        raise OutbrainInternalAPIException("Invalid response status code. response: {}".format(r.content))

    try:
        ret = r.json()
    except Exception:
        raise OutbrainInternalAPIException("JSON deserialization not successful: {}".format(r.content))

    return ret


def _get_api_token():
    global api_token

    if api_token:
        return api_token

    credentials = _base64_encode_credentials(settings.OUTBRAIN_INTERNAL_USERNAME, settings.OUTBRAIN_INTERNAL_PASSWORD)
    headers = {"Authorization": "Basic {}".format(credentials.decode("utf-8"))}
    r = requests.request(method="GET", url=settings.AMELIA_BASE_URL + URL_LOGIN, headers=headers, timeout=TIMEOUT)

    if r.status_code != 200:
        raise OutbrainInternalAPIException("Unable to obtain API token. Response: {}".format(r.text))

    api_token = json.loads(r.text)["OB-TOKEN-V1"]

    return api_token


def _base64_encode_credentials(username, password):
    return base64.b64encode((username + ":" + password).encode("utf-8"))
