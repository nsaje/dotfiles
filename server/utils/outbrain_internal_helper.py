import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

NUM_RETRIES = 3
URL_IDS_TO_INTERNAL = "ids/{external_ids}/toInternal"


class OutbrainInternalAPIException(Exception):
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
    headers["OB-TOKEN-V1"] = settings.OB_TOKEN_V1
    headers["Host"] = "amelia"
    r = requests.request(method=method, url=url, headers=headers, **kwargs)
    if r.status_code != 200:
        raise OutbrainInternalAPIException("Invalid response status code. response: {}".format(r.content))

    try:
        ret = r.json()
    except Exception:
        raise OutbrainInternalAPIException("JSON deserialization not successful: {}".format(r.content))

    return ret
