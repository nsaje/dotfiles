import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from utils import request_signer
from utils import zlogging

logger = zlogging.getLogger(__name__)

NUM_RETRIES = 3


def get_pixel_traffic(timeout=300):
    request_url = settings.R1_PIXEL_TRAFFIC_URL

    logger.info("Querying pixel traffic")
    job_id = _call_api_retry(request_url, method="GET")

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        logger.info("Polling pixel traffic results")
        result = _call_api_retry(settings.R1_PIXEL_TRAFFIC_RESULT_URL.format(job_id=job_id), method="GET")
        if result is None:
            time.sleep(2)
            continue

        return result

    raise Exception("Pixel traffic timeout")


def update_pixel(conversion_pixel):
    try:
        data = json.dumps({"redirecturl": conversion_pixel.redirect_url})
        return _call_api_retry(
            settings.R1_PIXEL_URL.format(account_id=conversion_pixel.account_id, slug=conversion_pixel.slug),
            data,
            method="PUT",
        )
    except Exception:
        logger.exception("Exception in update_pixel")
        raise


def _call_api_retry(url, data=None, method="POST"):
    last_error = None
    for _ in range(NUM_RETRIES):
        try:
            return _call_api(url, data, method)
        except Exception as error:
            last_error = error

    raise last_error


def _call_api(url, data, method="POST"):
    if settings.R1_DEMO_MODE:
        return {}
    request = urllib.request.Request(url, data.encode("utf-8") if data else None)
    request.get_method = lambda: method
    response = request_signer.urllib_secure_open(request, settings.R1_API_SIGN_KEY)

    status_code = response.getcode()
    if status_code != 200:
        raise Exception("Invalid response status code. status code: {}".format(status_code))

    ret = json.loads(response.read())
    if ret["status"] != "ok":
        raise Exception("Request not successful. status: {}".format(ret["status"]))

    return ret.get("data")
